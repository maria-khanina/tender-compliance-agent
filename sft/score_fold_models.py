"""Score the held-out cases of every fold with a model that needs no training.

A model without fine-tuning sees no fold during training, so one loaded model
scores every fold; the scores are written per fold, in the same case order as
the trained fold models, to sft/runs/review_scores/folds/<model>/fold_<k>.json.

Usage (from the repository root, on the GPU):
  python -m sft.score_fold_models --model base_0.6b
"""
import argparse

from transformers import AutoTokenizer

from sft.fold_settings import FOLD_COUNT, FOLD_SCORES_DIRECTORY
from sft.folds import split_fold
from sft.review_workload_settings import REVIEW_MODELS
from sft.score_review_models import load_model, save_scores, score_rows


def parse_arguments() -> argparse.Namespace:
    """Read which untrained model to score."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=REVIEW_MODELS, required=True)
    return parser.parse_args()


def main() -> None:
    """Score the held-out cases of every fold and save them per fold."""
    arguments = parse_arguments()
    source = REVIEW_MODELS[arguments.model]
    tokenizer = AutoTokenizer.from_pretrained(source["tokenizer"])
    model = load_model(source)
    for fold in range(FOLD_COUNT):
        _, held_out_rows = split_fold(fold)
        scored = score_rows(model, tokenizer, held_out_rows)
        directory = f"{FOLD_SCORES_DIRECTORY}/{arguments.model}"
        save_scores(scored, f"{directory}/fold_{fold}.json")


if __name__ == "__main__":
    main()
