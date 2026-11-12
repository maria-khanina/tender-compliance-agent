"""Review workload a verdict model saves while it still catches the problems.

A case needs review when its gold verdict is anything other than compliant.
The model ranks cases by its needs-review score; a reviewer reads every case
at or above a threshold. The threshold is the highest one at which the share
of needs-review cases that are read (recall) reaches MINIMUM_PROBLEM_RECALL,
and the saved work is the share of all cases left unread. ROC AUC measures
the ranking without any threshold.
"""
import math

import numpy
from numpy.typing import NDArray

from sft.review_workload_settings import (
    MINIMUM_PROBLEM_RECALL,
    RECALL_ROUNDING_DIGITS,
)


def required_catches(problems: int) -> int:
    """Return how many needs-review cases must be read to reach the recall."""
    return math.ceil(round(MINIMUM_PROBLEM_RECALL * problems, RECALL_ROUNDING_DIGITS))


def read_count(labels: NDArray[numpy.bool_], scores: NDArray[numpy.float64]) -> int:
    """Return how many cases a reviewer reads at the highest sufficient threshold."""
    order = numpy.argsort(-scores, kind="stable")
    caught = numpy.cumsum(labels[order])
    first = int(numpy.argmax(caught >= required_catches(int(labels.sum()))))
    threshold = scores[order][first]
    return int(numpy.sum(scores >= threshold))


def saved_work(labels: NDArray[numpy.bool_], scores: NDArray[numpy.float64]) -> float:
    """Return the share of cases left unread at the minimum problem recall."""
    if not labels.any():
        return math.nan
    return 1.0 - read_count(labels, scores) / len(labels)


def ranking_auc(labels: NDArray[numpy.bool_], scores: NDArray[numpy.float64]) -> float:
    """Return ROC AUC: the chance that a problem outranks a compliant case."""
    problems, compliant = scores[labels], scores[~labels]
    if len(problems) == 0 or len(compliant) == 0:
        return math.nan
    higher = numpy.mean(problems[:, None] > compliant[None, :])
    tied = numpy.mean(problems[:, None] == compliant[None, :])
    return float(higher + tied / 2.0)
