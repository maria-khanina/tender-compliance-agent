from collections.abc import Mapping

from pydantic import BaseModel

from evaluation.matching import MatchGroup, OverlapEdge


DANGEROUS_ACTUAL_VERDICTS = frozenset({
    "non_compliant",
    "insufficient_information",
    "contradictory",
})


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


class VerdictConfusionCell(BaseModel):
    expected_verdict: str
    actual_verdict: str
    count: int


class VerdictAccuracyResult(BaseModel):
    confusion_matrix: list[VerdictConfusionCell]
    clean_match_count: int
    false_compliant_rate: float
    false_compliant_group_ids: list[str]
    false_issue_rate: float
    false_issue_group_ids: list[str]
    unscored_group_ids: list[str]
    not_verifiable_group_ids: list[str]


class EvidenceResult(BaseModel):
    citation_verified_rate: float
    unverified_evidence_count: int
    total_evidence_count: int


class EvidenceRecallResult(BaseModel):
    recall: float
    matched_topic_count: int
    total_topic_count: int
    missed_topic_ids: list[str]


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


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


def _group_label(group: MatchGroup) -> str:
    expected_part = "+".join(group.expected_topic_ids)
    actual_part = "+".join(group.actual_node_ids)
    return f"{expected_part} -> {actual_part}"


def _topic_requires_issue(acceptable_verdicts: list[str]) -> bool:
    return "compliant" not in acceptable_verdicts


def _topic_requires_compliant_only(acceptable_verdicts: list[str]) -> bool:
    for verdict in acceptable_verdicts:
        if verdict in DANGEROUS_ACTUAL_VERDICTS:
            return False
    return True


def _any_topic_requires_issue(
    topic_acceptable_verdicts: list[list[str]],
) -> bool:
    for acceptable in topic_acceptable_verdicts:
        if _topic_requires_issue(acceptable):
            return True
    return False


def _any_topic_requires_compliant_only(
    topic_acceptable_verdicts: list[list[str]],
) -> bool:
    for acceptable in topic_acceptable_verdicts:
        if _topic_requires_compliant_only(acceptable):
            return True
    return False


def _all_actual_compliant(actual_verdicts: list[str]) -> bool:
    for verdict in actual_verdicts:
        if verdict != "compliant":
            return False
    return True


def _any_actual_issue(actual_verdicts: list[str]) -> bool:
    for verdict in actual_verdicts:
        if verdict in DANGEROUS_ACTUAL_VERDICTS:
            return True
    return False


def _is_false_compliant(
    topic_acceptable_verdicts: list[list[str]],
    actual_verdicts: list[str],
) -> bool:
    return (
        _any_topic_requires_issue(topic_acceptable_verdicts)
        and _all_actual_compliant(actual_verdicts)
    )


def _is_false_issue(
    topic_acceptable_verdicts: list[list[str]],
    actual_verdicts: list[str],
) -> bool:
    return (
        _any_topic_requires_compliant_only(topic_acceptable_verdicts)
        and _any_actual_issue(actual_verdicts)
    )


def _has_verdict_for_all_actual(
    group: MatchGroup,
    actual_verdict_by_requirement: Mapping[str, str],
) -> bool:
    for node_id in group.actual_node_ids:
        if node_id not in actual_verdict_by_requirement:
            return False
    return True


def _has_acceptable_verdicts_for_all_topics(
    group: MatchGroup,
    acceptable_verdicts_by_topic: Mapping[str, list[str] | None],
) -> bool:
    for topic_id in group.expected_topic_ids:
        if acceptable_verdicts_by_topic.get(topic_id) is None:
            return False
    return True


def _is_scorable_group(
    group: MatchGroup,
    acceptable_verdicts_by_topic: Mapping[str, list[str] | None],
    actual_verdict_by_requirement: Mapping[str, str],
) -> bool:
    if group.shape in ("unmatched_expected", "unmatched_actual"):
        return False
    if not _has_acceptable_verdicts_for_all_topics(
        group, acceptable_verdicts_by_topic
    ):
        return False
    return _has_verdict_for_all_actual(group, actual_verdict_by_requirement)


def _is_not_verifiable_group(
    group: MatchGroup,
    acceptable_verdicts_by_topic: Mapping[str, list[str] | None],
    actual_verdict_by_requirement: Mapping[str, str],
) -> bool:
    if group.shape in ("unmatched_expected", "unmatched_actual"):
        return False
    if not _has_acceptable_verdicts_for_all_topics(
        group, acceptable_verdicts_by_topic
    ):
        return False
    return not _has_verdict_for_all_actual(
        group, actual_verdict_by_requirement
    )


def _scorable_groups(
    groups: list[MatchGroup],
    acceptable_verdicts_by_topic: Mapping[str, list[str] | None],
    actual_verdict_by_requirement: Mapping[str, str],
) -> list[MatchGroup]:
    scorable = []
    for group in groups:
        if _is_scorable_group(
            group, acceptable_verdicts_by_topic, actual_verdict_by_requirement
        ):
            scorable.append(group)
    return scorable


def _not_verifiable_group_labels(
    groups: list[MatchGroup],
    acceptable_verdicts_by_topic: Mapping[str, list[str] | None],
    actual_verdict_by_requirement: Mapping[str, str],
) -> list[str]:
    labels = []
    for group in groups:
        if _is_not_verifiable_group(
            group, acceptable_verdicts_by_topic, actual_verdict_by_requirement
        ):
            labels.append(_group_label(group))
    return labels


def _actual_verdicts_for_group(
    group: MatchGroup,
    actual_verdict_by_requirement: Mapping[str, str],
) -> list[str]:
    verdicts = []
    for node_id in group.actual_node_ids:
        verdicts.append(actual_verdict_by_requirement[node_id])
    return verdicts


def _topic_acceptable_verdicts_for_group(
    group: MatchGroup,
    acceptable_verdicts_by_topic: Mapping[str, list[str] | None],
) -> list[list[str]]:
    acceptable_lists = []
    for topic_id in group.expected_topic_ids:
        acceptable_lists.append(
            acceptable_verdicts_by_topic[topic_id] or []
        )
    return acceptable_lists


class _VerdictAccumulator:
    def __init__(self) -> None:
        self.confusion_counts: dict[tuple[str, str], int] = {}
        self.false_compliant_ids: list[str] = []
        self.false_issue_ids: list[str] = []
        self.unscored_ids: list[str] = []


def _record_confusion_cell(
    accumulator: _VerdictAccumulator,
    group: MatchGroup,
    acceptable_verdicts_by_topic: Mapping[str, list[str] | None],
    actual_verdicts: list[str],
) -> None:
    topic_id = group.expected_topic_ids[0]
    acceptable = acceptable_verdicts_by_topic[topic_id] or []
    primary_expected = acceptable[0]
    key = (primary_expected, actual_verdicts[0])
    accumulator.confusion_counts[key] = (
        accumulator.confusion_counts.get(key, 0) + 1
    )


def _score_group(
    group: MatchGroup,
    acceptable_verdicts_by_topic: Mapping[str, list[str] | None],
    actual_verdict_by_requirement: Mapping[str, str],
    accumulator: _VerdictAccumulator,
) -> None:
    actual_verdicts = _actual_verdicts_for_group(
        group, actual_verdict_by_requirement
    )
    if group.shape == "clean":
        _record_confusion_cell(
            accumulator, group, acceptable_verdicts_by_topic,
            actual_verdicts,
        )
    else:
        accumulator.unscored_ids.append(_group_label(group))
    topic_acceptable_verdicts = _topic_acceptable_verdicts_for_group(
        group, acceptable_verdicts_by_topic
    )
    if _is_false_compliant(topic_acceptable_verdicts, actual_verdicts):
        accumulator.false_compliant_ids.append(_group_label(group))
    if _is_false_issue(topic_acceptable_verdicts, actual_verdicts):
        accumulator.false_issue_ids.append(_group_label(group))


def _confusion_matrix_from_counts(
    confusion_counts: dict[tuple[str, str], int],
) -> list[VerdictConfusionCell]:
    cells = []
    for (expected_verdict, actual_verdict), count in (
        confusion_counts.items()
    ):
        cells.append(VerdictConfusionCell(
            expected_verdict=expected_verdict,
            actual_verdict=actual_verdict,
            count=count,
        ))
    return cells


def _count_clean_matches(groups: list[MatchGroup]) -> int:
    clean_count = 0
    for group in groups:
        if group.shape == "clean":
            clean_count += 1
    return clean_count


def _build_verdict_accuracy_result(
    scorable_groups: list[MatchGroup],
    accumulator: _VerdictAccumulator,
    not_verifiable_group_ids: list[str],
) -> VerdictAccuracyResult:
    total_groups = len(scorable_groups)
    false_compliant_rate = _safe_ratio(
        len(accumulator.false_compliant_ids), total_groups
    )
    false_issue_rate = _safe_ratio(
        len(accumulator.false_issue_ids), total_groups
    )
    clean_match_count = _count_clean_matches(scorable_groups)
    return VerdictAccuracyResult(
        confusion_matrix=_confusion_matrix_from_counts(
            accumulator.confusion_counts
        ),
        clean_match_count=clean_match_count,
        false_compliant_rate=false_compliant_rate,
        false_compliant_group_ids=accumulator.false_compliant_ids,
        false_issue_rate=false_issue_rate,
        false_issue_group_ids=accumulator.false_issue_ids,
        unscored_group_ids=accumulator.unscored_ids,
        not_verifiable_group_ids=not_verifiable_group_ids,
    )


def compute_verdict_accuracy(
    groups: list[MatchGroup],
    acceptable_verdicts_by_topic: Mapping[str, list[str] | None],
    actual_verdict_by_requirement: Mapping[str, str],
) -> VerdictAccuracyResult:
    scorable_groups = _scorable_groups(
        groups, acceptable_verdicts_by_topic, actual_verdict_by_requirement
    )
    not_verifiable_group_ids = _not_verifiable_group_labels(
        groups, acceptable_verdicts_by_topic, actual_verdict_by_requirement
    )
    accumulator = _VerdictAccumulator()
    for group in scorable_groups:
        _score_group(
            group, acceptable_verdicts_by_topic,
            actual_verdict_by_requirement, accumulator,
        )
    return _build_verdict_accuracy_result(
        scorable_groups, accumulator, not_verifiable_group_ids
    )


def _count_unverified(citation_verified_flags: list[bool]) -> int:
    unverified_count = 0
    for is_verified in citation_verified_flags:
        if not is_verified:
            unverified_count += 1
    return unverified_count


def compute_evidence_citation_verified_rate(
    citation_verified_flags: list[bool],
) -> EvidenceResult:
    total = len(citation_verified_flags)
    unverified_count = _count_unverified(citation_verified_flags)
    rate = _safe_ratio(total - unverified_count, total)
    return EvidenceResult(
        citation_verified_rate=rate,
        unverified_evidence_count=unverified_count,
        total_evidence_count=total,
    )


def _missed_topic_ids(
    expected_topic_ids: list[str],
    matched_topic_ids: set[str],
) -> list[str]:
    missed = []
    for topic_id in expected_topic_ids:
        if topic_id not in matched_topic_ids:
            missed.append(topic_id)
    return missed


def compute_evidence_recall(
    expected_topic_ids: list[str],
    matched_topic_ids: set[str],
) -> EvidenceRecallResult:
    missed = _missed_topic_ids(expected_topic_ids, matched_topic_ids)
    total = len(expected_topic_ids)
    matched_count = total - len(missed)
    recall = _safe_ratio(matched_count, total)
    return EvidenceRecallResult(
        recall=recall,
        matched_topic_count=matched_count,
        total_topic_count=total,
        missed_topic_ids=missed,
    )
