from rapidfuzz import fuzz

from config import (
    CITATION_FUZZY_MATCH_MINIMUM_SCORE,
    LOG_MESSAGE_PREVIEW_CHARACTER_COUNT,
)
from logging_config import get_logger
from schemas import Chunk, MatchPrecision, TextSpan


FUZZY_SCORE_SCALE = 100.0

logger = get_logger(__name__)


def _process_character(
    character: str,
    index: int,
    previous_was_space: bool,
    normalized_characters: list[str],
    offset_map: list[int],
) -> bool:
    if character.isspace():
        if not previous_was_space and normalized_characters:
            normalized_characters.append(" ")
            offset_map.append(index)
        return True
    normalized_characters.append(character)
    offset_map.append(index)
    return False


def _normalize_with_offset_map(text: str) -> tuple[str, list[int]]:
    normalized_characters: list[str] = []
    offset_map: list[int] = []
    previous_was_space = False
    for index, character in enumerate(text):
        previous_was_space = _process_character(
            character, index, previous_was_space, normalized_characters,
            offset_map,
        )
    normalized_text = "".join(normalized_characters)
    return normalized_text, offset_map


def _map_to_original_offsets(
    offset_map: list[int],
    found_index: int,
    match_length: int,
) -> tuple[int, int]:
    match_end_index = found_index + match_length - 1
    original_start = offset_map[found_index]
    original_end = offset_map[match_end_index] + 1
    return original_start, original_end


def _find_normalized_match(
    chunk_text: str,
    quote: str,
) -> tuple[int, int] | None:
    normalized_chunk_text, offset_map = _normalize_with_offset_map(
        chunk_text
    )
    normalized_quote, _ = _normalize_with_offset_map(quote)
    if not normalized_quote:
        return None
    found_index = normalized_chunk_text.find(normalized_quote)
    if found_index == -1:
        return None
    return _map_to_original_offsets(
        offset_map, found_index, len(normalized_quote)
    )


def _find_fuzzy_match(
    chunk_text: str,
    quote: str,
) -> tuple[int, int, float] | None:
    alignment = fuzz.partial_ratio_alignment(quote, chunk_text)
    if alignment is None:
        return None
    return alignment.dest_start, alignment.dest_end, alignment.score


def _build_text_span(
    document_path: str,
    quote: str,
    start_char: int | None,
    end_char: int | None,
    citation_verified: bool,
    match_precision: MatchPrecision | None = None,
) -> TextSpan:
    return TextSpan(
        document_path=document_path,
        quote=quote,
        start_char=start_char,
        end_char=end_char,
        citation_verified=citation_verified,
        match_precision=match_precision,
    )


def _span_from_local_offsets(
    chunk: Chunk,
    quote: str,
    local_start: int,
    local_end: int,
    match_precision: MatchPrecision,
) -> TextSpan:
    start_char = chunk.start_char + local_start
    end_char = chunk.start_char + local_end
    return _build_text_span(
        chunk.document_path, quote, start_char, end_char, True,
        match_precision,
    )


def _try_exact_match(chunk: Chunk, quote: str) -> TextSpan | None:
    exact_index = chunk.text.find(quote)
    if exact_index == -1:
        return None
    return _span_from_local_offsets(
        chunk, quote, exact_index, exact_index + len(quote), "precise"
    )


def _try_normalized_match(chunk: Chunk, quote: str) -> TextSpan | None:
    normalized_match = _find_normalized_match(chunk.text, quote)
    if normalized_match is None:
        return None
    local_start, local_end = normalized_match
    return _span_from_local_offsets(
        chunk, quote, local_start, local_end, "precise"
    )


def _try_fuzzy_match(
    chunk: Chunk,
    quote: str,
    fuzzy_match_minimum_score: float,
) -> TextSpan | None:
    fuzzy_match = _find_fuzzy_match(chunk.text, quote)
    if fuzzy_match is None:
        return None
    local_start, local_end, score = fuzzy_match
    match_ratio = score / FUZZY_SCORE_SCALE
    if match_ratio < fuzzy_match_minimum_score:
        return None
    return _span_from_local_offsets(
        chunk, quote, local_start, local_end, "fuzzy"
    )


def _log_unlocated_quote(chunk: Chunk, quote: str) -> None:
    quote_preview = quote[:LOG_MESSAGE_PREVIEW_CHARACTER_COUNT]
    logger.warning(
        "Could not locate quote in chunk %d of %s: %r",
        chunk.chunk_index,
        chunk.document_path,
        quote_preview,
    )


def _locate_quote_via_cascade(
    chunk: Chunk,
    quote: str,
    fuzzy_match_minimum_score: float,
) -> TextSpan | None:
    exact_span = _try_exact_match(chunk, quote)
    if exact_span is not None:
        return exact_span
    normalized_span = _try_normalized_match(chunk, quote)
    if normalized_span is not None:
        return normalized_span
    return _try_fuzzy_match(chunk, quote, fuzzy_match_minimum_score)


def locate_quote_in_chunk(
    chunk: Chunk,
    quote: str,
    fuzzy_match_minimum_score: float = CITATION_FUZZY_MATCH_MINIMUM_SCORE,
) -> TextSpan:
    span = _locate_quote_via_cascade(
        chunk, quote, fuzzy_match_minimum_score
    )
    if span is not None:
        return span
    _log_unlocated_quote(chunk, quote)
    return _build_text_span(chunk.document_path, quote, None, None, False)


def format_chunks_as_prompt_text(chunks: list[Chunk]) -> str:
    formatted_lines = []
    for chunk in chunks:
        formatted_lines.append(f"[{chunk.chunk_index}] {chunk.text}")
    return "\n\n".join(formatted_lines)


def find_chunk_by_index(
    chunks: list[Chunk],
    chunk_index: int,
) -> Chunk | None:
    for chunk in chunks:
        if chunk.chunk_index == chunk_index:
            return chunk
    return None
