import uuid

from pydantic import BaseModel

from backends.llm_client import get_structured_chat_model, invoke_structured
from logging_config import get_logger
from prompts import REQUIREMENT_EXTRACTION_PROMPT
from schemas import Chunk, RequirementDraft, TextSpan
from steps.text_matching import locate_quote_in_chunk


class ExtractedRequirementCandidate(BaseModel):
    lead_in_quote: str | None
    quote: str
    is_mandatory: bool
    is_text_verifiable: bool


class RequirementCandidateList(BaseModel):
    requirements: list[ExtractedRequirementCandidate]


logger = get_logger(__name__)


def _extract_candidates_from_chunk(
    chunk: Chunk,
) -> list[ExtractedRequirementCandidate]:
    structured_model = get_structured_chat_model(RequirementCandidateList)
    prompt_text = REQUIREMENT_EXTRACTION_PROMPT.format(
        chunk_text=chunk.text
    )
    result = invoke_structured(structured_model, prompt_text)
    return result.requirements


def _verified_or_candidate_text(
    citation_quote: str,
    citation_verified: bool,
    candidate_quote: str,
) -> str:
    if citation_verified:
        return citation_quote
    return candidate_quote


def _locate_lead_in_citation(
    chunk: Chunk,
    lead_in_quote: str | None,
) -> tuple[TextSpan, str] | None:
    if not lead_in_quote:
        return None
    citation = locate_quote_in_chunk(chunk, lead_in_quote)
    citation = citation.model_copy(update={"used_for_matching": False})
    text = _verified_or_candidate_text(
        citation.quote, citation.citation_verified, lead_in_quote
    )
    return citation, text


def _build_requirement_draft(
    chunk: Chunk,
    candidate: ExtractedRequirementCandidate,
) -> RequirementDraft:
    main_citation = locate_quote_in_chunk(chunk, candidate.quote)
    main_text = _verified_or_candidate_text(
        main_citation.quote, main_citation.citation_verified, candidate.quote
    )
    lead_in = _locate_lead_in_citation(chunk, candidate.lead_in_quote)
    if lead_in is None:
        citations = [main_citation]
        requirement_text = main_text
    else:
        lead_in_citation, lead_in_text = lead_in
        citations = [lead_in_citation, main_citation]
        requirement_text = f"{lead_in_text} ... {main_text}"
    return RequirementDraft(
        requirement_id=str(uuid.uuid4()),
        text=requirement_text,
        is_mandatory=candidate.is_mandatory,
        is_text_verifiable=candidate.is_text_verifiable,
        citations=citations,
    )


def extract_requirements_from_chunk(
    chunk: Chunk,
) -> list[RequirementDraft]:
    candidates = _extract_candidates_from_chunk(chunk)
    requirement_drafts = []
    for candidate in candidates:
        requirement_drafts.append(_build_requirement_draft(chunk, candidate))
    logger.info(
        "Extracted %d requirement candidate(s) from chunk %d of %s",
        len(requirement_drafts),
        chunk.chunk_index,
        chunk.document_path,
    )
    return requirement_drafts


def extract_requirements(
    chunks: list[Chunk],
) -> list[RequirementDraft]:
    requirement_drafts = []
    for chunk in chunks:
        requirement_drafts.extend(extract_requirements_from_chunk(chunk))
    return requirement_drafts
