from pydantic import BaseModel

from evaluation.matching import MatchGroup, SpanRef, overlap_length


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
    unexplained_requirement_ids: list[str]


class CoverageFlag(BaseModel):
    true_topic_ids: list[str]
    predicted_node_ids: list[str]
    true_covered_ratio: float
    predicted_explained_ratio: float


class IsMandatoryResult(BaseModel):
    accuracy: float
    scored_topic_count: int
    mismatched_groups: list[MatchGroup]


class IsTextVerifiableResult(BaseModel):
    accuracy: float
    scored_topic_count: int
    mismatched_groups: list[MatchGroup]


class ApplicabilityConditionDetectionResult(BaseModel):
    detection_recall: float
    true_condition_topic_count: int
    detected_topic_count: int
    missed_condition_topic_ids: list[str]
    false_condition_requirement_ids: list[str]


class ConditionHoldsResult(BaseModel):
    accuracy: float
    scored_topic_count: int
    mismatched_groups: list[MatchGroup]


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
        topic_ids.extend(group.true_topic_ids)
    return topic_ids


def compute_requirement_recall(groups: list[MatchGroup]) -> RecallResult:
    by_shape = _groups_by_shape(groups)
    missed = _topic_ids_for_shape(by_shape, "unmatched_true")
    over_split = _topic_ids_for_shape(by_shape, "over_split")
    over_merge = _topic_ids_for_shape(by_shape, "over_merge")
    tangled = _topic_ids_for_shape(by_shape, "tangled")
    total_topic_count = sum(len(g.true_topic_ids) for g in groups)
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


def _unmatched_predicted_ids(groups: list[MatchGroup]) -> set[str]:
    unmatched_ids = set()
    for group in groups:
        if group.shape == "unmatched_predicted":
            unmatched_ids.update(group.predicted_node_ids)
    return unmatched_ids


def compute_precision(
    groups: list[MatchGroup],
    citation_verified_by_requirement_id: dict[str, bool],
) -> PrecisionResult:
    all_requirement_ids = list(citation_verified_by_requirement_id.keys())
    unverified = _unverified_requirement_ids(
        citation_verified_by_requirement_id
    )
    total = len(all_requirement_ids)
    verified_rate = _safe_ratio(total - len(unverified), total)
    unexplained = sorted(_unmatched_predicted_ids(groups))
    classification_precision = _safe_ratio(total - len(unexplained), total)
    return PrecisionResult(
        citation_verified_rate=verified_rate,
        unverified_requirement_ids=sorted(unverified),
        classification_precision=classification_precision,
        unexplained_requirement_ids=unexplained,
    )


def _spans_by_node(spans: list[SpanRef]) -> dict[str, list[SpanRef]]:
    by_node: dict[str, list[SpanRef]] = {}
    for span in spans:
        by_node.setdefault(span.node_id, []).append(span)
    return by_node


def _collect_spans(
    node_ids: list[str],
    spans_by_node: dict[str, list[SpanRef]],
) -> list[SpanRef]:
    collected = []
    for node_id in node_ids:
        collected.extend(spans_by_node.get(node_id, []))
    return collected


def _pairwise_overlap(
    first_spans: list[SpanRef],
    second_spans: list[SpanRef],
) -> int:
    total = 0
    for first in first_spans:
        for second in second_spans:
            if first.document_path != second.document_path:
                continue
            total += overlap_length(first, second)
    return total


def _relevant_length(
    spans: list[SpanRef],
    reference_spans: list[SpanRef],
) -> int:
    total = 0
    for span in spans:
        for reference in reference_spans:
            if reference.document_path != span.document_path:
                continue
            if overlap_length(reference, span) > 0:
                total += span.end_char - span.start_char
                break
    return total


def _coverage_flag_for_group(
    group: MatchGroup,
    true_spans_by_topic: dict[str, list[SpanRef]],
    predicted_spans_by_node: dict[str, list[SpanRef]],
    coverage_threshold: float,
) -> CoverageFlag | None:
    true_spans = _collect_spans(group.true_topic_ids, true_spans_by_topic)
    predicted_spans = _collect_spans(
        group.predicted_node_ids, predicted_spans_by_node
    )
    total_overlap = _pairwise_overlap(true_spans, predicted_spans)
    true_total = sum(span.end_char - span.start_char for span in true_spans)
    predicted_total = _relevant_length(predicted_spans, true_spans)
    true_covered = _safe_ratio(total_overlap, true_total)
    predicted_explained = _safe_ratio(total_overlap, predicted_total)
    is_covered_enough = (
        true_covered >= coverage_threshold
        and predicted_explained >= coverage_threshold
    )
    if is_covered_enough:
        return None
    return CoverageFlag(
        true_topic_ids=group.true_topic_ids,
        predicted_node_ids=group.predicted_node_ids,
        true_covered_ratio=true_covered,
        predicted_explained_ratio=predicted_explained,
    )


def compute_coverage_flags(
    groups: list[MatchGroup],
    true_spans: list[SpanRef],
    predicted_spans: list[SpanRef],
    coverage_threshold: float,
) -> list[CoverageFlag]:
    true_spans_by_topic = _spans_by_node(true_spans)
    predicted_spans_by_node = _spans_by_node(predicted_spans)
    flags = []
    for group in groups:
        if group.shape != "clean":
            continue
        flag = _coverage_flag_for_group(
            group, true_spans_by_topic, predicted_spans_by_node,
            coverage_threshold,
        )
        if flag is not None:
            flags.append(flag)
    return flags


def _scorable_flag_groups(groups: list[MatchGroup]) -> list[MatchGroup]:
    scorable = []
    for group in groups:
        if group.shape in ("clean", "over_split", "over_merge"):
            scorable.append(group)
    return scorable


def _group_flag_matches(
    group: MatchGroup,
    true_flag_by_topic: dict[str, bool],
    predicted_flag_by_requirement: dict[str, bool],
) -> bool:
    if group.shape == "over_merge":
        predicted_value = predicted_flag_by_requirement[
            group.predicted_node_ids[0]
        ]
        for topic_id in group.true_topic_ids:
            if true_flag_by_topic[topic_id] != predicted_value:
                return False
        return True
    true_value = true_flag_by_topic[group.true_topic_ids[0]]
    for requirement_id in group.predicted_node_ids:
        if predicted_flag_by_requirement[requirement_id] != true_value:
            return False
    return True


def _mismatched_flag_groups(
    scorable_groups: list[MatchGroup],
    true_flag_by_topic: dict[str, bool],
    predicted_flag_by_requirement: dict[str, bool],
) -> list[MatchGroup]:
    mismatched = []
    for group in scorable_groups:
        if not _group_flag_matches(
            group, true_flag_by_topic, predicted_flag_by_requirement
        ):
            mismatched.append(group)
    return mismatched


def compute_is_mandatory_accuracy(
    groups: list[MatchGroup],
    true_is_mandatory: dict[str, bool],
    predicted_is_mandatory: dict[str, bool],
) -> IsMandatoryResult:
    scorable_groups = _scorable_flag_groups(groups)
    mismatched_groups = _mismatched_flag_groups(
        scorable_groups, true_is_mandatory, predicted_is_mandatory
    )
    scored_count = len(scorable_groups)
    accuracy = _safe_ratio(
        scored_count - len(mismatched_groups), scored_count
    )
    return IsMandatoryResult(
        accuracy=accuracy,
        scored_topic_count=scored_count,
        mismatched_groups=mismatched_groups,
    )


def _condition_spans_overlap(
    true_span: SpanRef,
    predicted_span: SpanRef,
    minimum_overlap_ratio: float,
) -> bool:
    if true_span.document_path != predicted_span.document_path:
        return False
    overlap = overlap_length(true_span, predicted_span)
    true_length = true_span.end_char - true_span.start_char
    if true_length <= 0:
        return False
    return (overlap / true_length) >= minimum_overlap_ratio


def _clean_groups(groups: list[MatchGroup]) -> list[MatchGroup]:
    return [group for group in groups if group.shape == "clean"]


def compute_applicability_condition_detection(
    groups: list[MatchGroup],
    true_condition_spans_by_topic: dict[str, SpanRef],
    predicted_condition_spans_by_requirement: dict[str, SpanRef],
    minimum_overlap_ratio: float,
) -> ApplicabilityConditionDetectionResult:
    missed: list[str] = []
    detected_count = 0
    false_condition: list[str] = []
    for group in _clean_groups(groups):
        topic_id = group.true_topic_ids[0]
        requirement_id = group.predicted_node_ids[0]
        true_span = true_condition_spans_by_topic.get(topic_id)
        predicted_span = predicted_condition_spans_by_requirement.get(
            requirement_id
        )
        if true_span is None:
            if predicted_span is not None:
                false_condition.append(requirement_id)
            continue
        if predicted_span is not None and _condition_spans_overlap(
            true_span, predicted_span, minimum_overlap_ratio
        ):
            detected_count += 1
        else:
            missed.append(topic_id)
    true_condition_topic_count = detected_count + len(missed)
    detection_recall = _safe_ratio(detected_count, true_condition_topic_count)
    return ApplicabilityConditionDetectionResult(
        detection_recall=detection_recall,
        true_condition_topic_count=true_condition_topic_count,
        detected_topic_count=detected_count,
        missed_condition_topic_ids=missed,
        false_condition_requirement_ids=false_condition,
    )


def _all_topics_have_true_condition(
    group: MatchGroup,
    true_condition_holds_by_topic: dict[str, bool],
) -> bool:
    for topic_id in group.true_topic_ids:
        if topic_id not in true_condition_holds_by_topic:
            return False
    return True


def _groups_with_true_condition(
    groups: list[MatchGroup],
    true_condition_holds_by_topic: dict[str, bool],
) -> list[MatchGroup]:
    scorable = []
    for group in _scorable_flag_groups(groups):
        if _all_topics_have_true_condition(
            group, true_condition_holds_by_topic
        ):
            scorable.append(group)
    return scorable


def compute_condition_holds_accuracy(
    groups: list[MatchGroup],
    true_condition_holds_by_topic: dict[str, bool],
    predicted_condition_holds_by_requirement: dict[str, bool],
) -> ConditionHoldsResult:
    scorable_groups = _groups_with_true_condition(
        groups, true_condition_holds_by_topic
    )
    mismatched_groups = _mismatched_flag_groups(
        scorable_groups, true_condition_holds_by_topic,
        predicted_condition_holds_by_requirement,
    )
    scored_count = len(scorable_groups)
    accuracy = _safe_ratio(
        scored_count - len(mismatched_groups), scored_count
    )
    return ConditionHoldsResult(
        accuracy=accuracy,
        scored_topic_count=scored_count,
        mismatched_groups=mismatched_groups,
    )


def compute_is_text_verifiable_accuracy(
    groups: list[MatchGroup],
    true_is_text_verifiable: dict[str, bool],
    predicted_is_text_verifiable: dict[str, bool],
) -> IsTextVerifiableResult:
    scorable_groups = _scorable_flag_groups(groups)
    mismatched_groups = _mismatched_flag_groups(
        scorable_groups, true_is_text_verifiable, predicted_is_text_verifiable
    )
    scored_count = len(scorable_groups)
    accuracy = _safe_ratio(
        scored_count - len(mismatched_groups), scored_count
    )
    return IsTextVerifiableResult(
        accuracy=accuracy,
        scored_topic_count=scored_count,
        mismatched_groups=mismatched_groups,
    )
