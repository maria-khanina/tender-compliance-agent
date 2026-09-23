from schemas import Chunk, DocumentSource
from steps.requirements_extraction import (
    ExtractedRequirementCandidate,
    _build_requirement_draft,
)


def _build_test_chunk(text: str) -> Chunk:
    return Chunk(
        document_source=DocumentSource.REQUIREMENTS,
        document_path="tender.txt",
        chunk_index=0,
        text=text,
        start_char=0,
        end_char=len(text),
    )


def test_draft_text_uses_verified_source_not_model_text() -> None:
    chunk = _build_test_chunk(
        "Provide us with the final offer total, as this will be the "
        "evaluated price."
    )
    candidate = ExtractedRequirementCandidate(
        lead_in_quote=None,
        quote=(
            "Provide us with the final offer total, GARBLED as this "
            "will be the evaluated price."
        ),
        is_mandatory=True,
        is_text_verifiable=True,
        applicability_condition_quote=None,
    )
    draft = _build_requirement_draft(chunk, candidate)
    assert draft.citations[0].citation_verified is True
    assert "GARBLED" not in draft.text
    assert draft.text == chunk.text


def test_draft_text_falls_back_to_model_text_when_unverified() -> None:
    chunk = _build_test_chunk("Nothing relevant is written here.")
    candidate = ExtractedRequirementCandidate(
        lead_in_quote=None,
        quote="completely different sentence that is nowhere in the chunk",
        is_mandatory=True,
        is_text_verifiable=True,
        applicability_condition_quote=None,
    )
    draft = _build_requirement_draft(chunk, candidate)
    assert draft.citations[0].citation_verified is False
    assert draft.text == candidate.quote


def test_lead_in_quote_is_marked_not_used_for_matching() -> None:
    chunk = _build_test_chunk(
        "The Government will not enter into a contract with any "
        "corporation that-- has unpaid taxes."
    )
    candidate = ExtractedRequirementCandidate(
        lead_in_quote=(
            "The Government will not enter into a contract with any "
            "corporation that--"
        ),
        quote="has unpaid taxes.",
        is_mandatory=True,
        is_text_verifiable=True,
        applicability_condition_quote=None,
    )
    draft = _build_requirement_draft(chunk, candidate)
    assert len(draft.citations) == 2
    assert draft.citations[0].used_for_matching is False
    assert draft.citations[1].used_for_matching is True
    assert draft.text == (
        "The Government will not enter into a contract with any "
        "corporation that-- ... has unpaid taxes."
    )


def test_no_lead_in_quote_produces_single_citation() -> None:
    chunk = _build_test_chunk("A single self-contained requirement.")
    candidate = ExtractedRequirementCandidate(
        lead_in_quote=None,
        quote="A single self-contained requirement.",
        is_mandatory=True,
        is_text_verifiable=True,
        applicability_condition_quote=None,
    )
    draft = _build_requirement_draft(chunk, candidate)
    assert len(draft.citations) == 1
    assert draft.citations[0].used_for_matching is True
    assert draft.applicability_condition_citation is None


def test_applicability_condition_quote_is_located_and_not_used_for_matching() -> None:
    chunk = _build_test_chunk(
        "If offering an equal product, it must match the salient "
        "characteristics in Attachment B."
    )
    candidate = ExtractedRequirementCandidate(
        lead_in_quote=None,
        quote=(
            "If offering an equal product, it must match the salient "
            "characteristics in Attachment B."
        ),
        is_mandatory=True,
        is_text_verifiable=True,
        applicability_condition_quote="If offering an equal product,",
    )
    draft = _build_requirement_draft(chunk, candidate)
    condition = draft.applicability_condition_citation
    assert condition is not None
    assert condition.quote == "If offering an equal product,"
    assert condition.used_for_matching is False
    assert condition.citation_verified is True
