from collections.abc import Mapping

from pydantic import BaseModel

from evaluation.matching import MatchGroup


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


DANGEROUS_ACTUAL_VERDICTS = frozenset({
    "non_compliant",
    "insufficient_information",
    "contradictory",
})


class VerdictConfusionCell(BaseModel):
    expected_verdict: str
    actual_verdict: str
    count: int


class VerdictAccuracyResult(BaseModel):
    confusion_matrix: list[VerdictConfusionCell]
    clean_match_count: int
    false_compliant_rate: float
    false_compliant_groups: list[MatchGroup]
    false_issue_rate: float
    false_issue_groups: list[MatchGroup]
    unscored_groups: list[MatchGroup]
    not_verifiable_groups: list[MatchGroup]


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


def _not_verifiable_groups(
    groups: list[MatchGroup],
    acceptable_verdicts_by_topic: Mapping[str, list[str] | None],
    actual_verdict_by_requirement: Mapping[str, str],
) -> list[MatchGroup]:
    not_verifiable = []
    for group in groups:
        if _is_not_verifiable_group(
            group, acceptable_verdicts_by_topic, actual_verdict_by_requirement
        ):
            not_verifiable.append(group)
    return not_verifiable


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
        self.false_compliant_groups: list[MatchGroup] = []
        self.false_issue_groups: list[MatchGroup] = []
        self.unscored_groups: list[MatchGroup] = []


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
        accumulator.unscored_groups.append(group)
    topic_acceptable_verdicts = _topic_acceptable_verdicts_for_group(
        group, acceptable_verdicts_by_topic
    )
    if _is_false_compliant(topic_acceptable_verdicts, actual_verdicts):
        accumulator.false_compliant_groups.append(group)
    if _is_false_issue(topic_acceptable_verdicts, actual_verdicts):
        accumulator.false_issue_groups.append(group)


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
    not_verifiable_groups: list[MatchGroup],
) -> VerdictAccuracyResult:
    total_groups = len(scorable_groups)
    false_compliant_rate = _safe_ratio(
        len(accumulator.false_compliant_groups), total_groups
    )
    false_issue_rate = _safe_ratio(
        len(accumulator.false_issue_groups), total_groups
    )
    clean_match_count = _count_clean_matches(scorable_groups)
    return VerdictAccuracyResult(
        confusion_matrix=_confusion_matrix_from_counts(
            accumulator.confusion_counts
        ),
        clean_match_count=clean_match_count,
        false_compliant_rate=false_compliant_rate,
        false_compliant_groups=accumulator.false_compliant_groups,
        false_issue_rate=false_issue_rate,
        false_issue_groups=accumulator.false_issue_groups,
        unscored_groups=accumulator.unscored_groups,
        not_verifiable_groups=not_verifiable_groups,
    )


def compute_verdict_accuracy(
    groups: list[MatchGroup],
    acceptable_verdicts_by_topic: Mapping[str, list[str] | None],
    actual_verdict_by_requirement: Mapping[str, str],
) -> VerdictAccuracyResult:
    scorable_groups = _scorable_groups(
        groups, acceptable_verdicts_by_topic, actual_verdict_by_requirement
    )
    not_verifiable = _not_verifiable_groups(
        groups, acceptable_verdicts_by_topic, actual_verdict_by_requirement
    )
    accumulator = _VerdictAccumulator()
    for group in scorable_groups:
        _score_group(
            group, acceptable_verdicts_by_topic,
            actual_verdict_by_requirement, accumulator,
        )
    return _build_verdict_accuracy_result(
        scorable_groups, accumulator, not_verifiable
    )
