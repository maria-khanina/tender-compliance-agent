import bisect
from collections import defaultdict

from pydantic import BaseModel


class SpanRef(BaseModel):
    node_id: str
    document_path: str
    start_char: int
    end_char: int


class MatchGroup(BaseModel):
    expected_topic_ids: list[str]
    actual_node_ids: list[str]
    shape: str


class OverlapEdge(BaseModel):
    expected_topic_id: str
    actual_node_id: str
    overlap_length: int


def _overlap_length(first: SpanRef, second: SpanRef) -> int:
    overlap_start = max(first.start_char, second.start_char)
    overlap_end = min(first.end_char, second.end_char)
    return max(0, overlap_end - overlap_start)


def _overlap_ratio(expected_span: SpanRef, other_span: SpanRef) -> float:
    overlap = _overlap_length(expected_span, other_span)
    expected_length = expected_span.end_char - expected_span.start_char
    other_length = other_span.end_char - other_span.start_char
    shorter_length = min(expected_length, other_length)
    if shorter_length <= 0:
        return 0.0
    return overlap / shorter_length


def _group_by_document_sorted(
    spans: list[SpanRef],
) -> dict[str, list[SpanRef]]:
    grouped: dict[str, list[SpanRef]] = defaultdict(list)
    for span in spans:
        grouped[span.document_path].append(span)
    for document_spans in grouped.values():
        document_spans.sort(key=lambda span: span.start_char)
    return grouped


def _candidate_indices(
    starts: list[int],
    ends: list[int],
    query_start: int,
    query_end: int,
) -> range:
    lower_bound = bisect.bisect_right(ends, query_start)
    upper_bound = bisect.bisect_left(starts, query_end)
    return range(lower_bound, upper_bound)


def _record_edge_if_overlapping(
    edges_by_key: dict[tuple[str, str], int],
    expected_span: SpanRef,
    other_span: SpanRef,
    minimum_overlap_ratio: float,
) -> None:
    ratio = _overlap_ratio(expected_span, other_span)
    if ratio < minimum_overlap_ratio:
        return
    key = (expected_span.node_id, other_span.node_id)
    overlap = _overlap_length(expected_span, other_span)
    edges_by_key[key] = max(edges_by_key.get(key, 0), overlap)


def _update_edges_for_span(
    edges_by_key: dict[tuple[str, str], int],
    expected_by_document: dict[str, list[SpanRef]],
    other_span: SpanRef,
    minimum_overlap_ratio: float,
) -> None:
    candidates = expected_by_document.get(other_span.document_path, [])
    starts = [candidate.start_char for candidate in candidates]
    ends = [candidate.end_char for candidate in candidates]
    indices = _candidate_indices(
        starts, ends, other_span.start_char, other_span.end_char
    )
    for index in indices:
        _record_edge_if_overlapping(
            edges_by_key, candidates[index], other_span,
            minimum_overlap_ratio,
        )


def _build_overlap_edges(
    edges_by_key: dict[tuple[str, str], int],
) -> list[OverlapEdge]:
    edges = []
    for (expected_topic_id, actual_node_id), overlap_length in (
        edges_by_key.items()
    ):
        edges.append(OverlapEdge(
            expected_topic_id=expected_topic_id,
            actual_node_id=actual_node_id,
            overlap_length=overlap_length,
        ))
    return edges


def find_overlapping_pairs(
    expected_spans: list[SpanRef],
    other_spans: list[SpanRef],
    minimum_overlap_ratio: float,
) -> list[OverlapEdge]:
    expected_by_document = _group_by_document_sorted(expected_spans)
    edges_by_key: dict[tuple[str, str], int] = {}
    for other_span in other_spans:
        _update_edges_for_span(
            edges_by_key, expected_by_document, other_span,
            minimum_overlap_ratio,
        )
    return _build_overlap_edges(edges_by_key)


class _UnionFind:
    def __init__(self, node_ids: list[str]) -> None:
        self._parent = {node_id: node_id for node_id in node_ids}

    def find(self, node_id: str) -> str:
        root = node_id
        while self._parent[root] != root:
            root = self._parent[root]
        while self._parent[node_id] != root:
            self._parent[node_id], node_id = root, self._parent[node_id]
        return root

    def union(self, first_node_id: str, second_node_id: str) -> None:
        first_root = self.find(first_node_id)
        second_root = self.find(second_node_id)
        if first_root != second_root:
            self._parent[first_root] = second_root


def _classify_matched_shape(expected_count: int, actual_count: int) -> str:
    if expected_count == 1 and actual_count == 1:
        return "clean"
    if expected_count == 1 and actual_count > 1:
        return "over_split"
    if expected_count > 1 and actual_count == 1:
        return "over_merge"
    return "tangled"


def _classify_shape(
    expected_topic_ids: list[str],
    actual_node_ids: list[str],
) -> str:
    expected_count = len(expected_topic_ids)
    actual_count = len(actual_node_ids)
    if expected_count == 0:
        return "unmatched_actual"
    if actual_count == 0:
        return "unmatched_expected"
    return _classify_matched_shape(expected_count, actual_count)


def _prefix_ids(node_ids: list[str], prefix: str) -> list[str]:
    prefixed_ids = []
    for node_id in node_ids:
        prefixed_ids.append(prefix + node_id)
    return prefixed_ids


def _group_members_by_root(
    union_find: _UnionFind,
    prefixed_node_ids: list[str],
) -> dict[str, list[str]]:
    members_by_root: dict[str, list[str]] = defaultdict(list)
    for prefixed_node_id in prefixed_node_ids:
        root = union_find.find(prefixed_node_id)
        members_by_root[root].append(prefixed_node_id)
    return members_by_root


def _unprefixed_members(
    prefixed_members: list[str],
    prefix: str,
) -> list[str]:
    matching_members = []
    for member in prefixed_members:
        if member.startswith(prefix):
            matching_members.append(member.removeprefix(prefix))
    return sorted(matching_members)


def _build_match_group(prefixed_members: list[str]) -> MatchGroup:
    expected_topic_ids = _unprefixed_members(prefixed_members, "expected:")
    actual_node_ids = _unprefixed_members(prefixed_members, "actual:")
    shape = _classify_shape(expected_topic_ids, actual_node_ids)
    return MatchGroup(
        expected_topic_ids=expected_topic_ids,
        actual_node_ids=actual_node_ids,
        shape=shape,
    )


def build_match_groups(
    expected_topic_ids: list[str],
    actual_node_ids: list[str],
    edges: list[OverlapEdge],
) -> list[MatchGroup]:
    prefixed_expected = _prefix_ids(expected_topic_ids, "expected:")
    prefixed_actual = _prefix_ids(actual_node_ids, "actual:")
    union_find = _UnionFind(prefixed_expected + prefixed_actual)
    for edge in edges:
        union_find.union(
            "expected:" + edge.expected_topic_id,
            "actual:" + edge.actual_node_id,
        )
    members_by_root = _group_members_by_root(
        union_find, prefixed_expected + prefixed_actual
    )
    groups = []
    for members in members_by_root.values():
        groups.append(_build_match_group(members))
    return groups
