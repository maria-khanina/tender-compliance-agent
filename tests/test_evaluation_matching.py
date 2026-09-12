from evaluation.matching import (
    OverlapEdge,
    SpanRef,
    build_match_groups,
    find_overlapping_pairs,
)


DOCUMENT_PATH = "tender.txt"


def _span(node_id: str, start_char: int, end_char: int) -> SpanRef:
    return SpanRef(
        node_id=node_id,
        document_path=DOCUMENT_PATH,
        start_char=start_char,
        end_char=end_char,
    )


def _pairs(edges: list[OverlapEdge]) -> set[tuple[str, str]]:
    pairs = set()
    for edge in edges:
        pairs.add((edge.true_topic_id, edge.predicted_node_id))
    return pairs


def test_clean_one_to_one_match() -> None:
    true_spans = [_span("topic_a", 0, 10)]
    predicted_spans = [_span("req_1", 2, 8)]
    edges = find_overlapping_pairs(true_spans, predicted_spans, 0.5)
    groups = build_match_groups(["topic_a"], ["req_1"], edges)
    assert len(groups) == 1
    assert groups[0].shape == "clean"
    assert groups[0].true_topic_ids == ["topic_a"]
    assert groups[0].predicted_node_ids == ["req_1"]


def test_unmatched_true_is_recall_miss() -> None:
    true_spans = [_span("topic_a", 0, 10)]
    predicted_spans = [_span("req_1", 100, 110)]
    edges = find_overlapping_pairs(true_spans, predicted_spans, 0.5)
    groups = build_match_groups(["topic_a"], ["req_1"], edges)
    shapes = {group.shape for group in groups}
    assert "unmatched_true" in shapes
    assert "unmatched_predicted" in shapes


def test_over_merge_two_true_one_predicted() -> None:
    true_spans = [_span("topic_a", 0, 10), _span("topic_b", 20, 30)]
    predicted_spans = [_span("req_1", 0, 30)]
    edges = find_overlapping_pairs(true_spans, predicted_spans, 0.9)
    groups = build_match_groups(["topic_a", "topic_b"], ["req_1"], edges)
    assert len(groups) == 1
    assert groups[0].shape == "over_merge"
    assert set(groups[0].true_topic_ids) == {"topic_a", "topic_b"}


def test_over_split_one_true_two_predicted() -> None:
    true_spans = [_span("topic_a", 0, 20)]
    predicted_spans = [_span("req_1", 0, 8), _span("req_2", 10, 18)]
    edges = find_overlapping_pairs(true_spans, predicted_spans, 0.9)
    groups = build_match_groups(["topic_a"], ["req_1", "req_2"], edges)
    assert len(groups) == 1
    assert groups[0].shape == "over_split"
    assert set(groups[0].predicted_node_ids) == {"req_1", "req_2"}


def test_low_overlap_below_threshold_is_not_a_match() -> None:
    true_spans = [_span("topic_a", 0, 100)]
    predicted_spans = [_span("req_1", 98, 108)]
    edges = find_overlapping_pairs(true_spans, predicted_spans, 0.5)
    assert edges == []


def test_different_documents_never_match() -> None:
    true_span = SpanRef(
        node_id="topic_a",
        document_path="tender.txt",
        start_char=0,
        end_char=10,
    )
    predicted_span = SpanRef(
        node_id="req_1",
        document_path="application.txt",
        start_char=0,
        end_char=10,
    )
    edges = find_overlapping_pairs([true_span], [predicted_span], 0.1)
    assert edges == []


def test_predicted_requirement_with_multiple_citations_matches_once() -> None:
    true_spans = [_span("topic_a", 0, 10)]
    predicted_spans = [_span("req_1", 2, 8), _span("req_1", 3, 9)]
    edges = find_overlapping_pairs(true_spans, predicted_spans, 0.5)
    assert _pairs(edges) == {("topic_a", "req_1")}
