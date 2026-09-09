from schemas import Chunk, DocumentSource
from steps.text_matching import locate_quote_in_chunk


def _build_test_chunk(text: str) -> Chunk:
    return Chunk(
        document_source=DocumentSource.APPLICATION,
        document_path="application.txt",
        chunk_index=0,
        text=text,
        start_char=100,
        end_char=100 + len(text),
    )


def test_exact_match_is_verified() -> None:
    chunk = _build_test_chunk("The exact phrase appears here.")
    span = locate_quote_in_chunk(chunk, "exact phrase appears")
    assert span.citation_verified is True
    assert span.match_precision == "precise"
    assert span.start_char is not None
    assert span.end_char is not None
    local_start = span.start_char - chunk.start_char
    local_end = span.end_char - chunk.start_char
    assert chunk.text[local_start:local_end] == "exact phrase appears"


def test_whitespace_normalized_match_is_verified() -> None:
    chunk = _build_test_chunk("Has   over 7   years of experience.")
    span = locate_quote_in_chunk(chunk, "over 7 years of experience")
    assert span.citation_verified is True
    assert span.match_precision == "precise"


def test_fuzzy_match_is_verified_as_fuzzy() -> None:
    chunk = _build_test_chunk(
        "The company has over 7 years of relevant experience."
    )
    span = locate_quote_in_chunk(chunk, "over 7 years of relevent experence")
    assert span.citation_verified is True
    assert span.match_precision == "fuzzy"


def test_unrelated_quote_is_not_verified() -> None:
    chunk = _build_test_chunk("Nothing relevant is written here.")
    span = locate_quote_in_chunk(chunk, "completely different sentence")
    assert span.citation_verified is False
    assert span.match_precision is None
    assert span.start_char is None
    assert span.end_char is None
