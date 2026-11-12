"""Compare the small verdict models by the review work they save.

Reads the verdict probabilities of every scored model
(sft/runs/review_scores/<model>.json), computes the share of cases a reviewer
does not have to read while MINIMUM_PROBLEM_RECALL of the needs-review cases
are still read, and ROC AUC of the needs-review score. A paired bootstrap
(the same resampled cases for every model, the threshold chosen again in
every resample) gives the confidence intervals of each model and of the
difference of every pair. The threshold is chosen on the same cases it is
applied to, so the saved work is the best a threshold could achieve on them.
Writes sft/runs/review_workload_comparison.json.

Usage (from the repository root):
  python -m sft.compare_review_models
"""
from itertools import combinations
import json
import os
from typing import TypedDict, cast

import numpy
from numpy.typing import NDArray

from sft.compare_equal_epochs import Interval, interval
from sft.full_fine_tuning_settings import BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED
from sft.review_workload import ranking_auc, saved_work
from sft.review_workload_settings import (
    COMPLIANT_VERDICT,
    MINIMUM_PROBLEM_RECALL,
    REVIEW_MODELS,
    REVIEW_REPORT,
    REVIEW_SCORES_DIRECTORY,
)
from sft.score_review_models import ScoredCase


class ModelScore(TypedDict):
    """The saved review work and ROC AUC of one model."""

    saved_work: Interval
    roc_auc: Interval


def load_scores() -> dict[str, list[ScoredCase]]:
    """Return the scored cases of every model that has been scored."""
    scores: dict[str, list[ScoredCase]] = {}
    for name in REVIEW_MODELS:
        path = f"{REVIEW_SCORES_DIRECTORY}/{name}.json"
        if os.path.exists(path):
            with open(path, encoding="utf-8") as scores_file:
                scores[name] = cast(list[ScoredCase], json.load(scores_file))
    return scores


def needs_review(cases: list[ScoredCase]) -> NDArray[numpy.bool_]:
    """Return whether the gold verdict of every case needs review."""
    return numpy.array([case["true_verdict"] != COMPLIANT_VERDICT for case in cases])


def review_scores(cases: list[ScoredCase]) -> NDArray[numpy.float64]:
    """Return one minus the probability of compliant for every case."""
    compliant: list[float] = []
    for case in cases:
        compliant.append(case["verdict_probabilities"][COMPLIANT_VERDICT])
    return 1.0 - numpy.array(compliant, dtype=numpy.float64)


def resampled_metrics(
    labels: NDArray[numpy.bool_],
    scores: NDArray[numpy.float64],
    resamples: NDArray[numpy.int64],
) -> NDArray[numpy.float64]:
    """Return the saved work and ROC AUC on every resample of the cases."""
    metrics = numpy.empty((len(resamples), 2))
    for index, cases in enumerate(resamples):
        metrics[index] = (
            saved_work(labels[cases], scores[cases]),
            ranking_auc(labels[cases], scores[cases]),
        )
    return metrics


def score_model(
    labels: NDArray[numpy.bool_],
    scores: NDArray[numpy.float64],
    samples: NDArray[numpy.float64],
) -> ModelScore:
    """Return the saved work and ROC AUC of a model with their intervals."""
    return {
        "saved_work": interval(saved_work(labels, scores), samples[:, 0]),
        "roc_auc": interval(ranking_auc(labels, scores), samples[:, 1]),
    }


def compare_pairs(
    estimates: dict[str, ModelScore],
    samples: dict[str, NDArray[numpy.float64]],
) -> dict[str, ModelScore]:
    """Return the difference of every pair of models with its interval."""
    differences: dict[str, ModelScore] = {}
    for first, second in combinations(estimates, 2):
        difference = samples[second] - samples[first]
        differences[f"{second}_minus_{first}"] = {
            "saved_work": interval(
                estimates[second]["saved_work"]["estimate"]
                - estimates[first]["saved_work"]["estimate"],
                difference[:, 0],
            ),
            "roc_auc": interval(
                estimates[second]["roc_auc"]["estimate"]
                - estimates[first]["roc_auc"]["estimate"],
                difference[:, 1],
            ),
        }
    return differences


def build_report(scores: dict[str, list[ScoredCase]]) -> dict[str, object]:
    """Score every model and every pair on the same bootstrap resamples."""
    labels = needs_review(next(iter(scores.values())))
    generator = numpy.random.default_rng(BOOTSTRAP_SEED)
    resamples = generator.integers(0, len(labels), (BOOTSTRAP_RESAMPLES, len(labels)))
    estimates: dict[str, ModelScore] = {}
    samples: dict[str, NDArray[numpy.float64]] = {}
    for name, cases in scores.items():
        samples[name] = resampled_metrics(labels, review_scores(cases), resamples)
        estimates[name] = score_model(labels, review_scores(cases), samples[name])
    return {
        "minimum_problem_recall": MINIMUM_PROBLEM_RECALL,
        "cases": len(labels),
        "needs_review_cases": int(labels.sum()),
        "models": estimates,
        "differences": compare_pairs(estimates, samples),
    }


def main() -> None:
    """Compare the scored models and write the report."""
    report = build_report(load_scores())
    text = json.dumps(report, indent=2) + "\n"
    with open(REVIEW_REPORT, "w", encoding="utf-8") as report_file:
        report_file.write(text)
    print(text)


if __name__ == "__main__":
    main()
