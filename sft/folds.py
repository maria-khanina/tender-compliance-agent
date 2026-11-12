"""Tender-grouped folds over every labeled case outside the test tender.

The training and validation sets are pooled (the test tender stays out) and
every tender is put whole into one of FOLD_COUNT folds, so a fold model never
sees the tender it is scored on. Tenders are assigned from the largest to the
fold with the fewest cases so far, which keeps the folds of similar size.
The assignment is written once to sft/folds.json and read by training,
scoring and the comparison.

Usage (from the repository root):
  python -m sft.folds
"""
import json

from sft.fold_settings import FOLDS_PATH, FOLD_COUNT
from sft.train_verdict_lora import load_jsonl, to_chat_example
from sft.training_config import TRAIN_DATA_PATH
from sft.training_config import VAL_DATA_PATH as VALIDATION_DATA_PATH
from sft.training_schemas import ChatExample


def pooled_rows() -> list[ChatExample]:
    """Return the training and validation cases in their file order."""
    rows: list[ChatExample] = []
    for path in (TRAIN_DATA_PATH, VALIDATION_DATA_PATH):
        for row in load_jsonl(path):
            rows.append(to_chat_example(row))
    return rows


def count_tender_cases(rows: list[ChatExample]) -> dict[str, int]:
    """Return the number of cases of every tender."""
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["case"]] = counts.get(row["case"], 0) + 1
    return counts


def assign_folds(counts: dict[str, int]) -> dict[str, int]:
    """Put every tender, largest first, into the fold with the fewest cases."""
    sizes: list[int] = [0] * FOLD_COUNT
    folds: dict[str, int] = {}
    for tender in sorted(counts, key=lambda name: (-counts[name], name)):
        fold = sizes.index(min(sizes))
        folds[tender] = fold
        sizes[fold] += counts[tender]
    return folds


def load_folds() -> dict[str, int]:
    """Return the fold of every tender."""
    with open(FOLDS_PATH, encoding="utf-8") as folds_file:
        return json.load(folds_file)


def split_fold(fold: int) -> tuple[list[ChatExample], list[ChatExample]]:
    """Return the training cases and the held-out cases of one fold."""
    folds = load_folds()
    training: list[ChatExample] = []
    held_out: list[ChatExample] = []
    for row in pooled_rows():
        (held_out if folds[row["case"]] == fold else training).append(row)
    return training, held_out


def main() -> None:
    """Assign the tenders to folds and write the assignment."""
    rows = pooled_rows()
    folds = assign_folds(count_tender_cases(rows))
    with open(FOLDS_PATH, "w", encoding="utf-8") as folds_file:
        json.dump(folds, folds_file, indent=2)
    print(json.dumps(folds, indent=2))


if __name__ == "__main__":
    main()
