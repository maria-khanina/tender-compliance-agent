from pydantic import BaseModel

from config import (
    EVALUATION_CONDITION_MATCH_MINIMUM_OVERLAP_RATIO,
    EVALUATION_COVERAGE_FLAG_THRESHOLD,
)
from evaluation.evidence_metrics import (
    EvidenceRecallResult,
    EvidenceResult,
    compute_evidence_citation_verified_rate,
    compute_evidence_recall,
)
from evaluation.fixtures import (
    TrueRequirementsFixture,
    TrueVerdictsFixture,
    load_predicted_requirements,
    load_predicted_verdicts,
    load_retrieved_context,
    load_true_requirements,
    load_true_verdicts,
)
from evaluation.matching import MatchGroup
from evaluation.requirement_metrics import (
    ApplicabilityConditionDetectionResult,
    ConditionHoldsResult,
    CoverageFlag,
    IsMandatoryResult,
    IsTextVerifiableResult,
    PrecisionResult,
    RecallResult,
    compute_applicability_condition_detection,
    compute_condition_holds_accuracy,
    compute_coverage_flags,
    compute_is_mandatory_accuracy,
    compute_is_text_verifiable_accuracy,
    compute_precision,
    compute_requirement_recall,
)
from evaluation.span_adapters import (
    build_match_groups_for_requirements,
    citation_verified_by_requirement,
    group_lookup_by_topic,
    matched_evidence_topic_ids,
    predicted_condition_holds_by_requirement,
    predicted_condition_spans_by_requirement,
    predicted_requirement_spans,
    retrieved_by_requirement,
    topic_ids_with_evidence,
    topics_with_evidence,
    topics_with_matched_requirement,
    true_condition_holds_by_topic,
    true_condition_spans_by_topic,
    true_requirement_spans,
)
from evaluation.verdict_metrics import (
    VerdictAccuracyResult,
    compute_verdict_accuracy,
)
from schemas import Requirement, RetrievedContextRecord, Verdict


__all__ = [
    "EvaluationReport",
    "TrueRequirementsFixture",
    "TrueVerdictsFixture",
    "evaluate",
    "load_predicted_requirements",
    "load_predicted_verdicts",
    "load_retrieved_context",
    "load_true_requirements",
    "load_true_verdicts",
]


class EvaluationReport(BaseModel):
    requirement_recall: RecallResult
    requirement_precision: PrecisionResult
    coverage_flags: list[CoverageFlag]
    is_mandatory_accuracy: IsMandatoryResult
    is_text_verifiable_accuracy: IsTextVerifiableResult
    applicability_condition_detection: ApplicabilityConditionDetectionResult
    condition_holds_accuracy: ConditionHoldsResult
    verdict_accuracy: VerdictAccuracyResult
    evidence_citation_verified: EvidenceResult
    evidence_recall: EvidenceRecallResult
    match_groups: list[MatchGroup]
    true_quotes_by_topic: dict[str, str]
    predicted_texts: dict[str, str]
    acceptable_verdicts_by_topic: dict[str, list[str] | None]
    predicted_verdict_labels: dict[str, str]
    predicted_verdict_reasoning: dict[str, str]
    predicted_verdict_evidence: dict[str, list[str]]
    predicted_citation_status: dict[str, str]
    true_evidence_by_topic: dict[str, list[str]]
    true_verdict_rationale_by_topic: dict[str, str]
    retrieved_context_by_requirement: dict[str, list[str]]
    is_mandatory_true_by_topic: dict[str, bool]
    is_mandatory_predicted_by_requirement: dict[str, bool]
    is_text_verifiable_true_by_topic: dict[str, bool]
    is_text_verifiable_predicted_by_requirement: dict[str, bool]
    condition_holds_true_by_topic: dict[str, bool]
    condition_holds_predicted_by_requirement: dict[str, bool]


def _compute_precision_result(
    predicted_requirements: list[Requirement],
    match_groups: list[MatchGroup],
) -> PrecisionResult:
    citation_verified = citation_verified_by_requirement(
        predicted_requirements
    )
    return compute_precision(match_groups, citation_verified)


def _compute_coverage_flags_result(
    requirements_fixture: TrueRequirementsFixture,
    predicted_requirements: list[Requirement],
    match_groups: list[MatchGroup],
) -> list[CoverageFlag]:
    true_spans = true_requirement_spans(requirements_fixture)
    predicted_spans = predicted_requirement_spans(predicted_requirements)
    return compute_coverage_flags(
        match_groups, true_spans, predicted_spans,
        EVALUATION_COVERAGE_FLAG_THRESHOLD,
    )


def _true_is_mandatory_by_topic(
    fixture: TrueRequirementsFixture,
) -> dict[str, bool]:
    flags = {}
    for requirement in fixture.requirements:
        flags[requirement.topic_id] = requirement.is_mandatory
    return flags


def _predicted_is_mandatory_by_requirement(
    requirements: list[Requirement],
) -> dict[str, bool]:
    flags = {}
    for requirement in requirements:
        flags[requirement.requirement_id] = requirement.is_mandatory
    return flags


def _compute_is_mandatory_result(
    requirements_fixture: TrueRequirementsFixture,
    predicted_requirements: list[Requirement],
    match_groups: list[MatchGroup],
) -> IsMandatoryResult:
    true_is_mandatory = _true_is_mandatory_by_topic(requirements_fixture)
    predicted_is_mandatory = _predicted_is_mandatory_by_requirement(
        predicted_requirements
    )
    return compute_is_mandatory_accuracy(
        match_groups, true_is_mandatory, predicted_is_mandatory
    )


def _true_is_text_verifiable_by_topic(
    fixture: TrueRequirementsFixture,
) -> dict[str, bool]:
    flags = {}
    for requirement in fixture.requirements:
        flags[requirement.topic_id] = requirement.is_text_verifiable
    return flags


def _predicted_is_text_verifiable_by_requirement(
    requirements: list[Requirement],
) -> dict[str, bool]:
    flags = {}
    for requirement in requirements:
        flags[requirement.requirement_id] = requirement.is_text_verifiable
    return flags


def _compute_is_text_verifiable_result(
    requirements_fixture: TrueRequirementsFixture,
    predicted_requirements: list[Requirement],
    match_groups: list[MatchGroup],
) -> IsTextVerifiableResult:
    true_is_text_verifiable = _true_is_text_verifiable_by_topic(
        requirements_fixture
    )
    predicted_is_text_verifiable = _predicted_is_text_verifiable_by_requirement(
        predicted_requirements
    )
    return compute_is_text_verifiable_accuracy(
        match_groups, true_is_text_verifiable, predicted_is_text_verifiable
    )


def _compute_applicability_condition_detection_result(
    requirements_fixture: TrueRequirementsFixture,
    predicted_requirements: list[Requirement],
    match_groups: list[MatchGroup],
) -> ApplicabilityConditionDetectionResult:
    true_spans = true_condition_spans_by_topic(requirements_fixture)
    predicted_spans = predicted_condition_spans_by_requirement(
        predicted_requirements
    )
    return compute_applicability_condition_detection(
        match_groups, true_spans, predicted_spans,
        EVALUATION_CONDITION_MATCH_MINIMUM_OVERLAP_RATIO,
    )


def _compute_condition_holds_result(
    verdicts_fixture: TrueVerdictsFixture,
    predicted_verdicts: list[Verdict],
    match_groups: list[MatchGroup],
) -> ConditionHoldsResult:
    true_condition_holds = true_condition_holds_by_topic(verdicts_fixture)
    predicted_condition_holds = predicted_condition_holds_by_requirement(
        predicted_verdicts
    )
    return compute_condition_holds_accuracy(
        match_groups, true_condition_holds, predicted_condition_holds
    )


def _acceptable_verdicts_by_topic(
    fixture: TrueVerdictsFixture,
) -> dict[str, list[str] | None]:
    acceptable = {}
    for verdict in fixture.verdicts:
        acceptable[verdict.topic_id] = verdict.acceptable_verdicts
    return acceptable


def _predicted_verdict_by_requirement(
    verdicts: list[Verdict],
) -> dict[str, str]:
    verdict_by_requirement = {}
    for verdict in verdicts:
        verdict_by_requirement[verdict.requirement_id] = (
            verdict.verdict.value
        )
    return verdict_by_requirement


def _compute_verdict_accuracy_result(
    verdicts_fixture: TrueVerdictsFixture,
    predicted_verdicts: list[Verdict],
    match_groups: list[MatchGroup],
) -> VerdictAccuracyResult:
    acceptable = _acceptable_verdicts_by_topic(verdicts_fixture)
    predicted_by_requirement = _predicted_verdict_by_requirement(
        predicted_verdicts
    )
    true_condition_holds = true_condition_holds_by_topic(verdicts_fixture)
    return compute_verdict_accuracy(
        match_groups, acceptable, predicted_by_requirement,
        true_condition_holds,
    )


def _all_evidence_verified_flags(verdicts: list[Verdict]) -> list[bool]:
    flags = []
    for verdict in verdicts:
        for evidence in verdict.evidence:
            flags.append(evidence.citation_verified)
    return flags


def _compute_evidence_citation_verified_result(
    predicted_verdicts: list[Verdict],
) -> EvidenceResult:
    flags = _all_evidence_verified_flags(predicted_verdicts)
    return compute_evidence_citation_verified_rate(flags)


def _true_quotes_by_topic(
    fixture: TrueRequirementsFixture,
) -> dict[str, str]:
    quotes = {}
    for requirement in fixture.requirements:
        quotes[requirement.topic_id] = requirement.source.quote
    return quotes


def _predicted_texts(requirements: list[Requirement]) -> dict[str, str]:
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


def _predicted_citation_status(
    requirements: list[Requirement],
) -> dict[str, str]:
    statuses = {}
    for requirement in requirements:
        statuses[requirement.requirement_id] = _citation_status(requirement)
    return statuses


def _predicted_verdict_reasoning(
    verdicts: list[Verdict],
) -> dict[str, str]:
    reasoning = {}
    for verdict in verdicts:
        reasoning[verdict.requirement_id] = verdict.reasoning
    return reasoning


def _predicted_verdict_evidence(
    verdicts: list[Verdict],
) -> dict[str, list[str]]:
    evidence_by_requirement = {}
    for verdict in verdicts:
        quotes = [evidence.quote for evidence in verdict.evidence]
        evidence_by_requirement[verdict.requirement_id] = quotes
    return evidence_by_requirement


def _retrieved_context_by_requirement(
    retrieved_context: list[RetrievedContextRecord],
) -> dict[str, list[str]]:
    by_requirement = retrieved_by_requirement(retrieved_context)
    context = {}
    for requirement_id, chunks in by_requirement.items():
        context[requirement_id] = [chunk.text for chunk in chunks]
    return context


def _true_verdict_rationale_by_topic(
    fixture: TrueVerdictsFixture,
) -> dict[str, str]:
    rationale = {}
    for verdict in fixture.verdicts:
        rationale[verdict.topic_id] = verdict.rationale
    return rationale


def _true_evidence_by_topic(
    fixture: TrueVerdictsFixture,
) -> dict[str, list[str]]:
    evidence_by_topic = {}
    for verdict in fixture.verdicts:
        quotes = []
        for evidence in verdict.evidence:
            quotes.append(evidence.quote)
        evidence_by_topic[verdict.topic_id] = quotes
    return evidence_by_topic


def _evaluate_evidence_recall(
    verdicts_fixture: TrueVerdictsFixture,
    match_groups: list[MatchGroup],
    retrieved_context: list[RetrievedContextRecord],
) -> EvidenceRecallResult:
    by_requirement = retrieved_by_requirement(retrieved_context)
    group_by_topic = group_lookup_by_topic(match_groups)
    topics = topics_with_evidence(verdicts_fixture)
    scorable_topics = topics_with_matched_requirement(topics, group_by_topic)
    topic_ids = topic_ids_with_evidence(scorable_topics)
    matched_topic_ids = matched_evidence_topic_ids(
        scorable_topics, group_by_topic, by_requirement
    )
    return compute_evidence_recall(topic_ids, matched_topic_ids)


def evaluate(
    requirements_fixture: TrueRequirementsFixture,
    verdicts_fixture: TrueVerdictsFixture,
    predicted_requirements: list[Requirement],
    predicted_verdicts: list[Verdict],
    retrieved_context: list[RetrievedContextRecord],
) -> EvaluationReport:
    match_groups = build_match_groups_for_requirements(
        requirements_fixture, predicted_requirements
    )
    recall_result = compute_requirement_recall(match_groups)
    precision_result = _compute_precision_result(
        predicted_requirements, match_groups
    )
    coverage_flags = _compute_coverage_flags_result(
        requirements_fixture, predicted_requirements, match_groups
    )
    is_mandatory_result = _compute_is_mandatory_result(
        requirements_fixture, predicted_requirements, match_groups
    )
    is_text_verifiable_result = _compute_is_text_verifiable_result(
        requirements_fixture, predicted_requirements, match_groups
    )
    condition_detection_result = (
        _compute_applicability_condition_detection_result(
            requirements_fixture, predicted_requirements, match_groups
        )
    )
    condition_holds_result = _compute_condition_holds_result(
        verdicts_fixture, predicted_verdicts, match_groups
    )
    verdict_accuracy = _compute_verdict_accuracy_result(
        verdicts_fixture, predicted_verdicts, match_groups
    )
    evidence_citation_verified = _compute_evidence_citation_verified_result(
        predicted_verdicts
    )
    evidence_recall = _evaluate_evidence_recall(
        verdicts_fixture, match_groups, retrieved_context
    )
    return EvaluationReport(
        requirement_recall=recall_result,
        requirement_precision=precision_result,
        coverage_flags=coverage_flags,
        is_mandatory_accuracy=is_mandatory_result,
        is_text_verifiable_accuracy=is_text_verifiable_result,
        applicability_condition_detection=condition_detection_result,
        condition_holds_accuracy=condition_holds_result,
        verdict_accuracy=verdict_accuracy,
        evidence_citation_verified=evidence_citation_verified,
        evidence_recall=evidence_recall,
        match_groups=match_groups,
        true_quotes_by_topic=_true_quotes_by_topic(requirements_fixture),
        predicted_texts=_predicted_texts(predicted_requirements),
        acceptable_verdicts_by_topic=_acceptable_verdicts_by_topic(
            verdicts_fixture
        ),
        predicted_verdict_labels=_predicted_verdict_by_requirement(
            predicted_verdicts
        ),
        predicted_verdict_reasoning=_predicted_verdict_reasoning(
            predicted_verdicts
        ),
        predicted_verdict_evidence=_predicted_verdict_evidence(
            predicted_verdicts
        ),
        predicted_citation_status=_predicted_citation_status(
            predicted_requirements
        ),
        true_evidence_by_topic=_true_evidence_by_topic(verdicts_fixture),
        true_verdict_rationale_by_topic=_true_verdict_rationale_by_topic(
            verdicts_fixture
        ),
        retrieved_context_by_requirement=_retrieved_context_by_requirement(
            retrieved_context
        ),
        is_mandatory_true_by_topic=_true_is_mandatory_by_topic(
            requirements_fixture
        ),
        is_mandatory_predicted_by_requirement=(
            _predicted_is_mandatory_by_requirement(predicted_requirements)
        ),
        is_text_verifiable_true_by_topic=_true_is_text_verifiable_by_topic(
            requirements_fixture
        ),
        is_text_verifiable_predicted_by_requirement=(
            _predicted_is_text_verifiable_by_requirement(
                predicted_requirements
            )
        ),
        condition_holds_true_by_topic=true_condition_holds_by_topic(
            verdicts_fixture
        ),
        condition_holds_predicted_by_requirement=(
            predicted_condition_holds_by_requirement(predicted_verdicts)
        ),
    )
