from evaluation.chunk_diagnostics import _describe_span_coverage
from schemas import Chunk, DocumentSource


def _chunk(chunk_index: int, start_char: int, end_char: int) -> Chunk:
    return Chunk(
        document_source=DocumentSource.REQUIREMENTS,
        document_path="doc.txt",
        chunk_index=chunk_index,
        text="x" * (end_char - start_char),
        start_char=start_char,
        end_char=end_char,
    )


def test_span_whole_in_a_single_chunk():
    chunks = [_chunk(0, 0, 100), _chunk(1, 90, 200)]
    description = _describe_span_coverage(chunks, 10, 50)
    assert "whole, in chunk(s) [0]" in description
    assert "SPLIT" not in description


def test_span_whole_in_the_overlap_of_two_chunks_is_not_reported_as_split():
    chunks = [_chunk(0, 0, 1281), _chunk(1, 1122, 2657)]
    description = _describe_span_coverage(chunks, 1122, 1270)
    assert "whole, in chunk(s) [0, 1]" in description
    assert "SPLIT" not in description


def test_span_genuinely_split_across_chunks_with_no_full_container():
    chunks = [_chunk(0, 0, 100), _chunk(1, 100, 200)]
    description = _describe_span_coverage(chunks, 90, 110)
    assert "SPLIT across chunks [0, 1]" in description


def test_span_overlapping_no_chunk():
    chunks = [_chunk(0, 0, 100)]
    description = _describe_span_coverage(chunks, 200, 250)
    assert "overlaps no chunk" in description
