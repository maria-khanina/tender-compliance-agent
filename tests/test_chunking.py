from steps.chunking import (
    split_application_document,
    split_requirements_document,
)


def test_requirements_offsets_match_source_text() -> None:
    document_text = (
        "1. The bidder must have at least 5 years of experience.\n"
        "2. The bidder must submit a valid business license.\n"
        "3. The total price must not exceed 100000 USD.\n"
    )
    chunks = split_requirements_document(document_text, "tender.txt")
    for chunk in chunks:
        source_slice = document_text[chunk.start_char:chunk.end_char]
        assert source_slice == chunk.text


def test_requirements_splits_on_clause_numbers() -> None:
    document_text = (
        "1. First requirement text here.\n"
        "2. Second requirement text here.\n"
        "3. Third requirement text here.\n"
    )
    chunks = split_requirements_document(
        document_text,
        "tender.txt",
        fallback_chunk_size_characters=40,
        fallback_chunk_overlap_characters=0,
    )
    assert len(chunks) == 3


def test_requirements_coalesces_small_clauses() -> None:
    document_text = (
        "1. First requirement text here.\n"
        "2. Second requirement text here.\n"
        "3. Third requirement text here.\n"
    )
    chunks = split_requirements_document(document_text, "tender.txt")
    assert len(chunks) == 1


def test_application_offsets_match_source_text() -> None:
    document_text = "This is a free form application text. " * 100
    chunks = split_application_document(document_text, "application.txt")
    for chunk in chunks:
        source_slice = document_text[chunk.start_char:chunk.end_char]
        assert source_slice == chunk.text
    assert len(chunks) > 1
