"""Compare the verdict models over the tender-grouped folds.

Reads the held-out scores of every fold of every model in FOLD_MODELS
(sft/runs/review_scores/folds/<model>/fold_<k>.json), all in the same case
order. For every model it reports the saved review work and the recall it
actually reaches when every fold is read at the threshold chosen on the other
folds, the saved work of the best threshold on all cases (optimistic), and
ROC AUC of the pooled held-out scores. A paired bootstrap resamples the cases
within every fold (the same resample for every model) and gives the
intervals of each model and of the difference of every pair. Writes
sft/runs/review_workload_folds.json.

Usage (from the repository root):
  python -m sft.compare_fold_models
"""
from itertools import combinations
import json
import os
from typing import TypedDict, cast

import numpy
from numpy.typing import NDArray

from sft.compare_equal_epochs import Interval, interval
from sft.compare_review_models import needs_review, review_scores
from sft.fold_settings import (
    FOLD_COUNT,
    FOLD_MODELS,
    FOLD_REPORT,
    FOLD_SCORES_DIRECTORY,
)
from sft.full_fine_tuning_settings import BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED
from sft.review_workload import cross_fitted_review, ranking_auc, saved_work
from sft.review_workload_settings import MINIMUM_PROBLEM_RECALL
from sft.score_review_models import ScoredCase

METRICS = ("saved_work", "reached_recall", "best_threshold_saved_work", "roc_auc")


class FoldScores(TypedDict):
    """The gold labels, needs-review scores and folds of one model."""

    labels: NDArray[numpy.bool_]
    scores: NDArray[numpy.float64]
    folds: NDArray[numpy.int64]


def read_fold(name: str, fold: int) -> list[ScoredCase] | None:
    """Return the held-out scores of one fold of a model, or None if missing."""
    path = f"{FOLD_SCORES_DIRECTORY}/{name}/fold_{fold}.json"
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as scores_file:
        return cast(list[ScoredCase], json.load(scores_file))


def load_model_scores(name: str) -> FoldScores | None:
    """Return the pooled held-out scores of a model, or None if a fold is missing."""
    cases: list[ScoredCase] = []
    folds: list[int] = []
    for fold in range(FOLD_COUNT):
        fold_cases = read_fold(name, fold)
        if fold_cases is None:
            return None
        cases.extend(fold_cases)
        folds.extend([fold] * len(fold_cases))
    return {
        "labels": needs_review(cases),
        "scores": review_scores(cases),
        "folds": numpy.array(folds, dtype=numpy.int64),
    }


def metric_values(scores: FoldScores, cases: NDArray[numpy.int64]) -> list[float]:
    """Return every metric of a model on the chosen cases."""
    labels, values = scores["labels"][cases], scores["scores"][cases]
    saved, recall = cross_fitted_review(labels, values, scores["folds"][cases])
    return [saved, recall, saved_work(labels, values), ranking_auc(labels, values)]


def resample_within_folds(
    folds: NDArray[numpy.int64],
    generator: numpy.random.Generator,
) -> NDArray[numpy.int64]:
    """Return a resample of the cases that keeps the size of every fold."""
    chosen: list[NDArray[numpy.int64]] = []
    for fold in range(FOLD_COUNT):
        members = numpy.flatnonzero(folds == fold)
        chosen.append(generator.choice(members, len(members)))
    return numpy.concatenate(chosen)


def bootstrap_models(
    models: dict[str, FoldScores],
) -> dict[str, NDArray[numpy.float64]]:
    """Return every metric of every model on the same resamples."""
    folds = next(iter(models.values()))["folds"]
    generator = numpy.random.default_rng(BOOTSTRAP_SEED)
    samples: dict[str, NDArray[numpy.float64]] = {}
    for name in models:
        samples[name] = numpy.empty((BOOTSTRAP_RESAMPLES, len(METRICS)))
    for index in range(BOOTSTRAP_RESAMPLES):
        cases = resample_within_folds(folds, generator)
        for name, scores in models.items():
            samples[name][index] = metric_values(scores, cases)
    return samples


def describe(
    estimates: list[float],
    samples: NDArray[numpy.float64],
) -> dict[str, Interval]:
    """Return every metric with its bootstrap interval."""
    described: dict[str, Interval] = {}
    for column, metric in enumerate(METRICS):
        described[metric] = interval(estimates[column], samples[:, column])
    return described


def compare_pairs(
    estimates: dict[str, list[float]],
    samples: dict[str, NDArray[numpy.float64]],
) -> dict[str, dict[str, Interval]]:
    """Return every metric of the difference of every pair of models."""
    differences: dict[str, dict[str, Interval]] = {}
    for first, second in combinations(estimates, 2):
        difference = numpy.subtract(estimates[second], estimates[first]).tolist()
        differences[f"{second}_minus_{first}"] = describe(
            difference, samples[second] - samples[first]
        )
    return differences


def build_report(models: dict[str, FoldScores]) -> dict[str, object]:
    """Score every model and every pair of models on the same resamples."""
    samples = bootstrap_models(models)
    every_case = numpy.arange(len(next(iter(models.values()))["labels"]))
    estimates: dict[str, list[float]] = {}
    described: dict[str, dict[str, Interval]] = {}
    for name, scores in models.items():
        estimates[name] = metric_values(scores, every_case)
        described[name] = describe(estimates[name], samples[name])
    return {
        "minimum_problem_recall": MINIMUM_PROBLEM_RECALL,
        "cases": len(every_case),
        "models": described,
        "differences": compare_pairs(estimates, samples),
    }


def main() -> None:
    """Compare every model whose folds are all scored and write the report."""
    models: dict[str, FoldScores] = {}
    for name in FOLD_MODELS:
        scores = load_model_scores(name)
        if scores is not None:
            models[name] = scores
    report = build_report(models)
    text = json.dumps(report, indent=2) + "\n"
    with open(FOLD_REPORT, "w", encoding="utf-8") as report_file:
        report_file.write(text)
    print(text)


if __name__ == "__main__":
    main()
