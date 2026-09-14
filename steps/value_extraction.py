from pydantic import BaseModel

from backends.llm_client import get_structured_chat_model, invoke_structured
from logging_config import get_logger
from prompts import VALUE_EXTRACTION_PROMPT
from schemas import Chunk, ConditionSpec, ExtractedValue
from steps.text_matching import (
    find_chunk_by_index,
    format_chunks_as_prompt_text,
    locate_quote_in_chunk,
)


class ExtractedValueCandidate(BaseModel):
    quote: str
    chunk_index: int
    value: float


class ExtractedValueCandidateList(BaseModel):
    candidates: list[ExtractedValueCandidate]


logger = get_logger(__name__)


def _extract_value_from_candidate(
    context_chunks: list[Chunk],
    candidate: ExtractedValueCandidate,
    condition: ConditionSpec,
) -> ExtractedValue | None:
    source_chunk = find_chunk_by_index(
        context_chunks, candidate.chunk_index
    )
    if source_chunk is None:
        logger.warning(
            "Language model referenced unknown chunk_index %d "
            "while extracting values for field %s",
            candidate.chunk_index,
            condition.field_name,
        )
        return None
    source_span = locate_quote_in_chunk(source_chunk, candidate.quote)
    return ExtractedValue(
        value_type=condition.condition_type,
        field_name=condition.field_name,
        value=candidate.value,
        unit=condition.unit,
        source=source_span,
    )


def _extract_values_from_candidates(
    context_chunks: list[Chunk],
    candidates: list[ExtractedValueCandidate],
    condition: ConditionSpec,
) -> list[ExtractedValue]:
    extracted_values = []
    for candidate in candidates:
        value = _extract_value_from_candidate(
            context_chunks, candidate, condition
        )
        if value is not None:
            extracted_values.append(value)
    return extracted_values


def extract_values(
    context_chunks: list[Chunk],
    condition: ConditionSpec,
) -> list[ExtractedValue]:
    context_text = format_chunks_as_prompt_text(context_chunks)
    prompt_text = VALUE_EXTRACTION_PROMPT.format(
        field_name=condition.field_name,
        unit=condition.unit,
        context_text=context_text,
    )
    structured_model = get_structured_chat_model(
        ExtractedValueCandidateList
    )
    result = invoke_structured(structured_model, prompt_text)
    extracted_values = _extract_values_from_candidates(
        context_chunks, result.candidates, condition
    )
    logger.info(
        "Extracted %d value(s) for field %s from %d context chunk(s)",
        len(extracted_values),
        condition.field_name,
        len(context_chunks),
    )
    return extracted_values
