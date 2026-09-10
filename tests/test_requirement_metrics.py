from evaluation.matching import MatchGroup, OverlapEdge
from evaluation.requirement_metrics import (
    compute_coverage_flags,
    compute_is_mandatory_accuracy,
    compute_precision,
    compute_requirement_recall,
)


def _group(
    shape: str,
    expected_topic_ids: list[str],
    actual_node_ids: list[str],
) -> MatchGroup:
    return MatchGroup(
        expected_topic_ids=expected_topic_ids,
        actual_node_ids=actual_node_ids,
        shape=shape,
    )


def test_recall_counts_clean_and_split_merge_as_found() -> None:
    groups = [
        _group("clean", ["topic_a"], ["req_1"]),
        _group("over_split", ["topic_b"], ["req_2", "req_3"]),
        _group("over_merge", ["topic_c", "topic_d"], ["req_4"]),
        _group("unmatched_expected", ["topic_e"], []),
    ]
    result = compute_requirement_recall(groups)
    assert result.total_topic_count == 5
    assert result.matched_topic_count == 4
    assert result.recall == 4 / 5
    assert result.missed_topic_ids == ["topic_e"]
    assert result.over_split_topic_ids == ["topic_b"]
    assert result.over_merge_topic_ids == ["topic_c", "topic_d"]


def test_precision_splits_hallucination_from_classification_error() -> None:
    groups = [
        _group("clean", ["topic_a"], ["req_1"]),
        _group("unmatched_actual", [], ["req_2"]),
        _group("unmatched_actual", [], ["req_3"]),
    ]
    citation_verified = {
        "req_1": True,
        "req_2": False,
        "req_3": True,
    }
    result = compute_precision(groups, citation_verified, {"req_3"})
    assert result.citation_verified_rate == 2 / 3
    assert result.unverified_requirement_ids == ["req_2"]
    assert result.unexplained_requirement_ids == ["req_2"]
    assert result.classification_precision == 2 / 3


def test_coverage_flags_catch_incomplete_and_overbroad() -> None:
    groups = [
        _group("clean", ["topic_a"], ["req_1"]),
        _group("clean", ["topic_b"], ["req_2"]),
    ]
    edges = [
        OverlapEdge(
            expected_topic_id="topic_a",
            actual_node_id="req_1",
            overlap_length=10,
        ),
        OverlapEdge(
            expected_topic_id="topic_b",
            actual_node_id="req_2",
            overlap_length=100,
        ),
    ]
    expected_lengths = {"topic_a": 100, "topic_b": 100}
    actual_lengths = {"req_1": 100, "req_2": 100}
    flags = compute_coverage_flags(
        groups, edges, expected_lengths, actual_lengths, 0.9
    )
    flagged_topics = {flag.expected_topic_ids[0] for flag in flags}
    assert flagged_topics == {"topic_a"}


def test_is_mandatory_accuracy_only_scores_clean_matches() -> None:
    groups = [
        _group("clean", ["topic_a"], ["req_1"]),
        _group("clean", ["topic_b"], ["req_2"]),
        _group("over_merge", ["topic_c", "topic_d"], ["req_3"]),
    ]
    expected_is_mandatory = {
        "topic_a": True,
        "topic_b": False,
        "topic_c": True,
        "topic_d": True,
    }
    actual_is_mandatory = {
        "req_1": True,
        "req_2": True,
        "req_3": True,
    }
    result = compute_is_mandatory_accuracy(
        groups, expected_is_mandatory, actual_is_mandatory
    )
    assert result.scored_topic_count == 2
    assert result.mismatched_topic_ids == ["topic_b"]
    assert result.accuracy == 1 / 2
