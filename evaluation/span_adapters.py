from config import (
    EVALUATION_EVIDENCE_MATCH_MINIMUM_OVERLAP_RATIO,
    EVALUATION_EXCLUDED_CLAUSE_MINIMUM_OVERLAP_RATIO,
    EVALUATION_REQUIREMENT_MATCH_MINIMUM_OVERLAP_RATIO,
)
from evaluation.fixtures import (
    ExpectedRequirementsFixture,
    ExpectedSource,
    ExpectedVerdict,
    ExpectedVerdictsFixture,
)
from evaluation.matching import (
    MatchGroup,
    SpanRef,
    build_match_groups,
    find_overlapping_pairs,
)
from schemas import Chunk, Requirement, RetrievedEvidenceRecord, TextSpan


def _span_from_source(node_id: str, source: ExpectedSource) -> SpanRef:
    return SpanRef(
        node_id=node_id,
        document_path=source.document_path,
        start_char=source.start_char,
        end_char=source.end_char,
    )


def expected_requirement_spans(
    fixture: ExpectedRequirementsFixture,
) -> list[SpanRef]:
    spans = []
    for requirement in fixture.requirements:
        spans.append(
            _span_from_source(requirement.topic_id, requirement.source)
        )
    return spans


def excluded_clause_spans(
    fixture: ExpectedRequirementsFixture,
) -> list[SpanRef]:
    spans = []
    for clause in fixture.excluded_clauses:
        spans.append(_span_from_source(clause.clause_id, clause.source))
    return spans


def actual_requirement_spans(
    requirements: list[Requirement],
) -> list[SpanRef]:
    spans = []
    for requirement in requirements:
        for citation in requirement.citations:
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


def excluded_overlap_requirement_ids(
    excluded_spans: list[SpanRef],
    actual_spans: list[SpanRef],
) -> set[str]:
    edges = find_overlapping_pairs(
        excluded_spans, actual_spans,
        EVALUATION_EXCLUDED_CLAUSE_MINIMUM_OVERLAP_RATIO,
    )
    overlap_ids = set()
    for edge in edges:
        overlap_ids.add(edge.actual_node_id)
    return overlap_ids


def span_length(span: ExpectedSource) -> int:
    return span.end_char - span.start_char


def _citation_length(citation: TextSpan) -> int:
    if citation.start_char is None or citation.end_char is None:
        return 0
    return citation.end_char - citation.start_char


def citation_total_length(requirement: Requirement) -> int:
    total = 0
    for citation in requirement.citations:
        total += _citation_length(citation)
    return total


def _topic_ids_of_requirements(
    fixture: ExpectedRequirementsFixture,
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
    fixture: ExpectedRequirementsFixture,
    actual_requirements: list[Requirement],
) -> list[MatchGroup]:
    expected_spans = expected_requirement_spans(fixture)
    actual_spans = actual_requirement_spans(actual_requirements)
    edges = find_overlapping_pairs(
        expected_spans, actual_spans,
        EVALUATION_REQUIREMENT_MATCH_MINIMUM_OVERLAP_RATIO,
    )
    expected_topic_ids = _topic_ids_of_requirements(fixture)
    actual_requirement_ids = _requirement_ids_of(actual_requirements)
    return build_match_groups(
        expected_topic_ids, actual_requirement_ids, edges
    )


def group_lookup_by_topic(
    groups: list[MatchGroup],
) -> dict[str, MatchGroup]:
    lookup = {}
    for group in groups:
        for topic_id in group.expected_topic_ids:
            lookup[topic_id] = group
    return lookup


def _retrieved_spans_for_group(
    group: MatchGroup,
    retrieved_by_requirement: dict[str, list[Chunk]],
) -> list[SpanRef]:
    spans = []
    for requirement_id in group.actual_node_ids:
        for chunk in retrieved_by_requirement.get(requirement_id, []):
            spans.append(SpanRef(
                node_id=requirement_id,
                document_path=chunk.document_path,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
            ))
    return spans


def _expected_evidence_spans(verdict: ExpectedVerdict) -> list[SpanRef]:
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
    verdict: ExpectedVerdict,
    group_by_topic: dict[str, MatchGroup],
    retrieved_by_requirement: dict[str, list[Chunk]],
) -> bool:
    group = group_by_topic.get(verdict.topic_id)
    if group is None:
        return False
    retrieved_spans = _retrieved_spans_for_group(
        group, retrieved_by_requirement
    )
    expected_spans = _expected_evidence_spans(verdict)
    edges = find_overlapping_pairs(
        expected_spans, retrieved_spans,
        EVALUATION_EVIDENCE_MATCH_MINIMUM_OVERLAP_RATIO,
    )
    return len(edges) > 0


def retrieved_by_requirement(
    retrieved_evidence: list[RetrievedEvidenceRecord],
) -> dict[str, list[Chunk]]:
    by_requirement = {}
    for record in retrieved_evidence:
        by_requirement[record.requirement_id] = record.evidence_chunks
    return by_requirement


def topics_with_evidence(
    fixture: ExpectedVerdictsFixture,
) -> list[ExpectedVerdict]:
    topics = []
    for verdict in fixture.verdicts:
        if verdict.evidence:
            topics.append(verdict)
    return topics


def topic_ids_with_evidence(
    topics: list[ExpectedVerdict],
) -> list[str]:
    topic_ids = []
    for verdict in topics:
        topic_ids.append(verdict.topic_id)
    return topic_ids


def matched_evidence_topic_ids(
    topics: list[ExpectedVerdict],
    group_by_topic: dict[str, MatchGroup],
    by_requirement: dict[str, list[Chunk]],
) -> set[str]:
    matched = set()
    for verdict in topics:
        if _has_evidence_overlap(verdict, group_by_topic, by_requirement):
            matched.add(verdict.topic_id)
    return matched
