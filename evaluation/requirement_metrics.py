from pydantic import BaseModel

from evaluation.matching import MatchGroup, OverlapEdge


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


class RecallResult(BaseModel):
    recall: float
    matched_topic_count: int
    total_topic_count: int
    missed_topic_ids: list[str]
    over_split_topic_ids: list[str]
    over_merge_topic_ids: list[str]
    tangled_topic_ids: list[str]


class PrecisionResult(BaseModel):
    citation_verified_rate: float
    unverified_requirement_ids: list[str]
    classification_precision: float
    excluded_overlap_requirement_ids: list[str]
    unexplained_requirement_ids: list[str]


class CoverageFlag(BaseModel):
    expected_topic_ids: list[str]
    actual_node_ids: list[str]
    expected_covered_ratio: float
    actual_explained_ratio: float


class IsMandatoryResult(BaseModel):
    accuracy: float
    scored_topic_count: int
    mismatched_topic_ids: list[str]


def _groups_by_shape(groups: list[MatchGroup]) -> dict[str, list[MatchGroup]]:
    grouped: dict[str, list[MatchGroup]] = {}
    for group in groups:
        grouped.setdefault(group.shape, []).append(group)
    return grouped


def _topic_ids_for_shape(
    by_shape: dict[str, list[MatchGroup]],
    shape: str,
) -> list[str]:
    topic_ids = []
    for group in by_shape.get(shape, []):
        topic_ids.extend(group.expected_topic_ids)
    return topic_ids


def compute_requirement_recall(groups: list[MatchGroup]) -> RecallResult:
    by_shape = _groups_by_shape(groups)
    missed = _topic_ids_for_shape(by_shape, "unmatched_expected")
    over_split = _topic_ids_for_shape(by_shape, "over_split")
    over_merge = _topic_ids_for_shape(by_shape, "over_merge")
    tangled = _topic_ids_for_shape(by_shape, "tangled")
    total_topic_count = sum(len(g.expected_topic_ids) for g in groups)
    matched_topic_count = total_topic_count - len(missed)
    recall = _safe_ratio(matched_topic_count, total_topic_count)
    return RecallResult(
        recall=recall,
        matched_topic_count=matched_topic_count,
        total_topic_count=total_topic_count,
        missed_topic_ids=missed,
        over_split_topic_ids=over_split,
        over_merge_topic_ids=over_merge,
        tangled_topic_ids=tangled,
    )


def _unverified_requirement_ids(
    citation_verified_by_requirement_id: dict[str, bool],
) -> list[str]:
    unverified = []
    for requirement_id, is_verified in (
        citation_verified_by_requirement_id.items()
    ):
        if not is_verified:
            unverified.append(requirement_id)
    return unverified


def _unmatched_actual_ids(groups: list[MatchGroup]) -> set[str]:
    unmatched_ids = set()
    for group in groups:
        if group.shape == "unmatched_actual":
            unmatched_ids.update(group.actual_node_ids)
    return unmatched_ids


def compute_precision(
    groups: list[MatchGroup],
    citation_verified_by_requirement_id: dict[str, bool],
    excluded_overlap_requirement_ids: set[str],
) -> PrecisionResult:
    all_requirement_ids = list(citation_verified_by_requirement_id.keys())
    unverified = _unverified_requirement_ids(
        citation_verified_by_requirement_id
    )
    total = len(all_requirement_ids)
    verified_rate = _safe_ratio(total - len(unverified), total)
    unmatched_actual_ids = _unmatched_actual_ids(groups)
    unexplained = sorted(
        unmatched_actual_ids - excluded_overlap_requirement_ids
    )
    classification_precision = _safe_ratio(total - len(unexplained), total)
    return PrecisionResult(
        citation_verified_rate=verified_rate,
        unverified_requirement_ids=sorted(unverified),
        classification_precision=classification_precision,
        excluded_overlap_requirement_ids=sorted(
            excluded_overlap_requirement_ids
        ),
        unexplained_requirement_ids=unexplained,
    )


def _overlap_by_pair(edges: list[OverlapEdge]) -> dict[tuple[str, str], int]:
    overlap_by_pair = {}
    for edge in edges:
        key = (edge.expected_topic_id, edge.actual_node_id)
        overlap_by_pair[key] = edge.overlap_length
    return overlap_by_pair


def _total_overlap_for_group(
    group: MatchGroup,
    overlap_by_pair: dict[tuple[str, str], int],
) -> int:
    total = 0
    for expected_id in group.expected_topic_ids:
        for actual_id in group.actual_node_ids:
            total += overlap_by_pair.get((expected_id, actual_id), 0)
    return total


def _summed_lengths(node_ids: list[str], lengths: dict[str, int]) -> int:
    total = 0
    for node_id in node_ids:
        total += lengths[node_id]
    return total


def _coverage_flag_for_group(
    group: MatchGroup,
    overlap_by_pair: dict[tuple[str, str], int],
    expected_lengths: dict[str, int],
    actual_lengths: dict[str, int],
    coverage_threshold: float,
) -> CoverageFlag | None:
    total_overlap = _total_overlap_for_group(group, overlap_by_pair)
    expected_total = _summed_lengths(
        group.expected_topic_ids, expected_lengths
    )
    actual_total = _summed_lengths(group.actual_node_ids, actual_lengths)
    expected_covered = _safe_ratio(total_overlap, expected_total)
    actual_explained = _safe_ratio(total_overlap, actual_total)
    is_covered_enough = (
        expected_covered >= coverage_threshold
        and actual_explained >= coverage_threshold
    )
    if is_covered_enough:
        return None
    return CoverageFlag(
        expected_topic_ids=group.expected_topic_ids,
        actual_node_ids=group.actual_node_ids,
        expected_covered_ratio=expected_covered,
        actual_explained_ratio=actual_explained,
    )


def compute_coverage_flags(
    groups: list[MatchGroup],
    edges: list[OverlapEdge],
    expected_lengths: dict[str, int],
    actual_lengths: dict[str, int],
    coverage_threshold: float,
) -> list[CoverageFlag]:
    overlap_by_pair = _overlap_by_pair(edges)
    flags = []
    for group in groups:
        if not group.expected_topic_ids or not group.actual_node_ids:
            continue
        flag = _coverage_flag_for_group(
            group, overlap_by_pair, expected_lengths, actual_lengths,
            coverage_threshold,
        )
        if flag is not None:
            flags.append(flag)
    return flags


def _mismatched_mandatory_topics(
    clean_groups: list[MatchGroup],
    expected_is_mandatory: dict[str, bool],
    actual_is_mandatory: dict[str, bool],
) -> list[str]:
    mismatched = []
    for group in clean_groups:
        topic_id = group.expected_topic_ids[0]
        requirement_id = group.actual_node_ids[0]
        if expected_is_mandatory[topic_id] != actual_is_mandatory[
            requirement_id
        ]:
            mismatched.append(topic_id)
    return mismatched


def compute_is_mandatory_accuracy(
    groups: list[MatchGroup],
    expected_is_mandatory: dict[str, bool],
    actual_is_mandatory: dict[str, bool],
) -> IsMandatoryResult:
    clean_groups = _groups_by_shape(groups).get("clean", [])
    mismatched = _mismatched_mandatory_topics(
        clean_groups, expected_is_mandatory, actual_is_mandatory
    )
    scored_count = len(clean_groups)
    accuracy = _safe_ratio(scored_count - len(mismatched), scored_count)
    return IsMandatoryResult(
        accuracy=accuracy,
        scored_topic_count=scored_count,
        mismatched_topic_ids=mismatched,
    )
