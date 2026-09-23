"""Compare baseline vs SFT vs DPO verdict models on the validation split."""
import argparse
import datetime
import json
import os
import pathlib
import sys
from collections.abc import Callable
from typing import TypedDict, cast

import torch
from peft import PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    PreTrainedModel,
    PreTrainedTokenizerBase,
)

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from sft.mine_dpo_pairs_local import extract_tool_call_json  # noqa: E402
from sft.schemas import (  # noqa: E402
    ClassMetrics,
    ScoreResult,
    TrainingRow,
    VerdictCompletion,
    VerdictLabel,
)
from sft.train_verdict_lora import (  # noqa: E402
    BASE_MODEL,
    TOOL_SCHEMA,
    VERDICT_LABELS,
    load_jsonl,
)
from sft.training_config import (  # noqa: E402
    DEFAULT_DPO_ADAPTER_DIR,
    EVAL_MAX_NEW_TOKENS,
    MERGED_MODEL_DIR,
    VAL_DATA_PATH,
)


class ClassCounts(TypedDict):
    true_positives: int
    false_positives: int
    false_negatives: int


def bnb_config() -> BitsAndBytesConfig:
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )


def load_baseline():
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config(),
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )
    return model, tokenizer


def load_sft():
    tokenizer = AutoTokenizer.from_pretrained(MERGED_MODEL_DIR)
    model = AutoModelForCausalLM.from_pretrained(
        MERGED_MODEL_DIR,
        quantization_config=bnb_config(),
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )
    return model, tokenizer


def load_dpo(adapter_dir: str):
    model, tokenizer = load_sft()
    model = PeftModel.from_pretrained(model, adapter_dir)
    return model, tokenizer


@torch.no_grad()
def generate_predictions(
    model: PreTrainedModel | PeftModel,
    tokenizer: PreTrainedTokenizerBase,
    rows: list[TrainingRow],
) -> list[VerdictCompletion | None]:
    model.eval()
    predictions: list[VerdictCompletion | None] = []
    for row in rows:
        input_text = cast(
            str,
            tokenizer.apply_chat_template(  # type: ignore[reportArgumentType]
                [{"role": "user", "content": row["prompt"]}],
                tools=[TOOL_SCHEMA],
                add_generation_prompt=True,
                tokenize=False,
                enable_thinking=False,
            ),
        )
        inputs = tokenizer(input_text, return_tensors="pt").to(
            cast(torch.device, model.device)
        )
        output_ids = model.generate(  # type: ignore[reportAttributeAccessIssue]
            **inputs,
            max_new_tokens=EVAL_MAX_NEW_TOKENS,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
        generated = cast(
            str,
            tokenizer.decode(
                output_ids[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True,
            ),
        )
        predictions.append(extract_tool_call_json(generated))
    return predictions


def empty_class_counts() -> dict[VerdictLabel, ClassCounts]:
    return {
        label: {"true_positives": 0, "false_positives": 0, "false_negatives": 0}
        for label in VERDICT_LABELS
    }


def update_class_counts(
    per_class: dict[VerdictLabel, ClassCounts],
    true_label: VerdictLabel,
    predicted_label: VerdictLabel,
) -> bool:
    if predicted_label == true_label:
        per_class[true_label]["true_positives"] += 1
        return True
    per_class[true_label]["false_negatives"] += 1
    if predicted_label in per_class:
        per_class[predicted_label]["false_positives"] += 1
    return False


def evidence_recall_for_row(
    row: TrainingRow, prediction: VerdictCompletion
) -> float | None:
    gold_chunks = {q["chunk_index"] for q in row["completion"]["evidence_quotes"]}
    if not gold_chunks:
        return None
    predicted_chunks = {q["chunk_index"] for q in prediction["evidence_quotes"]}
    return len(gold_chunks & predicted_chunks) / len(gold_chunks)


def class_metrics_from_counts(counts: ClassCounts) -> ClassMetrics:
    true_positives = counts["true_positives"]
    false_positives = counts["false_positives"]
    false_negatives = counts["false_negatives"]
    predicted_positive = true_positives + false_positives
    actual_positive = true_positives + false_negatives
    precision = true_positives / predicted_positive if predicted_positive else 0.0
    recall = true_positives / actual_positive if actual_positive else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) else 0.0
    )
    return {
        "precision": precision, "recall": recall, "f1": f1, "support": actual_positive,
    }


def score(
    rows: list[TrainingRow], predictions: list[VerdictCompletion | None]
) -> ScoreResult:
    per_class = empty_class_counts()
    correct = 0
    failed = 0
    evidence_recalls: list[float] = []
    for row, prediction in zip(rows, predictions):
        true_label = row["completion"]["verdict"]
        if prediction is None:
            failed += 1
            per_class[true_label]["false_negatives"] += 1
            continue
        if update_class_counts(per_class, true_label, prediction["verdict"]):
            correct += 1
        recall = evidence_recall_for_row(row, prediction)
        if recall is not None:
            evidence_recalls.append(recall)

    total_rows = len(rows)
    per_class_metrics: dict[VerdictLabel, ClassMetrics] = {
        label: class_metrics_from_counts(counts) for label, counts in per_class.items()
    }
    f1_scores = [metrics["f1"] for metrics in per_class_metrics.values()]
    return {
        "accuracy": correct / total_rows if total_rows else 0.0,
        "macro_f1": sum(f1_scores) / len(f1_scores) if f1_scores else 0.0,
        "per_class": per_class_metrics,
        "evidence_recall": (
            sum(evidence_recalls) / len(evidence_recalls) if evidence_recalls else 0.0
        ),
        "evidence_recall_n": len(evidence_recalls),
        "failed": failed,
        "n": total_rows,
    }


def render_overall_section(
    scores: dict[str, ScoreResult], labels: list[str]
) -> list[str]:
    n = scores[labels[0]]["n"]
    lines = ["## Overall\n"]
    lines.append("| Metric | " + " | ".join(labels) + " |")
    lines.append("|---|" + "|".join(["---"] * len(labels)) + "|")
    lines.append(
        "| Verdict accuracy | "
        + " | ".join(f"{scores[label]['accuracy']:.3f}" for label in labels) + " |"
    )
    lines.append(
        "| Macro F1 | "
        + " | ".join(f"{scores[label]['macro_f1']:.3f}" for label in labels) + " |"
    )
    lines.append(
        "| Evidence recall | "
        + " | ".join(f"{scores[label]['evidence_recall']:.3f}" for label in labels)
        + " |"
    )
    lines.append(
        f"| Failed to parse (of {n}) | "
        + " | ".join(str(scores[label]["failed"]) for label in labels) + " |"
    )
    return lines


def render_per_class_section(
    scores: dict[str, ScoreResult], labels: list[str]
) -> list[str]:
    lines = ["\n## Per-class F1\n"]
    lines.append("| Class | Support | " + " | ".join(labels) + " |")
    lines.append("|---|---|" + "|".join(["---"] * len(labels)) + "|")
    for verdict_label in VERDICT_LABELS:
        support = scores[labels[0]]["per_class"][verdict_label]["support"]
        row_values = " | ".join(
            f"{scores[label]['per_class'][verdict_label]['f1']:.3f}" for label in labels
        )
        lines.append(f"| {verdict_label} | {support} | {row_values} |")
    return lines


def render_table(scores: dict[str, ScoreResult], labels: list[str]) -> str:
    n = scores[labels[0]]["n"]
    lines = ["# Baseline vs SFT vs DPO verdict-model comparison\n"]
    lines.append(f"Validation split (`{VAL_DATA_PATH}`), n={n}.\n")
    lines.extend(render_overall_section(scores, labels))
    lines.extend(render_per_class_section(scores, labels))
    return "\n".join(lines) + "\n"


def default_output_dir() -> str:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"sft/eval_runs/{timestamp}_qwen3-4b-v1_bnb4bit"


def evaluate_config(
    label: str,
    loader: Callable[[], tuple[PreTrainedModel | PeftModel, PreTrainedTokenizerBase]],
    val_rows: list[TrainingRow],
) -> tuple[ScoreResult, list[VerdictCompletion | None]]:
    print(f"\nLoading {label}...")
    model, tokenizer = loader()
    print(f"Generating predictions for {label}...")
    predictions = generate_predictions(model, tokenizer, val_rows)
    result = score(val_rows, predictions)
    print(
        f"{label}: accuracy={result['accuracy']:.3f} "
        f"macro_f1={result['macro_f1']:.3f} failed={result['failed']}"
    )
    del model, tokenizer
    torch.cuda.empty_cache()
    return result, predictions


def write_report(
    output_dir: str,
    scores: dict[str, ScoreResult],
    raw_predictions: dict[str, list[VerdictCompletion | None]],
    dpo_adapter_dir: str,
    labels: list[str],
) -> None:
    table = render_table(scores, labels)
    metrics_path = f"{output_dir}/baseline_vs_sft_vs_dpo_metrics.md"
    raw_path = f"{output_dir}/baseline_vs_sft_vs_dpo_raw.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        f.write(table)
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "scores": scores,
                "predictions": raw_predictions,
                "dpo_adapter_dir": dpo_adapter_dir,
            },
            f, indent=2,
        )
    print(f"\nWrote {metrics_path} and {raw_path}")
    print("\n" + table)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dpo-adapter-dir",
        default=DEFAULT_DPO_ADAPTER_DIR,
    )
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    output_dir = args.output_dir or default_output_dir()
    os.makedirs(output_dir, exist_ok=True)

    val_rows = load_jsonl(VAL_DATA_PATH)
    print(f"{len(val_rows)} validation rows loaded")

    configs = [
        ("baseline", load_baseline),
        ("sft", load_sft),
        ("dpo", lambda: load_dpo(args.dpo_adapter_dir)),
    ]
    scores: dict[str, ScoreResult] = {}
    raw_predictions: dict[str, list[VerdictCompletion | None]] = {}
    for label, loader in configs:
        scores[label], raw_predictions[label] = evaluate_config(label, loader, val_rows)

    labels = [label for label, _ in configs]
    write_report(output_dir, scores, raw_predictions, args.dpo_adapter_dir, labels)


if __name__ == "__main__":
    main()
