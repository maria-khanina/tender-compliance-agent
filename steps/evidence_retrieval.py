from backends.vectorstore import get_neighbor_chunks, search_similar_chunks
from config import (
    AVERAGE_CHARACTERS_PER_TOKEN,
    EVIDENCE_MAXIMUM_CHUNK_COUNT,
    EVIDENCE_MAXIMUM_TOTAL_TOKENS,
    EVIDENCE_MINIMUM_CHUNK_COUNT,
    EVIDENCE_NEIGHBOR_EXPANSION_TOP_HIT_COUNT,
    EVIDENCE_RETRIEVAL_TOP_K,
    EVIDENCE_SIMILARITY_THRESHOLD,
)
from logging_config import get_logger
from schemas import Chunk


logger = get_logger(__name__)


def _approximate_token_count(text: str) -> int:
    return int(len(text) / AVERAGE_CHARACTERS_PER_TOKEN)


def _collect_neighbor_indices_by_document(
    matches: list[tuple[Chunk, float]],
    neighbor_expansion_top_hit_count: int,
) -> dict[str, list[int]]:
    neighbor_indices_by_document: dict[str, list[int]] = {}
    top_matches = matches[:neighbor_expansion_top_hit_count]
    for chunk, _ in top_matches:
        document_neighbors = neighbor_indices_by_document.setdefault(
            chunk.document_path, []
        )
        if chunk.chunk_index - 1 >= 0:
            document_neighbors.append(chunk.chunk_index - 1)
        document_neighbors.append(chunk.chunk_index + 1)
    return neighbor_indices_by_document


def _collect_neighbor_chunks(
    collection_name: str,
    matches: list[tuple[Chunk, float]],
    neighbor_expansion_top_hit_count: int,
) -> list[Chunk]:
    neighbor_indices_by_document = _collect_neighbor_indices_by_document(
        matches, neighbor_expansion_top_hit_count
    )
    neighbor_chunks = []
    for document_path, chunk_indices in (
        neighbor_indices_by_document.items()
    ):
        neighbor_chunks.extend(
            get_neighbor_chunks(collection_name, document_path, chunk_indices)
        )
    return neighbor_chunks


def _deduplicate_chunks(chunks: list[Chunk]) -> list[Chunk]:
    seen_chunk_keys = set()
    unique_chunks = []
    for chunk in chunks:
        chunk_key = (chunk.document_path, chunk.chunk_index)
        if chunk_key in seen_chunk_keys:
            continue
        seen_chunk_keys.add(chunk_key)
        unique_chunks.append(chunk)
    return unique_chunks


def _should_stop_selecting(
    selected_count: int,
    minimum_chunk_count: int,
    maximum_chunk_count: int,
    total_token_count: int,
    chunk_token_count: int,
    maximum_total_tokens: int,
) -> bool:
    if selected_count < minimum_chunk_count:
        return False
    reached_maximum_count = selected_count >= maximum_chunk_count
    reached_token_budget = (
        total_token_count + chunk_token_count > maximum_total_tokens
    )
    return reached_maximum_count or reached_token_budget


def _select_within_budget(
    ranked_chunks: list[Chunk],
    minimum_chunk_count: int,
    maximum_chunk_count: int,
    maximum_total_tokens: int,
) -> list[Chunk]:
    selected_chunks: list[Chunk] = []
    total_token_count = 0
    for chunk in ranked_chunks:
        chunk_token_count = _approximate_token_count(chunk.text)
        should_stop = _should_stop_selecting(
            len(selected_chunks), minimum_chunk_count, maximum_chunk_count,
            total_token_count, chunk_token_count, maximum_total_tokens,
        )
        if should_stop:
            break
        selected_chunks.append(chunk)
        total_token_count += chunk_token_count
    return selected_chunks


def _select_chunks_above_threshold(
    matches: list[tuple[Chunk, float]],
    similarity_threshold: float,
    minimum_chunk_count: int,
) -> list[Chunk]:
    thresholded_chunks = []
    for chunk, score in matches:
        if score >= similarity_threshold:
            thresholded_chunks.append(chunk)
    if len(thresholded_chunks) >= minimum_chunk_count:
        return thresholded_chunks
    top_matches = matches[:minimum_chunk_count]
    return [chunk for chunk, _ in top_matches]


def retrieve_evidence_chunks(
    requirement_text: str,
    collection_name: str,
    top_k: int = EVIDENCE_RETRIEVAL_TOP_K,
    similarity_threshold: float = EVIDENCE_SIMILARITY_THRESHOLD,
    minimum_chunk_count: int = EVIDENCE_MINIMUM_CHUNK_COUNT,
    maximum_chunk_count: int = EVIDENCE_MAXIMUM_CHUNK_COUNT,
    maximum_total_tokens: int = EVIDENCE_MAXIMUM_TOTAL_TOKENS,
    neighbor_expansion_top_hit_count: int = (
        EVIDENCE_NEIGHBOR_EXPANSION_TOP_HIT_COUNT
    ),
) -> list[Chunk]:
    matches = search_similar_chunks(collection_name, requirement_text, top_k)
    ranked_chunks = _select_chunks_above_threshold(
        matches, similarity_threshold, minimum_chunk_count
    )
    neighbor_chunks = _collect_neighbor_chunks(
        collection_name, matches, neighbor_expansion_top_hit_count
    )
    combined_chunks = ranked_chunks + neighbor_chunks
    unique_chunks = _deduplicate_chunks(combined_chunks)
    evidence_chunks = _select_within_budget(
        unique_chunks,
        minimum_chunk_count,
        maximum_chunk_count,
        maximum_total_tokens,
    )
    logger.debug(
        "Retrieved %d evidence chunk(s) for requirement text %r",
        len(evidence_chunks),
        requirement_text[:80],
    )
    return evidence_chunks
