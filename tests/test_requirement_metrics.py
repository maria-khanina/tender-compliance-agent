from evaluation.matching import MatchGroup, SpanRef
from evaluation.requirement_metrics import (
    compute_coverage_flags,
    compute_is_mandatory_accuracy,
    compute_is_text_verifiable_accuracy,
    compute_precision,
    compute_requirement_recall,
)


def _group(
    shape: str,
    true_topic_ids: list[str],
    predicted_node_ids: list[str],
) -> MatchGroup:
    return MatchGroup(
        true_topic_ids=true_topic_ids,
        predicted_node_ids=predicted_node_ids,
        shape=shape,
    )


def _span(node_id: str, start: int, end: int, path: str = "doc.txt") -> SpanRef:
    return SpanRef(
        node_id=node_id, document_path=path, start_char=start, end_char=end
    )


def test_recall_counts_clean_and_split_merge_as_found() -> None:
    groups = [
        _group("clean", ["topic_a"], ["req_1"]),
        _group("over_split", ["topic_b"], ["req_2", "req_3"]),
        _group("over_merge", ["topic_c", "topic_d"], ["req_4"]),
        _group("unmatched_true", ["topic_e"], []),
    ]
    result = compute_requirement_recall(groups)
    assert result.total_topic_count == 5
    assert result.matched_topic_count == 4
    assert result.recall == 4 / 5
    assert result.missed_topic_ids == ["topic_e"]
    assert result.over_split_topic_ids == ["topic_b"]
    assert result.over_merge_topic_ids == ["topic_c", "topic_d"]


def test_precision_counts_only_matched_predicted_requirements() -> None:
    groups = [
        _group("clean", ["topic_a"], ["req_1"]),
        _group("unmatched_predicted", [], ["req_2"]),
        _group("unmatched_predicted", [], ["req_3"]),
    ]
    citation_verified = {
        "req_1": True,
        "req_2": False,
        "req_3": True,
    }
    result = compute_precision(groups, citation_verified)
    assert result.citation_verified_rate == 2 / 3
    assert result.unverified_requirement_ids == ["req_2"]
    assert result.unexplained_requirement_ids == ["req_2", "req_3"]
    assert result.classification_precision == 1 / 3


def test_coverage_flags_catch_incomplete_and_overbroad() -> None:
    groups = [
        _group("clean", ["topic_a"], ["req_1"]),
        _group("clean", ["topic_b"], ["req_2"]),
    ]
    true_spans = [
        _span("topic_a", 0, 100),
        _span("topic_b", 0, 100),
    ]
    predicted_spans = [
        _span("req_1", 0, 200),
        _span("req_2", 0, 100),
    ]
    flags = compute_coverage_flags(groups, true_spans, predicted_spans, 0.9)
    flagged_topics = {flag.true_topic_ids[0] for flag in flags}
    assert flagged_topics == {"topic_a"}


def test_coverage_flags_ignore_unrelated_citations_of_the_same_node() -> None:
    # A predicted requirement with two citations from dedup: one overlaps
    # the true topic exactly, the other is an unrelated restatement
    # elsewhere. The unrelated citation must not be treated as padding.
    groups = [_group("clean", ["topic_a"], ["req_1"])]
    true_spans = [_span("topic_a", 0, 100)]
    predicted_spans = [
        _span("req_1", 0, 100),
        _span("req_1", 5000, 5100),
    ]
    flags = compute_coverage_flags(groups, true_spans, predicted_spans, 0.9)
    assert flags == []


def test_coverage_flags_exclude_non_clean_shapes() -> None:
    # Over-split fragments are inherently partial by construction --
    # they must not show up as "incomplete" coverage flags; that's
    # already visible in the recall breakdown's Over-split section.
    groups = [_group("over_split", ["topic_a"], ["req_1", "req_2"])]
    true_spans = [_span("topic_a", 0, 100)]
    predicted_spans = [_span("req_1", 0, 10)]
    flags = compute_coverage_flags(groups, true_spans, predicted_spans, 0.9)
    assert flags == []


def test_is_mandatory_accuracy_scores_clean_and_one_to_many() -> None:
    groups = [
        _group("clean", ["topic_a"], ["req_1"]),
        _group("clean", ["topic_b"], ["req_2"]),
        _group("over_merge", ["topic_c", "topic_d"], ["req_3"]),
        _group("tangled", ["topic_e"], ["req_4", "req_5"]),
    ]
    true_is_mandatory = {
        "topic_a": True,
        "topic_b": False,
        "topic_c": True,
        "topic_d": True,
        "topic_e": True,
    }
    predicted_is_mandatory = {
        "req_1": True,
        "req_2": True,
        "req_3": True,
        "req_4": True,
        "req_5": False,
    }
    result = compute_is_mandatory_accuracy(
        groups, true_is_mandatory, predicted_is_mandatory
    )
    # tangled group is excluded (no single "one" to compare against);
    # the over_merge group is scored and matches (both true topics agree
    # with the one predicted value).
    assert result.scored_topic_count == 3
    assert [g.true_topic_ids for g in result.mismatched_groups] == [
        ["topic_b"]
    ]
    assert result.accuracy == 2 / 3


def test_is_mandatory_accuracy_over_merge_needs_all_true_topics_to_agree() -> None:
    groups = [_group("over_merge", ["topic_a", "topic_b"], ["req_1"])]
    true_is_mandatory = {"topic_a": True, "topic_b": False}
    predicted_is_mandatory = {"req_1": True}
    result = compute_is_mandatory_accuracy(
        groups, true_is_mandatory, predicted_is_mandatory
    )
    assert result.scored_topic_count == 1
    assert [g.true_topic_ids for g in result.mismatched_groups] == [
        ["topic_a", "topic_b"]
    ]
    assert result.accuracy == 0.0


def test_is_text_verifiable_accuracy_over_split_needs_all_predicted_to_agree() -> None:
    groups = [_group("over_split", ["topic_a"], ["req_1", "req_2"])]
    true_is_text_verifiable = {"topic_a": True}
    predicted_is_text_verifiable = {"req_1": True, "req_2": False}
    result = compute_is_text_verifiable_accuracy(
        groups, true_is_text_verifiable, predicted_is_text_verifiable
    )
    assert result.scored_topic_count == 1
    assert [g.true_topic_ids for g in result.mismatched_groups] == [
        ["topic_a"]
    ]
    assert result.accuracy == 0.0
