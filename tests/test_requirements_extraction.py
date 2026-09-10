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
        quote=(
            "Provide us with the final offer total, GARBLED as this "
            "will be the evaluated price."
        ),
        is_mandatory=True,
        is_text_verifiable=True,
    )
    draft = _build_requirement_draft(chunk, candidate)
    assert draft.citations[0].citation_verified is True
    assert "GARBLED" not in draft.text
    assert draft.text == chunk.text


def test_draft_text_falls_back_to_model_text_when_unverified() -> None:
    chunk = _build_test_chunk("Nothing relevant is written here.")
    candidate = ExtractedRequirementCandidate(
        quote="completely different sentence that is nowhere in the chunk",
        is_mandatory=True,
        is_text_verifiable=True,
    )
    draft = _build_requirement_draft(chunk, candidate)
    assert draft.citations[0].citation_verified is False
    assert draft.text == candidate.quote
