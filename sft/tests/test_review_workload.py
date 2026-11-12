import numpy

from sft.review_workload import (
    cross_fitted_review,
    ranking_auc,
    required_catches,
    saved_work,
)
from sft.tests.review_fixture_settings import (
    CHANCE_AUC,
    EQUAL_SCORES,
    FOLDED_FOLDS,
    FOLDED_LABELS,
    FOLDED_RECALL,
    FOLDED_SAVED_WORK,
    FOLDED_SCORES,
    LAST_LABELS,
    LAST_SCORES,
    PROBLEM_COUNTS_AND_CATCHES,
    RANKED_COMPLIANT,
    RANKED_PROBLEMS,
    RANKED_READ,
    SEPARATED_SCORES,
    TIED_LABELS,
    TIED_READ,
    TIED_SCORES,
)


def test_required_catches_rounds_up() -> None:
    for problems, catches in PROBLEM_COUNTS_AND_CATCHES:
        assert required_catches(problems) == catches


def test_saved_work_reads_until_the_recall_is_reached() -> None:
    labels = numpy.array([True] * RANKED_PROBLEMS + [False] * RANKED_COMPLIANT)
    scores = numpy.linspace(1.0, 0.0, len(labels))
    assert saved_work(labels, scores) == 1.0 - RANKED_READ / len(labels)


def test_saved_work_reads_every_tied_case() -> None:
    labels = numpy.array(TIED_LABELS)
    expected = 1.0 - TIED_READ / len(labels)
    assert saved_work(labels, numpy.array(TIED_SCORES)) == expected


def test_saved_work_is_zero_when_problems_rank_last() -> None:
    labels = numpy.array(LAST_LABELS)
    assert saved_work(labels, numpy.array(LAST_SCORES)) == 0.0


def test_ranking_auc_counts_ties_as_half() -> None:
    labels = numpy.array(TIED_LABELS)
    assert ranking_auc(labels, numpy.array(SEPARATED_SCORES)) == 1.0
    assert ranking_auc(labels, numpy.array(EQUAL_SCORES)) == CHANCE_AUC


def test_cross_fitted_review_uses_the_threshold_of_the_other_fold() -> None:
    saved, recall = cross_fitted_review(
        numpy.array(FOLDED_LABELS),
        numpy.array(FOLDED_SCORES),
        numpy.array(FOLDED_FOLDS),
    )
    assert saved == FOLDED_SAVED_WORK
    assert recall == FOLDED_RECALL
