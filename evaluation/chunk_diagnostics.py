from evaluation.fixtures import TrueRequirement
from schemas import Chunk
from steps.chunking import split_requirements_document
from steps.ingestion import load_document_text


_document_chunks_cache: dict[str, list[Chunk]] = {}


def _chunks_for_document(document_path: str) -> list[Chunk]:
    if document_path not in _document_chunks_cache:
        document = load_document_text(document_path)
        _document_chunks_cache[document_path] = split_requirements_document(
            document.text, document.path
        )
    return _document_chunks_cache[document_path]


def _chunk_indices_overlapping_span(
    chunks: list[Chunk],
    start_char: int,
    end_char: int,
) -> list[int]:
    overlapping = []
    for chunk in chunks:
        if chunk.start_char < end_char and start_char < chunk.end_char:
            overlapping.append(chunk.chunk_index)
    return overlapping


def _chunk_indices_fully_containing_span(
    chunks: list[Chunk],
    start_char: int,
    end_char: int,
) -> list[int]:
    containing = []
    for chunk in chunks:
        if chunk.start_char <= start_char and end_char <= chunk.end_char:
            containing.append(chunk.chunk_index)
    return containing


def _describe_span_coverage(
    chunks: list[Chunk],
    start_char: int,
    end_char: int,
) -> str:
    containing_indices = _chunk_indices_fully_containing_span(
        chunks, start_char, end_char
    )
    if containing_indices:
        return (
            f"[{start_char}:{end_char}] whole, in chunk(s) "
            f"{containing_indices} -- the model saw this text intact"
        )
    overlapping_indices = _chunk_indices_overlapping_span(
        chunks, start_char, end_char
    )
    if not overlapping_indices:
        return (
            f"[{start_char}:{end_char}] overlaps no chunk "
            "-- offset may be stale"
        )
    return (
        f"[{start_char}:{end_char}] SPLIT across chunks "
        f"{overlapping_indices} -- the model may never have seen this "
        "requirement's full text in one call"
    )


def describe_missed_topic_chunk_coverage(topic: TrueRequirement) -> str:
    """Mechanically check whether a missed true topic's matching span(s)
    were ever presented to the extraction LLM whole, in a single chunk,
    or were split across chunk boundaries. This does not call any LLM --
    it just re-runs the same deterministic chunking the pipeline used.
    """
    try:
        chunks = _chunks_for_document(topic.source.document_path)
    except (OSError, ValueError) as error:
        return f"could not re-chunk {topic.source.document_path}: {error}"

    matching_spans = [
        span for span in topic.source.spans if span.used_for_matching
    ]
    if not matching_spans:
        matching_spans = topic.source.spans

    descriptions = [
        _describe_span_coverage(chunks, span.start_char, span.end_char)
        for span in matching_spans
    ]
    return "; ".join(descriptions)
