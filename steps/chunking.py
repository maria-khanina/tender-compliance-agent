import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    APPLICATION_CHUNK_OVERLAP_CHARACTERS,
    APPLICATION_CHUNK_SIZE_CHARACTERS,
    REQUIREMENTS_CLAUSE_DETECTION_SAMPLE_LINES,
    REQUIREMENTS_CLAUSE_MINIMUM_MATCH_COUNT,
    REQUIREMENTS_FALLBACK_CHUNK_OVERLAP_CHARACTERS,
    REQUIREMENTS_FALLBACK_CHUNK_SIZE_CHARACTERS,
)
from logging_config import get_logger
from schemas import Chunk, DocumentSource


CLAUSE_PATTERN_CANDIDATES = [
    r"^\s*\d+(?:\.\d+)*\.?\s+",
    r"^\s*\(?[a-zA-Z]\)\s+",
    r"^\s*[-•]\s+",
    r"^\s*Section\s+\d+",
    r"^\s*Article\s+\d+",
]

logger = get_logger(__name__)


def _sample_text_for_detection(document_text: str) -> str:
    sample_lines = document_text.splitlines()
    sample_lines = sample_lines[:REQUIREMENTS_CLAUSE_DETECTION_SAMPLE_LINES]
    return "\n".join(sample_lines)


def _count_pattern_matches(
    pattern_text: str,
    sample_text: str,
) -> tuple[re.Pattern[str], int]:
    compiled_pattern = re.compile(pattern_text, re.MULTILINE)
    match_count = len(compiled_pattern.findall(sample_text))
    return compiled_pattern, match_count


def _best_clause_pattern_candidate(
    sample_text: str,
) -> tuple[re.Pattern[str] | None, int]:
    best_pattern = None
    best_match_count = 0
    for pattern_text in CLAUSE_PATTERN_CANDIDATES:
        compiled_pattern, match_count = _count_pattern_matches(
            pattern_text, sample_text
        )
        if match_count > best_match_count:
            best_match_count = match_count
            best_pattern = compiled_pattern
    return best_pattern, best_match_count


def _detect_best_clause_pattern(
    document_text: str,
) -> re.Pattern[str] | None:
    sample_text = _sample_text_for_detection(document_text)
    best_pattern, best_match_count = _best_clause_pattern_candidate(
        sample_text
    )
    if best_match_count < REQUIREMENTS_CLAUSE_MINIMUM_MATCH_COUNT:
        return None
    return best_pattern


def _find_clause_boundaries(
    document_text: str,
    clause_pattern: re.Pattern[str],
) -> list[int]:
    boundaries = []
    for match in clause_pattern.finditer(document_text):
        boundaries.append(match.start())
    return boundaries


def _boundary_end_offset(
    boundary_offsets: list[int],
    position: int,
    document_length: int,
) -> int:
    last_index = len(boundary_offsets) - 1
    if position < last_index:
        return boundary_offsets[position + 1]
    return document_length


def _split_by_boundaries(
    document_text: str,
    boundary_offsets: list[int],
) -> list[tuple[int, int]]:
    spans = []
    if boundary_offsets[0] > 0:
        spans.append((0, boundary_offsets[0]))
    document_length = len(document_text)
    for position, start_offset in enumerate(boundary_offsets):
        end_offset = _boundary_end_offset(
            boundary_offsets, position, document_length
        )
        spans.append((start_offset, end_offset))
    return spans


def _coalesce_small_spans(
    spans: list[tuple[int, int]],
    target_chunk_size_characters: int,
) -> list[tuple[int, int]]:
    coalesced_spans = []
    current_start, current_end = spans[0]
    for span_start, span_end in spans[1:]:
        combined_length = span_end - current_start
        if combined_length <= target_chunk_size_characters:
            current_end = span_end
        else:
            coalesced_spans.append((current_start, current_end))
            current_start, current_end = span_start, span_end
    coalesced_spans.append((current_start, current_end))
    return coalesced_spans


def _locate_piece(
    container_text: str,
    piece: str,
    search_cursor: int,
) -> int:
    found_index = container_text.find(piece, search_cursor)
    if found_index == -1:
        found_index = container_text.find(piece)
    if found_index == -1:
        raise ValueError(
            "Text splitter produced a piece that is not a "
            "literal substring of its source text: "
            f"{piece[:80]!r}"
        )
    return found_index


def _locate_piece_offsets(
    container_text: str,
    pieces: list[str],
) -> list[tuple[int, int]]:
    offsets = []
    search_cursor = 0
    for piece in pieces:
        found_index = _locate_piece(container_text, piece, search_cursor)
        offsets.append((found_index, found_index + len(piece)))
        search_cursor = found_index
    return offsets


def _recursive_split_with_offsets(
    text: str,
    base_offset: int,
    chunk_size_characters: int,
    chunk_overlap_characters: int,
) -> list[tuple[int, int]]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size_characters,
        chunk_overlap=chunk_overlap_characters,
    )
    pieces = splitter.split_text(text)
    local_offsets = _locate_piece_offsets(text, pieces)
    offsets = []
    for local_start, local_end in local_offsets:
        offsets.append((base_offset + local_start, base_offset + local_end))
    return offsets


def _split_oversized_span(
    document_text: str,
    span_start: int,
    span_end: int,
    fallback_chunk_size_characters: int,
    fallback_chunk_overlap_characters: int,
) -> list[tuple[int, int]]:
    span_length = span_end - span_start
    if span_length <= fallback_chunk_size_characters:
        return [(span_start, span_end)]
    span_text = document_text[span_start:span_end]
    return _recursive_split_with_offsets(
        span_text,
        span_start,
        fallback_chunk_size_characters,
        fallback_chunk_overlap_characters,
    )


def _build_chunks(
    document_text: str,
    spans: list[tuple[int, int]],
    document_source: DocumentSource,
    document_path: str,
) -> list[Chunk]:
    if not spans:
        raise ValueError(
            f"Splitting the {document_source.value} document produced "
            "no chunks; the document may be empty."
        )
    chunks = []
    for chunk_index, span in enumerate(spans):
        span_start, span_end = span
        chunks.append(
            Chunk(
                document_source=document_source,
                document_path=document_path,
                chunk_index=chunk_index,
                text=document_text[span_start:span_end],
                start_char=span_start,
                end_char=span_end,
            )
        )
    return chunks


def _split_via_fallback(
    document_text: str,
    fallback_chunk_size_characters: int,
    fallback_chunk_overlap_characters: int,
) -> list[tuple[int, int]]:
    logger.info(
        "No clause numbering detected; using fallback splitter "
        "for the requirements document"
    )
    return _recursive_split_with_offsets(
        document_text,
        0,
        fallback_chunk_size_characters,
        fallback_chunk_overlap_characters,
    )


def _split_via_clause_pattern(
    document_text: str,
    clause_pattern: re.Pattern[str],
    fallback_chunk_size_characters: int,
    fallback_chunk_overlap_characters: int,
) -> list[tuple[int, int]]:
    logger.info(
        "Detected clause pattern %s for the requirements document",
        clause_pattern.pattern,
    )
    boundary_offsets = _find_clause_boundaries(document_text, clause_pattern)
    clause_spans = _split_by_boundaries(document_text, boundary_offsets)
    coalesced_spans = _coalesce_small_spans(
        clause_spans, fallback_chunk_size_characters
    )
    spans = []
    for span_start, span_end in coalesced_spans:
        spans.extend(
            _split_oversized_span(
                document_text,
                span_start,
                span_end,
                fallback_chunk_size_characters,
                fallback_chunk_overlap_characters,
            )
        )
    return spans


def split_requirements_document(
    document_text: str,
    document_path: str,
    fallback_chunk_size_characters: int = (
        REQUIREMENTS_FALLBACK_CHUNK_SIZE_CHARACTERS
    ),
    fallback_chunk_overlap_characters: int = (
        REQUIREMENTS_FALLBACK_CHUNK_OVERLAP_CHARACTERS
    ),
) -> list[Chunk]:
    clause_pattern = _detect_best_clause_pattern(document_text)
    if clause_pattern is None:
        spans = _split_via_fallback(
            document_text, fallback_chunk_size_characters,
            fallback_chunk_overlap_characters,
        )
    else:
        spans = _split_via_clause_pattern(
            document_text, clause_pattern, fallback_chunk_size_characters,
            fallback_chunk_overlap_characters,
        )
    chunks = _build_chunks(
        document_text, spans, DocumentSource.REQUIREMENTS, document_path
    )
    logger.info("Split requirements document into %d chunks", len(chunks))
    return chunks


def split_application_document(
    document_text: str,
    document_path: str,
    chunk_size_characters: int = APPLICATION_CHUNK_SIZE_CHARACTERS,
    chunk_overlap_characters: int = APPLICATION_CHUNK_OVERLAP_CHARACTERS,
) -> list[Chunk]:
    spans = _recursive_split_with_offsets(
        document_text,
        0,
        chunk_size_characters,
        chunk_overlap_characters,
    )
    chunks = _build_chunks(
        document_text, spans, DocumentSource.APPLICATION, document_path
    )
    logger.info("Split application document into %d chunks", len(chunks))
    return chunks
