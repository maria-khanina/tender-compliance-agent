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
        pairs.add((edge.expected_topic_id, edge.actual_node_id))
    return pairs


def test_clean_one_to_one_match() -> None:
    expected = [_span("topic_a", 0, 10)]
    actual = [_span("req_1", 2, 8)]
    edges = find_overlapping_pairs(expected, actual, 0.5)
    groups = build_match_groups(["topic_a"], ["req_1"], edges)
    assert len(groups) == 1
    assert groups[0].shape == "clean"
    assert groups[0].expected_topic_ids == ["topic_a"]
    assert groups[0].actual_node_ids == ["req_1"]


def test_unmatched_expected_is_recall_miss() -> None:
    expected = [_span("topic_a", 0, 10)]
    actual = [_span("req_1", 100, 110)]
    edges = find_overlapping_pairs(expected, actual, 0.5)
    groups = build_match_groups(["topic_a"], ["req_1"], edges)
    shapes = {group.shape for group in groups}
    assert "unmatched_expected" in shapes
    assert "unmatched_actual" in shapes


def test_over_merge_two_expected_one_actual() -> None:
    expected = [_span("topic_a", 0, 10), _span("topic_b", 20, 30)]
    actual = [_span("req_1", 0, 30)]
    edges = find_overlapping_pairs(expected, actual, 0.9)
    groups = build_match_groups(["topic_a", "topic_b"], ["req_1"], edges)
    assert len(groups) == 1
    assert groups[0].shape == "over_merge"
    assert set(groups[0].expected_topic_ids) == {"topic_a", "topic_b"}


def test_over_split_one_expected_two_actual() -> None:
    expected = [_span("topic_a", 0, 20)]
    actual = [_span("req_1", 0, 8), _span("req_2", 10, 18)]
    edges = find_overlapping_pairs(expected, actual, 0.9)
    groups = build_match_groups(["topic_a"], ["req_1", "req_2"], edges)
    assert len(groups) == 1
    assert groups[0].shape == "over_split"
    assert set(groups[0].actual_node_ids) == {"req_1", "req_2"}


def test_low_overlap_below_threshold_is_not_a_match() -> None:
    expected = [_span("topic_a", 0, 100)]
    actual = [_span("req_1", 98, 108)]
    edges = find_overlapping_pairs(expected, actual, 0.5)
    assert edges == []


def test_different_documents_never_match() -> None:
    expected_span = SpanRef(
        node_id="topic_a",
        document_path="tender.txt",
        start_char=0,
        end_char=10,
    )
    actual_span = SpanRef(
        node_id="req_1",
        document_path="application.txt",
        start_char=0,
        end_char=10,
    )
    edges = find_overlapping_pairs([expected_span], [actual_span], 0.1)
    assert edges == []


def test_actual_requirement_with_multiple_citations_matches_once() -> None:
    expected = [_span("topic_a", 0, 10)]
    actual = [_span("req_1", 2, 8), _span("req_1", 3, 9)]
    edges = find_overlapping_pairs(expected, actual, 0.5)
    assert _pairs(edges) == {("topic_a", "req_1")}
