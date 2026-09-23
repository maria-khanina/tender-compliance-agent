import json
import os
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import TypedDict, cast

import torch
from datasets import Dataset
from peft import LoraConfig, PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BatchEncoding,
    BitsAndBytesConfig,
    PreTrainedModel,
    PreTrainedTokenizerBase,
    TrainerCallback,
    TrainerControl,
    TrainerState,
    TrainingArguments,
)
from trl import SFTConfig, SFTTrainer  # type: ignore[reportPrivateImportUsage]

from sft.schemas import (
    ChatExample,
    EvalHistoryEntry,
    TaskEvalResult,
    TrainingRow,
    VerdictLabel,
)
from sft.training_config import (
    BASE_MODEL,
    EVAL_MAX_NEW_TOKENS,
    LORA_ALPHA,
    LORA_DROPOUT,
    LORA_RANK,
    LORA_TARGET_MODULES,
    SFT_EARLY_STOP_MIN_DELTA,
    SFT_EARLY_STOP_PATIENCE,
    SFT_EVAL_EVERY_N_STEPS,
    SFT_GRADIENT_ACCUMULATION_STEPS,
    SFT_LEARNING_RATE,
    SFT_LOGGING_STEPS,
    SFT_MAX_SEQ_LEN,
    SFT_NUM_TRAIN_EPOCHS,
    SFT_PER_DEVICE_TRAIN_BATCH_SIZE,
    SFT_RUN_DIR,
    SFT_SAVE_EVERY_N_STEPS,
    SFT_WEIGHT_DECAY,
    TRAIN_DATA_PATH,
    VAL_DATA_PATH,
)

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DIR = f"{SFT_RUN_DIR}/sft_checkpoints"

VERDICT_LABELS: list[VerdictLabel] = [
    "compliant", "non_compliant", "insufficient_information", "contradictory",
]

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "submit_verdict",
        "description": "Submit the compliance verdict for this requirement.",
        "parameters": {
            "type": "object",
            "properties": {
                "verdict": {"type": "string", "enum": VERDICT_LABELS},
                "evidence_quotes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "chunk_index": {"type": "integer"},
                            "quote": {"type": "string"},
                            "role": {
                                "type": "string",
                                "enum": ["supports", "contradicts", "inconclusive"],
                            },
                        },
                        "required": ["chunk_index", "quote", "role"],
                    },
                },
                "reasoning": {"type": "string"},
            },
            "required": ["verdict", "evidence_quotes", "reasoning"],
        },
    },
}


def load_jsonl(path: str) -> list[TrainingRow]:
    rows: list[TrainingRow] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def to_chat_example(row: TrainingRow) -> ChatExample:
    completion = row["completion"]
    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {
            "name": "submit_verdict",
            "arguments": json.dumps(completion, ensure_ascii=False),
        },
    }
    return {
        "messages": [
            {"role": "user", "content": row["prompt"]},
            {"role": "assistant", "content": None, "tool_calls": [tool_call]},
        ],
        "tools": [TOOL_SCHEMA],
        "topic_id": row["topic_id"],
        "case": row["case"],
        "true_verdict": completion["verdict"],
    }


def build_datasets() -> tuple[Dataset, list[ChatExample]]:
    train_rows = [to_chat_example(r) for r in load_jsonl(TRAIN_DATA_PATH)]
    val_rows = [to_chat_example(r) for r in load_jsonl(VAL_DATA_PATH)]
    train_ds = Dataset.from_list(train_rows)  # type: ignore[reportArgumentType]
    return train_ds, val_rows


def load_model_and_tokenizer():
    from sft.peft_utils import wrap_with_lora

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )
    lora_config = LoraConfig(
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGET_MODULES,
        task_type="CAUSAL_LM",
    )
    model = wrap_with_lora(model, lora_config)
    model.print_trainable_parameters()
    return model, tokenizer


class ClassCounts(TypedDict):
    true_positives: int
    false_positives: int
    false_negatives: int


def extract_verdict_label(generated_text: str) -> VerdictLabel | None:
    match = re.search(r'"verdict"\s*:\s*"(\w+)"', generated_text)
    if match and match.group(1) in VERDICT_LABELS:
        return cast(VerdictLabel, match.group(1))
    return None


def predict_verdict_label(
    model: PreTrainedModel | PeftModel,
    tokenizer: PreTrainedTokenizerBase,
    row: ChatExample,
) -> VerdictLabel | None:
    prompt_messages = [row["messages"][0]]
    raw_inputs = tokenizer.apply_chat_template(
        prompt_messages,  # type: ignore[reportArgumentType]
        tools=row["tools"],  # type: ignore[reportArgumentType]
        add_generation_prompt=True,
        tokenize=True,
        return_tensors="pt",
        return_dict=True,
        enable_thinking=False,
    )
    inputs = cast(BatchEncoding, raw_inputs).to(cast(torch.device, model.device))
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
    return extract_verdict_label(generated)


def empty_class_counts() -> dict[VerdictLabel, ClassCounts]:
    return {
        label: {"true_positives": 0, "false_positives": 0, "false_negatives": 0}
        for label in VERDICT_LABELS
    }


def update_class_counts(
    per_class: dict[VerdictLabel, ClassCounts],
    true_label: VerdictLabel,
    predicted_label: VerdictLabel | None,
) -> bool:
    if predicted_label == true_label:
        per_class[true_label]["true_positives"] += 1
        return True
    per_class[true_label]["false_negatives"] += 1
    if predicted_label in per_class:
        per_class[predicted_label]["false_positives"] += 1
    return False


def macro_f1_from_class_counts(per_class: dict[VerdictLabel, ClassCounts]) -> float:
    f1_scores = []
    for counts in per_class.values():
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
        f1_scores.append(f1)
    return sum(f1_scores) / len(f1_scores) if f1_scores else 0.0


@torch.no_grad()
def evaluate_task_accuracy(
    model: PreTrainedModel | PeftModel,
    tokenizer: PreTrainedTokenizerBase,
    val_rows: list[ChatExample],
) -> TaskEvalResult:
    model.eval()
    correct = 0
    per_class = empty_class_counts()
    for row in val_rows:
        predicted_label = predict_verdict_label(model, tokenizer, row)
        if update_class_counts(per_class, row["true_verdict"], predicted_label):
            correct += 1

    accuracy = correct / len(val_rows) if val_rows else 0.0
    macro_f1 = macro_f1_from_class_counts(per_class)
    model.train()
    return {"task_accuracy": accuracy, "macro_f1": macro_f1, "n": len(val_rows)}


@dataclass
class TaskMetricEarlyStopping(TrainerCallback):
    tokenizer: PreTrainedTokenizerBase
    val_rows: list[ChatExample]
    patience: int = 3
    min_delta: float = 0.01
    eval_every_n_steps: int = SFT_EVAL_EVERY_N_STEPS
    save_every_n_steps: int = SFT_SAVE_EVERY_N_STEPS
    history_path: str = f"{SFT_RUN_DIR}/sft_training_history.json"
    loss_log_path: str = f"{SFT_RUN_DIR}/sft_loss_log.jsonl"
    best_metric: float = field(default=-1.0)
    best_step: int = field(default=-1)
    rounds_without_improvement: int = field(default=0)
    history: list[EvalHistoryEntry] = field(default_factory=list)

    def _persist_history(self) -> None:
        os.makedirs(SFT_RUN_DIR, exist_ok=True)
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)

    def on_log(  # type: ignore[reportIncompatibleMethodOverride]
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        logs: dict[str, float] | None = None,
        **kwargs: object,
    ) -> TrainerControl:
        if logs is None:
            return control
        os.makedirs(SFT_RUN_DIR, exist_ok=True)
        with open(self.loss_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"step": state.global_step, **logs}) + "\n")
        return control

    def on_step_end(  # type: ignore[reportIncompatibleMethodOverride]
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        model: PreTrainedModel | PeftModel | None = None,
        **kwargs: object,
    ) -> TrainerControl:
        step = state.global_step
        if step == 0:
            return control
        is_eval_step = step % self.eval_every_n_steps == 0
        is_periodic_save_step = (
            self.save_every_n_steps and step % self.save_every_n_steps == 0
        )
        if is_periodic_save_step:
            control.should_save = True
            print(f"[checkpoint] periodic save at step {step}")
        if not is_eval_step:
            return control
        assert model is not None, "Trainer always passes model to on_step_end"
        eval_result = evaluate_task_accuracy(model, self.tokenizer, self.val_rows)
        result: EvalHistoryEntry = {**eval_result, "step": state.global_step}
        self.history.append(result)
        self._persist_history()
        print(
            f"[task-eval] step={state.global_step} "
            f"accuracy={result['task_accuracy']:.3f} "
            f"macro_f1={result['macro_f1']:.3f} (n={result['n']})"
        )
        metric = result["macro_f1"]
        if metric > self.best_metric + self.min_delta:
            self.best_metric = metric
            self.best_step = step
            self.rounds_without_improvement = 0
            control.should_save = True
            print(f"[task-eval] new best macro_f1={metric:.3f} at step {step}")
        else:
            self.rounds_without_improvement += 1
            print(
                f"[task-eval] no improvement "
                f"({self.rounds_without_improvement}/{self.patience})"
            )
            if self.rounds_without_improvement >= self.patience:
                print(
                    f"[task-eval] stopping: no macro_f1 improvement for "
                    f"{self.patience} rounds. Best step={self.best_step} "
                    f"(macro_f1={self.best_metric:.3f})"
                )
                control.should_training_stop = True
        return control


def main():
    from sft.peft_utils import as_peft_model

    train_ds, val_rows = build_datasets()
    print(f"train examples: {len(train_ds)}, validation examples: {len(val_rows)}")

    model, tokenizer = load_model_and_tokenizer()

    early_stopping = TaskMetricEarlyStopping(
        tokenizer=tokenizer,
        val_rows=val_rows,
        patience=SFT_EARLY_STOP_PATIENCE,
        min_delta=SFT_EARLY_STOP_MIN_DELTA,
        eval_every_n_steps=SFT_EVAL_EVERY_N_STEPS,
    )

    sft_config = SFTConfig(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=SFT_PER_DEVICE_TRAIN_BATCH_SIZE,
        gradient_accumulation_steps=SFT_GRADIENT_ACCUMULATION_STEPS,
        gradient_checkpointing=True,
        learning_rate=SFT_LEARNING_RATE,
        weight_decay=SFT_WEIGHT_DECAY,
        num_train_epochs=SFT_NUM_TRAIN_EPOCHS,
        logging_steps=SFT_LOGGING_STEPS,
        save_strategy="no",
        max_length=SFT_MAX_SEQ_LEN,
        bf16=True,
        report_to=[],
        assistant_only_loss=True,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=train_ds,
        processing_class=tokenizer,
        callbacks=[early_stopping],
    )
    trainer.train()

    final_dir = f"{OUTPUT_DIR}/final"
    as_peft_model(trainer.model).save_pretrained(final_dir)
    tokenizer.save_pretrained(final_dir)
    print(f"Saved LoRA adapter to {final_dir}")
    print(f"Best step: {early_stopping.best_step}, "
          f"best macro_f1: {early_stopping.best_metric:.3f}")


if __name__ == "__main__":
    main()
