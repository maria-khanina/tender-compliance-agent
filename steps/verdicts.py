from pydantic import BaseModel

from backends.llm_client import get_structured_chat_model, invoke_structured
from logging_config import get_logger
from prompts import VERDICT_CONDITION_SECTION, VERDICT_GENERATION_PROMPT
from schemas import (
    Chunk,
    ConditionSpec,
    Evidence,
    EvidenceRole,
    ExtractedValue,
    Requirement,
    Verdict,
    VerdictLabel,
)
from steps.conditions import apply_operator, compare_conditions
from steps.text_matching import (
    find_chunk_by_index,
    format_chunks_as_prompt_text,
    locate_quote_in_chunk,
)
from steps.value_extraction import extract_values


class EvidenceQuote(BaseModel):
    chunk_index: int
    quote: str
    role: EvidenceRole


class VerdictResult(BaseModel):
    condition_holds: bool
    verdict: VerdictLabel
    evidence_quotes: list[EvidenceQuote]
    reasoning: str


logger = get_logger(__name__)


def _build_evidence_list(
    context_chunks: list[Chunk],
    evidence_quotes: list[EvidenceQuote],
) -> list[Evidence]:
    evidence_list = []
    for evidence_quote in evidence_quotes:
        source_chunk = find_chunk_by_index(
            context_chunks, evidence_quote.chunk_index
        )
        if source_chunk is None:
            logger.warning(
                "Language model referenced unknown chunk_index %d "
                "while building evidence",
                evidence_quote.chunk_index,
            )
            continue
        text_span = locate_quote_in_chunk(
            source_chunk, evidence_quote.quote
        )
        evidence_list.append(
            Evidence(
                document_path=text_span.document_path,
                quote=text_span.quote,
                start_char=text_span.start_char,
                end_char=text_span.end_char,
                citation_verified=text_span.citation_verified,
                role=evidence_quote.role,
            )
        )
    return evidence_list


def _build_condition_section(requirement: Requirement) -> str:
    condition_citation = requirement.applicability_condition_citation
    if condition_citation is None:
        return ""
    return "\n" + VERDICT_CONDITION_SECTION.format(
        condition_text=condition_citation.quote
    )


def _generate_verdict_with_language_model(
    requirement: Requirement,
    context_chunks: list[Chunk],
) -> Verdict:
    context_text = format_chunks_as_prompt_text(context_chunks)
    prompt_text = VERDICT_GENERATION_PROMPT.format(
        requirement_text=requirement.text,
        condition_section=_build_condition_section(requirement),
        context_text=context_text,
    )
    structured_model = get_structured_chat_model(VerdictResult)
    result = invoke_structured(structured_model, prompt_text)
    evidence_list = _build_evidence_list(
        context_chunks, result.evidence_quotes
    )
    if requirement.applicability_condition_citation is None:
        condition_holds = True
    else:
        condition_holds = result.condition_holds
    return Verdict(
        requirement_id=requirement.requirement_id,
        requirement_text=requirement.text,
        verdict=result.verdict,
        evidence=evidence_list,
        reasoning=result.reasoning,
        condition_holds=condition_holds,
    )


def _build_deterministic_evidence(
    extracted_values: list[ExtractedValue],
    condition: ConditionSpec,
) -> list[Evidence]:
    evidence_list = []
    for extracted_value in extracted_values:
        individual_label = apply_operator(
            condition.operator, extracted_value.value, condition.value
        )
        if individual_label == VerdictLabel.COMPLIANT:
            evidence_role = EvidenceRole.SUPPORTS
        else:
            evidence_role = EvidenceRole.CONTRADICTS
        source = extracted_value.source
        evidence_list.append(
            Evidence(
                document_path=source.document_path,
                quote=source.quote,
                start_char=source.start_char,
                end_char=source.end_char,
                citation_verified=source.citation_verified,
                role=evidence_role,
            )
        )
    return evidence_list


def _build_deterministic_reasoning(
    condition: ConditionSpec,
    extracted_values: list[ExtractedValue],
) -> str:
    extracted_value_numbers = []
    for extracted_value in extracted_values:
        extracted_value_numbers.append(str(extracted_value.value))
    values_text = ", ".join(extracted_value_numbers)
    return (
        f"Extracted value(s) for '{condition.field_name}': "
        f"{values_text}. Required {condition.operator} "
        f"{condition.value}."
    )


def _extracted_values_by_condition(
    conditions: list[ConditionSpec],
    context_chunks: list[Chunk],
) -> list[tuple[ConditionSpec, list[ExtractedValue]]]:
    results = []
    for condition in conditions:
        results.append((condition, extract_values(context_chunks, condition)))
    return results


def _flatten_extracted_values(
    extracted_values_by_condition: (
        list[tuple[ConditionSpec, list[ExtractedValue]]]
    ),
) -> list[ExtractedValue]:
    all_values = []
    for _, condition_values in extracted_values_by_condition:
        all_values.extend(condition_values)
    return all_values


def _build_deterministic_verdict_parts(
    extracted_values_by_condition: (
        list[tuple[ConditionSpec, list[ExtractedValue]]]
    ),
) -> tuple[list[Evidence], str]:
    evidence_list = []
    reasoning_parts = []
    for condition, extracted_values in extracted_values_by_condition:
        if not extracted_values:
            continue
        evidence_list.extend(
            _build_deterministic_evidence(extracted_values, condition)
        )
        reasoning_parts.append(
            _build_deterministic_reasoning(condition, extracted_values)
        )
    reasoning = " ".join(reasoning_parts)
    return evidence_list, reasoning


def _generate_verdict_deterministically(
    requirement: Requirement,
    context_chunks: list[Chunk],
) -> Verdict | None:
    conditions = requirement.conditions
    if not conditions:
        return None
    extracted_values_by_condition = _extracted_values_by_condition(
        conditions, context_chunks
    )
    all_extracted_values = _flatten_extracted_values(
        extracted_values_by_condition
    )
    verdict_label = compare_conditions(conditions, all_extracted_values)
    if verdict_label is None:
        return None
    evidence_list, reasoning = _build_deterministic_verdict_parts(
        extracted_values_by_condition
    )
    return Verdict(
        requirement_id=requirement.requirement_id,
        requirement_text=requirement.text,
        verdict=verdict_label,
        evidence=evidence_list,
        reasoning=reasoning,
        condition_holds=requirement.applicability_condition_citation is None,
    )


def generate_verdict(
    requirement: Requirement,
    context_chunks: list[Chunk],
) -> Verdict:
    deterministic_verdict = _generate_verdict_deterministically(
        requirement, context_chunks
    )
    if deterministic_verdict is not None:
        logger.info(
            "Requirement %s: verdict=%s (deterministic)",
            requirement.requirement_id,
            deterministic_verdict.verdict.value,
        )
        return deterministic_verdict
    verdict = _generate_verdict_with_language_model(
        requirement, context_chunks
    )
    logger.info(
        "Requirement %s: verdict=%s (language model)",
        requirement.requirement_id,
        verdict.verdict.value,
    )
    return verdict
