import json
import pathlib

from pydantic import BaseModel

from config import (
    EVALUATION_COVERAGE_FLAG_THRESHOLD,
    EVALUATION_EVIDENCE_MATCH_MINIMUM_OVERLAP_RATIO,
    EVALUATION_EXCLUDED_CLAUSE_MINIMUM_OVERLAP_RATIO,
    EVALUATION_REQUIREMENT_MATCH_MINIMUM_OVERLAP_RATIO,
)
from evaluation.matching import (
    MatchGroup,
    SpanRef,
    build_match_groups,
    find_overlapping_pairs,
)
from evaluation.metrics import (
    CoverageFlag,
    EvidenceRecallResult,
    EvidenceResult,
    IsMandatoryResult,
    PrecisionResult,
    RecallResult,
    VerdictAccuracyResult,
    compute_coverage_flags,
    compute_evidence_citation_verified_rate,
    compute_evidence_recall,
    compute_is_mandatory_accuracy,
    compute_precision,
    compute_requirement_recall,
    compute_verdict_accuracy,
)
from schemas import (
    Chunk,
    Requirement,
    RetrievedEvidenceRecord,
    TextSpan,
    Verdict,
)


class ExpectedSource(BaseModel):
    document_path: str
    quote: str
    start_char: int
    end_char: int


class ExpectedRequirement(BaseModel):
    topic_id: str
    description: str
    is_mandatory: bool
    source: ExpectedSource


class ExcludedClause(BaseModel):
    clause_id: str
    description: str
    source: ExpectedSource


class ExpectedRequirementsFixture(BaseModel):
    notes: list[str]
    requirements: list[ExpectedRequirement]
    excluded_clauses: list[ExcludedClause]


class ExpectedEvidenceSpan(BaseModel):
    document_path: str
    quote: str
    start_char: int
    end_char: int


class ExpectedVerdict(BaseModel):
    topic_id: str
    acceptable_verdicts: list[str] | None
    rationale: str
    evidence: list[ExpectedEvidenceSpan]


class ExpectedVerdictsFixture(BaseModel):
    notes: list[str]
    verdicts: list[ExpectedVerdict]


class EvaluationReport(BaseModel):
    requirement_recall: RecallResult
    requirement_precision: PrecisionResult
    coverage_flags: list[CoverageFlag]
    is_mandatory_accuracy: IsMandatoryResult
    verdict_accuracy: VerdictAccuracyResult
    evidence_citation_verified: EvidenceResult
    evidence_recall: EvidenceRecallResult


def _load_json(path: pathlib.Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_expected_requirements(
    path: pathlib.Path,
) -> ExpectedRequirementsFixture:
    return ExpectedRequirementsFixture.model_validate(_load_json(path))


def load_expected_verdicts(path: pathlib.Path) -> ExpectedVerdictsFixture:
    return ExpectedVerdictsFixture.model_validate(_load_json(path))


def load_actual_requirements(path: pathlib.Path) -> list[Requirement]:
    payload = _load_json(path)
    assert isinstance(payload, list)
    return [Requirement.model_validate(item) for item in payload]


def load_actual_verdicts(path: pathlib.Path) -> list[Verdict]:
    payload = _load_json(path)
    assert isinstance(payload, list)
    return [Verdict.model_validate(item) for item in payload]


def load_retrieved_evidence(
    path: pathlib.Path,
) -> list[RetrievedEvidenceRecord]:
    payload = _load_json(path)
    assert isinstance(payload, list)
    return [RetrievedEvidenceRecord.model_validate(item) for item in payload]


def _span_from_source(node_id: str, source: ExpectedSource) -> SpanRef:
    return SpanRef(
        node_id=node_id,
        document_path=source.document_path,
        start_char=source.start_char,
        end_char=source.end_char,
    )


def _expected_requirement_spans(
    fixture: ExpectedRequirementsFixture,
) -> list[SpanRef]:
    spans = []
    for requirement in fixture.requirements:
        spans.append(_span_from_source(requirement.topic_id, requirement.source))
    return spans


def _excluded_clause_spans(
    fixture: ExpectedRequirementsFixture,
) -> list[SpanRef]:
    spans = []
    for clause in fixture.excluded_clauses:
        spans.append(_span_from_source(clause.clause_id, clause.source))
    return spans


def _actual_requirement_spans(
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


def _citation_verified_by_requirement(
    requirements: list[Requirement],
) -> dict[str, bool]:
    verified_by_requirement = {}
    for requirement in requirements:
        verified_by_requirement[requirement.requirement_id] = (
            _all_citations_verified(requirement)
        )
    return verified_by_requirement


def _excluded_overlap_requirement_ids(
    excluded_spans: list[SpanRef],
    actual_spans: list[SpanRef],
) -> set[str]:
    edges = find_overlapping_pairs(
        excluded_spans, actual_spans, EVALUATION_EXCLUDED_CLAUSE_MINIMUM_OVERLAP_RATIO
    )
    overlap_ids = set()
    for edge in edges:
        overlap_ids.add(edge.actual_node_id)
    return overlap_ids


def _span_length(span: ExpectedSource) -> int:
    return span.end_char - span.start_char


def _citation_length(citation: TextSpan) -> int:
    if citation.start_char is None or citation.end_char is None:
        return 0
    return citation.end_char - citation.start_char


def _citation_total_length(requirement: Requirement) -> int:
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


def _build_match_groups_for_requirements(
    fixture: ExpectedRequirementsFixture,
    actual_requirements: list[Requirement],
) -> list[MatchGroup]:
    expected_spans = _expected_requirement_spans(fixture)
    actual_spans = _actual_requirement_spans(actual_requirements)
    edges = find_overlapping_pairs(
        expected_spans, actual_spans, EVALUATION_REQUIREMENT_MATCH_MINIMUM_OVERLAP_RATIO
    )
    expected_topic_ids = _topic_ids_of_requirements(fixture)
    actual_requirement_ids = _requirement_ids_of(actual_requirements)
    return build_match_groups(
        expected_topic_ids, actual_requirement_ids, edges
    )


def _group_lookup_by_topic(
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
        expected_spans, retrieved_spans, EVALUATION_EVIDENCE_MATCH_MINIMUM_OVERLAP_RATIO
    )
    return len(edges) > 0


def _retrieved_by_requirement(
    retrieved_evidence: list[RetrievedEvidenceRecord],
) -> dict[str, list[Chunk]]:
    by_requirement = {}
    for record in retrieved_evidence:
        by_requirement[record.requirement_id] = record.evidence_chunks
    return by_requirement


def _topics_with_evidence(
    fixture: ExpectedVerdictsFixture,
) -> list[ExpectedVerdict]:
    topics = []
    for verdict in fixture.verdicts:
        if verdict.evidence:
            topics.append(verdict)
    return topics


def _topic_ids_with_evidence(
    topics_with_evidence: list[ExpectedVerdict],
) -> list[str]:
    topic_ids = []
    for verdict in topics_with_evidence:
        topic_ids.append(verdict.topic_id)
    return topic_ids


def _matched_evidence_topic_ids(
    topics_with_evidence: list[ExpectedVerdict],
    group_by_topic: dict[str, MatchGroup],
    retrieved_by_requirement: dict[str, list[Chunk]],
) -> set[str]:
    matched = set()
    for verdict in topics_with_evidence:
        if _has_evidence_overlap(
            verdict, group_by_topic, retrieved_by_requirement
        ):
            matched.add(verdict.topic_id)
    return matched


def _evaluate_evidence_recall(
    verdicts_fixture: ExpectedVerdictsFixture,
    match_groups: list[MatchGroup],
    retrieved_evidence: list[RetrievedEvidenceRecord],
) -> EvidenceRecallResult:
    retrieved_by_requirement = _retrieved_by_requirement(retrieved_evidence)
    group_by_topic = _group_lookup_by_topic(match_groups)
    topics_with_evidence = _topics_with_evidence(verdicts_fixture)
    topic_ids = _topic_ids_with_evidence(topics_with_evidence)
    matched_topic_ids = _matched_evidence_topic_ids(
        topics_with_evidence, group_by_topic, retrieved_by_requirement
    )
    return compute_evidence_recall(topic_ids, matched_topic_ids)


def _expected_lengths_by_topic(
    fixture: ExpectedRequirementsFixture,
) -> dict[str, int]:
    lengths = {}
    for requirement in fixture.requirements:
        lengths[requirement.topic_id] = _span_length(requirement.source)
    return lengths


def _actual_lengths_by_requirement(
    requirements: list[Requirement],
) -> dict[str, int]:
    lengths = {}
    for requirement in requirements:
        lengths[requirement.requirement_id] = _citation_total_length(
            requirement
        )
    return lengths


def _compute_precision_result(
    requirements_fixture: ExpectedRequirementsFixture,
    actual_requirements: list[Requirement],
    match_groups: list[MatchGroup],
) -> PrecisionResult:
    excluded_spans = _excluded_clause_spans(requirements_fixture)
    actual_spans = _actual_requirement_spans(actual_requirements)
    excluded_overlap_ids = _excluded_overlap_requirement_ids(
        excluded_spans, actual_spans
    )
    citation_verified_by_requirement = _citation_verified_by_requirement(
        actual_requirements
    )
    return compute_precision(
        match_groups, citation_verified_by_requirement, excluded_overlap_ids
    )


def _compute_coverage_flags_result(
    requirements_fixture: ExpectedRequirementsFixture,
    actual_requirements: list[Requirement],
    match_groups: list[MatchGroup],
) -> list[CoverageFlag]:
    expected_spans = _expected_requirement_spans(requirements_fixture)
    actual_spans = _actual_requirement_spans(actual_requirements)
    edges = find_overlapping_pairs(
        expected_spans, actual_spans, EVALUATION_REQUIREMENT_MATCH_MINIMUM_OVERLAP_RATIO
    )
    expected_lengths = _expected_lengths_by_topic(requirements_fixture)
    actual_lengths = _actual_lengths_by_requirement(actual_requirements)
    return compute_coverage_flags(
        match_groups, edges, expected_lengths, actual_lengths,
        EVALUATION_COVERAGE_FLAG_THRESHOLD,
    )


def _expected_is_mandatory_by_topic(
    fixture: ExpectedRequirementsFixture,
) -> dict[str, bool]:
    flags = {}
    for requirement in fixture.requirements:
        flags[requirement.topic_id] = requirement.is_mandatory
    return flags


def _actual_is_mandatory_by_requirement(
    requirements: list[Requirement],
) -> dict[str, bool]:
    flags = {}
    for requirement in requirements:
        flags[requirement.requirement_id] = requirement.is_mandatory
    return flags


def _compute_is_mandatory_result(
    requirements_fixture: ExpectedRequirementsFixture,
    actual_requirements: list[Requirement],
    match_groups: list[MatchGroup],
) -> IsMandatoryResult:
    expected_is_mandatory = _expected_is_mandatory_by_topic(
        requirements_fixture
    )
    actual_is_mandatory = _actual_is_mandatory_by_requirement(
        actual_requirements
    )
    return compute_is_mandatory_accuracy(
        match_groups, expected_is_mandatory, actual_is_mandatory
    )


def _acceptable_verdicts_by_topic(
    fixture: ExpectedVerdictsFixture,
) -> dict[str, list[str] | None]:
    acceptable = {}
    for verdict in fixture.verdicts:
        acceptable[verdict.topic_id] = verdict.acceptable_verdicts
    return acceptable


def _actual_verdict_by_requirement(
    verdicts: list[Verdict],
) -> dict[str, str]:
    verdict_by_requirement = {}
    for verdict in verdicts:
        verdict_by_requirement[verdict.requirement_id] = (
            verdict.verdict.value
        )
    return verdict_by_requirement


def _compute_verdict_accuracy_result(
    verdicts_fixture: ExpectedVerdictsFixture,
    actual_verdicts: list[Verdict],
    match_groups: list[MatchGroup],
) -> VerdictAccuracyResult:
    acceptable = _acceptable_verdicts_by_topic(verdicts_fixture)
    actual_by_requirement = _actual_verdict_by_requirement(actual_verdicts)
    return compute_verdict_accuracy(
        match_groups, acceptable, actual_by_requirement
    )


def _all_evidence_verified_flags(verdicts: list[Verdict]) -> list[bool]:
    flags = []
    for verdict in verdicts:
        for evidence in verdict.evidence:
            flags.append(evidence.citation_verified)
    return flags


def _compute_evidence_citation_verified_result(
    actual_verdicts: list[Verdict],
) -> EvidenceResult:
    flags = _all_evidence_verified_flags(actual_verdicts)
    return compute_evidence_citation_verified_rate(flags)


def evaluate(
    requirements_fixture: ExpectedRequirementsFixture,
    verdicts_fixture: ExpectedVerdictsFixture,
    actual_requirements: list[Requirement],
    actual_verdicts: list[Verdict],
    retrieved_evidence: list[RetrievedEvidenceRecord],
) -> EvaluationReport:
    match_groups = _build_match_groups_for_requirements(
        requirements_fixture, actual_requirements
    )
    recall_result = compute_requirement_recall(match_groups)
    precision_result = _compute_precision_result(
        requirements_fixture, actual_requirements, match_groups
    )
    coverage_flags = _compute_coverage_flags_result(
        requirements_fixture, actual_requirements, match_groups
    )
    is_mandatory_result = _compute_is_mandatory_result(
        requirements_fixture, actual_requirements, match_groups
    )
    verdict_accuracy = _compute_verdict_accuracy_result(
        verdicts_fixture, actual_verdicts, match_groups
    )
    evidence_citation_verified = _compute_evidence_citation_verified_result(
        actual_verdicts
    )
    evidence_recall = _evaluate_evidence_recall(
        verdicts_fixture, match_groups, retrieved_evidence
    )
    return EvaluationReport(
        requirement_recall=recall_result,
        requirement_precision=precision_result,
        coverage_flags=coverage_flags,
        is_mandatory_accuracy=is_mandatory_result,
        verdict_accuracy=verdict_accuracy,
        evidence_citation_verified=evidence_citation_verified,
        evidence_recall=evidence_recall,
    )
