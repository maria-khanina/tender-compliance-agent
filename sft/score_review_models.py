"""Score every validation case with one verdict model.

For each validation case the probability of every verdict is read from the
tokens of the model (sft/verdict_probabilities.py) and written with the gold
verdict to sft/runs/review_scores/<model>.json. The models are named in
REVIEW_MODELS: Qwen3-0.6B without training and with the QLoRA adapter after
4 epochs, and Qwen3-4B without training, after QLoRA SFT (the merged
checkpoint) and after QLoRA SFT followed by DPO.

Usage (from the repository root, on the GPU):
  python -m sft.score_review_models --model qlora_0.6b
"""
import argparse
import json
import os
from typing import TypedDict

from peft import PeftModel
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, PreTrainedTokenizerBase

from sft.compare_models import bnb_config
from sft.review_workload_settings import REVIEW_MODELS, REVIEW_SCORES_DIRECTORY
from sft.training_schemas import ModelSource
from sft.train_verdict_lora import build_datasets
from sft.verdict_probabilities import VerdictModel, verdict_probabilities


class ScoredCase(TypedDict):
    """The gold verdict of a validation case and the verdict probabilities."""

    case: str
    topic_id: str
    true_verdict: str
    verdict_probabilities: dict[str, float]


def parse_arguments() -> argparse.Namespace:
    """Read which model to score."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=REVIEW_MODELS, required=True)
    return parser.parse_args()


def load_model(source: ModelSource) -> VerdictModel:
    """Load the weights of a model, quantized to 4 bits when it was trained so."""
    model = AutoModelForCausalLM.from_pretrained(
        source["weights"],
        quantization_config=bnb_config() if source["quantized"] else None,
        dtype=torch.bfloat16,
        device_map="auto",
    )
    if source["adapter"] is None:
        return model
    return PeftModel.from_pretrained(model, source["adapter"])


def score_cases(
    model: VerdictModel,
    tokenizer: PreTrainedTokenizerBase,
) -> list[ScoredCase]:
    """Return the verdict probabilities of every validation case."""
    _, validation_rows = build_datasets()
    model.eval()
    scored: list[ScoredCase] = []
    for row in validation_rows:
        scored.append({
            "case": row["case"],
            "topic_id": row["topic_id"],
            "true_verdict": row["true_verdict"],
            "verdict_probabilities": verdict_probabilities(model, tokenizer, row),
        })
    return scored


def main() -> None:
    """Score the validation cases with the named model and save the scores."""
    arguments = parse_arguments()
    source = REVIEW_MODELS[arguments.model]
    tokenizer = AutoTokenizer.from_pretrained(source["tokenizer"])
    scored = score_cases(load_model(source), tokenizer)
    os.makedirs(REVIEW_SCORES_DIRECTORY, exist_ok=True)
    path = f"{REVIEW_SCORES_DIRECTORY}/{arguments.model}.json"
    with open(path, "w", encoding="utf-8") as scores_file:
        json.dump(scored, scores_file, indent=2)
    print(f"scored {len(scored)} cases into {path}")


if __name__ == "__main__":
    main()
