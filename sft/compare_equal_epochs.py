"""Compare full fine-tuning and QLoRA trained for the same number of epochs.

Both runs store the predicted verdict of every validation case at every
evaluation. For each run the step with the best validation macro F1 is taken;
a paired bootstrap over the validation cases (the same resampled cases for
both runs) gives a confidence interval of each macro F1 and of their
difference. The best step is chosen on the same validation cases, so both
scores are optimistic in the same way. Writes
sft/runs/equal_epoch_comparison.json.

Usage (from the repository root):
  python -m sft.compare_equal_epochs
"""
import json
from pathlib import Path
from typing import TypedDict, cast

import numpy
from numpy.typing import NDArray

from sft.full_fine_tuning_settings import (
    BOOTSTRAP_RESAMPLES,
    BOOTSTRAP_SEED,
    CONFIDENCE_LEVEL,
    EQUAL_EPOCHS_REPORT,
    FULL_EQUAL_EPOCHS_HISTORY,
    PERCENT,
    QLORA_EQUAL_EPOCHS_HISTORY,
)
from sft.train_verdict_lora import (
    empty_class_counts,
    load_jsonl,
    macro_f1_from_class_counts,
    to_chat_example,
    update_class_counts,
)
from sft.training_config import VAL_DATA_PATH as VALIDATION_DATA_PATH
from sft.training_schemas import EvalHistoryEntry, VerdictLabel


class Interval(TypedDict):
    """A point estimate with its bootstrap confidence interval."""

    estimate: float
    low: float
    high: float


class RunScore(TypedDict):
    """The best validation step of a run and its macro F1."""

    best_step: int
    macro_f1: Interval
    macro_f1_by_step: dict[int, float]


def load_history(path: str) -> list[EvalHistoryEntry]:
    """Return the validation history of a run."""
    return cast(list[EvalHistoryEntry], json.loads(Path(path).read_text()))


def macro_f1(
    gold: list[VerdictLabel],
    predicted: list[str | None],
    cases: NDArray[numpy.int64],
) -> float:
    """Return the macro F1 of the predictions on the chosen cases."""
    per_class = empty_class_counts()
    for case in cases:
        label = cast(VerdictLabel | None, predicted[case])
        update_class_counts(per_class, gold[case], label)
    return macro_f1_from_class_counts(per_class)


def best_entry(history: list[EvalHistoryEntry]) -> EvalHistoryEntry:
    """Return the evaluation with the highest macro F1 (the earliest on ties)."""
    return max(history, key=lambda entry: entry["macro_f1"])


def interval(estimate: float, samples: NDArray[numpy.float64]) -> Interval:
    """Return the estimate with the percentile interval of the samples."""
    tail = (1 - CONFIDENCE_LEVEL) / 2 * PERCENT
    low, high = numpy.percentile(samples, [tail, PERCENT - tail])
    return {"estimate": estimate, "low": float(low), "high": float(high)}


def bootstrap(
    gold: list[VerdictLabel],
    first: list[str | None],
    second: list[str | None],
) -> NDArray[numpy.float64]:
    """Return the macro F1 of both runs on the same resampled cases."""
    generator = numpy.random.default_rng(BOOTSTRAP_SEED)
    count = len(gold)
    samples = numpy.empty((BOOTSTRAP_RESAMPLES, 2))
    for index in range(BOOTSTRAP_RESAMPLES):
        cases = generator.integers(0, count, count)
        samples[index] = (
            macro_f1(gold, first, cases),
            macro_f1(gold, second, cases),
        )
    return samples


def score_run(
    history: list[EvalHistoryEntry],
    samples: NDArray[numpy.float64],
) -> RunScore:
    """Return the best step, its macro F1 with an interval and the curve."""
    best = best_entry(history)
    return {
        "best_step": best["step"],
        "macro_f1": interval(best["macro_f1"], samples),
        "macro_f1_by_step": {entry["step"]: entry["macro_f1"] for entry in history},
    }


def build_report(
    gold: list[VerdictLabel],
    full: list[EvalHistoryEntry],
    qlora: list[EvalHistoryEntry],
) -> dict[str, object]:
    """Score both runs on the same bootstrap resamples and their difference."""
    full_best, qlora_best = best_entry(full), best_entry(qlora)
    samples = bootstrap(
        gold, full_best["predicted_verdicts"], qlora_best["predicted_verdicts"]
    )
    difference = full_best["macro_f1"] - qlora_best["macro_f1"]
    return {
        "full_fine_tuning": score_run(full, samples[:, 0]),
        "qlora": score_run(qlora, samples[:, 1]),
        "difference_full_minus_qlora": interval(
            difference, samples[:, 0] - samples[:, 1]
        ),
        "share_of_resamples_full_better": float(
            numpy.mean(samples[:, 0] > samples[:, 1])
        ),
        "validation_cases": len(gold),
    }


def main() -> None:
    """Score both runs, the difference, and write the report."""
    rows = load_jsonl(VALIDATION_DATA_PATH)
    gold: list[VerdictLabel] = [
        cast(VerdictLabel, to_chat_example(row)["true_verdict"]) for row in rows
    ]
    report = build_report(
        gold,
        load_history(FULL_EQUAL_EPOCHS_HISTORY),
        load_history(QLORA_EQUAL_EPOCHS_HISTORY),
    )
    text = json.dumps(report, indent=2) + "\n"
    Path(EQUAL_EPOCHS_REPORT).write_text(text)
    print(text)


if __name__ == "__main__":
    main()
