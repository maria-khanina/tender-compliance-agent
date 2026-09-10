from pydantic import BaseModel

from config import (
    EVALUATION_COVERAGE_FLAG_THRESHOLD,
    EVALUATION_REQUIREMENT_MATCH_MINIMUM_OVERLAP_RATIO,
)
from evaluation.evidence_metrics import (
    EvidenceRecallResult,
    EvidenceResult,
    compute_evidence_citation_verified_rate,
    compute_evidence_recall,
)
from evaluation.fixtures import (
    ExpectedRequirementsFixture,
    ExpectedVerdictsFixture,
    load_actual_requirements,
    load_actual_verdicts,
    load_expected_requirements,
    load_expected_verdicts,
    load_retrieved_evidence,
)
from evaluation.matching import MatchGroup, find_overlapping_pairs
from evaluation.requirement_metrics import (
    CoverageFlag,
    IsMandatoryResult,
    PrecisionResult,
    RecallResult,
    compute_coverage_flags,
    compute_is_mandatory_accuracy,
    compute_precision,
    compute_requirement_recall,
)
from evaluation.span_adapters import (
    actual_requirement_spans,
    build_match_groups_for_requirements,
    citation_total_length,
    citation_verified_by_requirement,
    excluded_clause_spans,
    excluded_overlap_requirement_ids,
    expected_requirement_spans,
    group_lookup_by_topic,
    matched_evidence_topic_ids,
    retrieved_by_requirement,
    span_length,
    topic_ids_with_evidence,
    topics_with_evidence,
)
from evaluation.verdict_metrics import (
    VerdictAccuracyResult,
    compute_verdict_accuracy,
)
from schemas import Requirement, RetrievedEvidenceRecord, Verdict


__all__ = [
    "EvaluationReport",
    "ExpectedRequirementsFixture",
    "ExpectedVerdictsFixture",
    "evaluate",
    "load_actual_requirements",
    "load_actual_verdicts",
    "load_expected_requirements",
    "load_expected_verdicts",
    "load_retrieved_evidence",
]


class EvaluationReport(BaseModel):
    requirement_recall: RecallResult
    requirement_precision: PrecisionResult
    coverage_flags: list[CoverageFlag]
    is_mandatory_accuracy: IsMandatoryResult
    verdict_accuracy: VerdictAccuracyResult
    evidence_citation_verified: EvidenceResult
    evidence_recall: EvidenceRecallResult
    match_groups: list[MatchGroup]
    expected_descriptions: dict[str, str]
    actual_texts: dict[str, str]
    acceptable_verdicts_by_topic: dict[str, list[str] | None]
    actual_verdict_labels: dict[str, str]
    actual_citation_status: dict[str, str]
    expected_evidence_by_topic: dict[str, list[str]]


def _expected_lengths_by_topic(
    fixture: ExpectedRequirementsFixture,
) -> dict[str, int]:
    lengths = {}
    for requirement in fixture.requirements:
        lengths[requirement.topic_id] = span_length(requirement.source)
    return lengths


def _actual_lengths_by_requirement(
    requirements: list[Requirement],
) -> dict[str, int]:
    lengths = {}
    for requirement in requirements:
        lengths[requirement.requirement_id] = citation_total_length(
            requirement
        )
    return lengths


def _compute_precision_result(
    requirements_fixture: ExpectedRequirementsFixture,
    actual_requirements: list[Requirement],
    match_groups: list[MatchGroup],
) -> PrecisionResult:
    excluded_spans = excluded_clause_spans(requirements_fixture)
    actual_spans = actual_requirement_spans(actual_requirements)
    excluded_overlap_ids = excluded_overlap_requirement_ids(
        excluded_spans, actual_spans
    )
    citation_verified = citation_verified_by_requirement(
        actual_requirements
    )
    return compute_precision(
        match_groups, citation_verified, excluded_overlap_ids
    )


def _compute_coverage_flags_result(
    requirements_fixture: ExpectedRequirementsFixture,
    actual_requirements: list[Requirement],
    match_groups: list[MatchGroup],
) -> list[CoverageFlag]:
    expected_spans = expected_requirement_spans(requirements_fixture)
    actual_spans = actual_requirement_spans(actual_requirements)
    edges = find_overlapping_pairs(
        expected_spans, actual_spans,
        EVALUATION_REQUIREMENT_MATCH_MINIMUM_OVERLAP_RATIO,
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


def _expected_descriptions(
    fixture: ExpectedRequirementsFixture,
) -> dict[str, str]:
    descriptions = {}
    for requirement in fixture.requirements:
        descriptions[requirement.topic_id] = requirement.description
    return descriptions


def _actual_texts(requirements: list[Requirement]) -> dict[str, str]:
    texts = {}
    for requirement in requirements:
        texts[requirement.requirement_id] = requirement.text
    return texts


def _citation_status(requirement: Requirement) -> str:
    statuses = []
    for citation in requirement.citations:
        if not citation.citation_verified:
            statuses.append("unverified")
        elif citation.match_precision == "fuzzy":
            statuses.append("fuzzy")
        else:
            statuses.append("precise")
    if "unverified" in statuses:
        return "unverified"
    if "fuzzy" in statuses:
        return "fuzzy"
    return "precise"


def _actual_citation_status(
    requirements: list[Requirement],
) -> dict[str, str]:
    statuses = {}
    for requirement in requirements:
        statuses[requirement.requirement_id] = _citation_status(requirement)
    return statuses


def _expected_evidence_by_topic(
    fixture: ExpectedVerdictsFixture,
) -> dict[str, list[str]]:
    evidence_by_topic = {}
    for verdict in fixture.verdicts:
        quotes = []
        for evidence in verdict.evidence:
            quotes.append(evidence.quote)
        evidence_by_topic[verdict.topic_id] = quotes
    return evidence_by_topic


def _evaluate_evidence_recall(
    verdicts_fixture: ExpectedVerdictsFixture,
    match_groups: list[MatchGroup],
    retrieved_evidence: list[RetrievedEvidenceRecord],
) -> EvidenceRecallResult:
    by_requirement = retrieved_by_requirement(retrieved_evidence)
    group_by_topic = group_lookup_by_topic(match_groups)
    topics = topics_with_evidence(verdicts_fixture)
    topic_ids = topic_ids_with_evidence(topics)
    matched_topic_ids = matched_evidence_topic_ids(
        topics, group_by_topic, by_requirement
    )
    return compute_evidence_recall(topic_ids, matched_topic_ids)


def evaluate(
    requirements_fixture: ExpectedRequirementsFixture,
    verdicts_fixture: ExpectedVerdictsFixture,
    actual_requirements: list[Requirement],
    actual_verdicts: list[Verdict],
    retrieved_evidence: list[RetrievedEvidenceRecord],
) -> EvaluationReport:
    match_groups = build_match_groups_for_requirements(
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
        match_groups=match_groups,
        expected_descriptions=_expected_descriptions(requirements_fixture),
        actual_texts=_actual_texts(actual_requirements),
        acceptable_verdicts_by_topic=_acceptable_verdicts_by_topic(
            verdicts_fixture
        ),
        actual_verdict_labels=_actual_verdict_by_requirement(actual_verdicts),
        actual_citation_status=_actual_citation_status(actual_requirements),
        expected_evidence_by_topic=_expected_evidence_by_topic(
            verdicts_fixture
        ),
    )
