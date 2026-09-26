from config import (
    EVALUATION_EVIDENCE_MATCH_MINIMUM_OVERLAP_RATIO,
    EVALUATION_REQUIREMENT_MATCH_MINIMUM_OVERLAP_RATIO,
)
from evaluation.fixtures import (
    TrueRequirementsFixture,
    TrueSource,
    TrueVerdict,
    TrueVerdictsFixture,
)
from evaluation.matching import (
    MatchGroup,
    SpanRef,
    build_match_groups,
    find_overlapping_pairs,
)
from schemas import Chunk, Requirement, RetrievedContextRecord


def _spans_from_source(node_id: str, source: TrueSource) -> list[SpanRef]:
    spans = []
    for span in source.spans:
        if not span.used_for_matching:
            continue
        spans.append(SpanRef(
            node_id=node_id,
            document_path=source.document_path,
            start_char=span.start_char,
            end_char=span.end_char,
        ))
    return spans


def true_requirement_spans(
    fixture: TrueRequirementsFixture,
) -> list[SpanRef]:
    spans = []
    for requirement in fixture.requirements:
        spans.extend(_spans_from_source(requirement.topic_id, requirement.source))
    return spans


def predicted_requirement_spans(
    requirements: list[Requirement],
) -> list[SpanRef]:
    spans = []
    for requirement in requirements:
        for citation in requirement.citations:
            if not citation.used_for_matching:
                continue
            if citation.start_char is None or citation.end_char is None:
                continue
            spans.append(SpanRef(
                node_id=requirement.requirement_id,
                document_path=citation.document_path,
                start_char=citation.start_char,
                end_char=citation.end_char,
            ))
    return spans


def _all_citations_verified(requirement: Requirement) -> bool:
    for citation in requirement.citations:
        if not citation.citation_verified:
            return False
    return True


def citation_verified_by_requirement(
    requirements: list[Requirement],
) -> dict[str, bool]:
    verified_by_requirement = {}
    for requirement in requirements:
        verified_by_requirement[requirement.requirement_id] = (
            _all_citations_verified(requirement)
        )
    return verified_by_requirement


def _topic_ids_of_requirements(
    fixture: TrueRequirementsFixture,
) -> list[str]:
    topic_ids = []
    for requirement in fixture.requirements:
        topic_ids.append(requirement.topic_id)
    return topic_ids


def _requirement_ids_of(requirements: list[Requirement]) -> list[str]:
    requirement_ids = []
    for requirement in requirements:
        requirement_ids.append(requirement.requirement_id)
    return requirement_ids


def build_match_groups_for_requirements(
    fixture: TrueRequirementsFixture,
    predicted_requirements: list[Requirement],
) -> list[MatchGroup]:
    true_spans = true_requirement_spans(fixture)
    predicted_spans = predicted_requirement_spans(predicted_requirements)
    edges = find_overlapping_pairs(
        true_spans, predicted_spans,
        EVALUATION_REQUIREMENT_MATCH_MINIMUM_OVERLAP_RATIO,
    )
    true_topic_ids = _topic_ids_of_requirements(fixture)
    predicted_requirement_ids = _requirement_ids_of(predicted_requirements)
    return build_match_groups(
        true_topic_ids, predicted_requirement_ids, edges
    )


def group_lookup_by_topic(
    groups: list[MatchGroup],
) -> dict[str, MatchGroup]:
    lookup = {}
    for group in groups:
        for topic_id in group.true_topic_ids:
            lookup[topic_id] = group
    return lookup


def _retrieved_spans_for_group(
    group: MatchGroup,
    retrieved_by_requirement: dict[str, list[Chunk]],
) -> list[SpanRef]:
    spans = []
    for requirement_id in group.predicted_node_ids:
        for chunk in retrieved_by_requirement.get(requirement_id, []):
            spans.append(SpanRef(
                node_id=requirement_id,
                document_path=chunk.document_path,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
            ))
    return spans


def _true_evidence_spans(verdict: TrueVerdict) -> list[SpanRef]:
    spans = []
    for evidence in verdict.evidence:
        spans.append(SpanRef(
            node_id=verdict.topic_id,
            document_path=evidence.document_path,
            start_char=evidence.start_char,
            end_char=evidence.end_char,
        ))
    return spans


def _has_evidence_overlap(
    verdict: TrueVerdict,
    group_by_topic: dict[str, MatchGroup],
    retrieved_by_requirement: dict[str, list[Chunk]],
) -> bool:
    group = group_by_topic.get(verdict.topic_id)
    if group is None:
        return False
    retrieved_spans = _retrieved_spans_for_group(
        group, retrieved_by_requirement
    )
    true_spans = _true_evidence_spans(verdict)
    edges = find_overlapping_pairs(
        true_spans, retrieved_spans,
        EVALUATION_EVIDENCE_MATCH_MINIMUM_OVERLAP_RATIO,
    )
    return len(edges) > 0


def retrieved_by_requirement(
    retrieved_context: list[RetrievedContextRecord],
) -> dict[str, list[Chunk]]:
    by_requirement = {}
    for record in retrieved_context:
        by_requirement[record.requirement_id] = record.retrieved_context
    return by_requirement


def topics_with_evidence(
    fixture: TrueVerdictsFixture,
) -> list[TrueVerdict]:
    topics = []
    for verdict in fixture.verdicts:
        if verdict.evidence:
            topics.append(verdict)
    return topics


def topic_ids_with_evidence(
    topics: list[TrueVerdict],
) -> list[str]:
    topic_ids = []
    for verdict in topics:
        topic_ids.append(verdict.topic_id)
    return topic_ids


def _topic_has_matched_requirement(
    topic_id: str,
    group_by_topic: dict[str, MatchGroup],
) -> bool:
    group = group_by_topic.get(topic_id)
    if group is None:
        return False
    return len(group.predicted_node_ids) > 0


def topics_with_matched_requirement(
    topics: list[TrueVerdict],
    group_by_topic: dict[str, MatchGroup],
) -> list[TrueVerdict]:
    matched = []
    for verdict in topics:
        if _topic_has_matched_requirement(verdict.topic_id, group_by_topic):
            matched.append(verdict)
    return matched


def matched_evidence_topic_ids(
    topics: list[TrueVerdict],
    group_by_topic: dict[str, MatchGroup],
    by_requirement: dict[str, list[Chunk]],
) -> set[str]:
    matched = set()
    for verdict in topics:
        if _has_evidence_overlap(verdict, group_by_topic, by_requirement):
            matched.add(verdict.topic_id)
    return matched
