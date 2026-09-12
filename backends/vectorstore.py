import uuid
from typing import Protocol

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    PointStruct,
    VectorParams,
)
from backends.embeddings import (
    embed_text,
    embed_texts,
    get_embedding_dimension,
)
from backends.retry import build_retry_decorator
from config import (
    VECTOR_STORE_RETRY_ATTEMPT_COUNT,
    VECTOR_STORE_RETRY_WAIT_MAXIMUM_SECONDS,
    VECTOR_STORE_RETRY_WAIT_MINIMUM_SECONDS,
    VectorStoreProvider,
    settings,
)
from logging_config import get_logger
from schemas import Chunk


POINT_ID_NAMESPACE = uuid.NAMESPACE_DNS

logger = get_logger(__name__)

_vector_store_retry = build_retry_decorator(
    VECTOR_STORE_RETRY_ATTEMPT_COUNT,
    VECTOR_STORE_RETRY_WAIT_MINIMUM_SECONDS,
    VECTOR_STORE_RETRY_WAIT_MAXIMUM_SECONDS,
)


def _compute_point_id(chunk: Chunk) -> str:
    reference = f"{chunk.document_path}#{chunk.chunk_index}"
    return str(uuid.uuid5(POINT_ID_NAMESPACE, reference))


class VectorStoreBackend(Protocol):
    def reset_collection(
        self, collection_name: str, vector_size: int
    ) -> None: ...

    def index_chunks(
        self, collection_name: str, chunks: list[Chunk]
    ) -> None: ...

    def search_similar_chunks(
        self,
        collection_name: str,
        query_text: str,
        result_limit: int,
    ) -> list[tuple[Chunk, float]]: ...

    def get_neighbor_chunks(
        self,
        collection_name: str,
        document_path: str,
        chunk_indices: list[int],
    ) -> list[Chunk]: ...

    def delete_collection(self, collection_name: str) -> None: ...


class QdrantVectorStoreBackend:
    def __init__(self) -> None:
        self._client: QdrantClient | None = None

    def _get_client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(url=settings.vector_store_url)
        return self._client

    def _existing_collection_names(self) -> list[str]:
        client = self._get_client()
        existing_collections = client.get_collections().collections
        existing_collection_names = []
        for collection in existing_collections:
            existing_collection_names.append(collection.name)
        return existing_collection_names

    @_vector_store_retry
    def reset_collection(
        self, collection_name: str, vector_size: int
    ) -> None:
        client = self._get_client()
        if collection_name in self._existing_collection_names():
            client.delete_collection(collection_name)
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )
        logger.info("Reset vector store collection %s", collection_name)

    @_vector_store_retry
    def index_chunks(
        self, collection_name: str, chunks: list[Chunk]
    ) -> None:
        self.reset_collection(collection_name, get_embedding_dimension())
        client = self._get_client()
        chunk_texts = [chunk.text for chunk in chunks]
        embedding_vectors = embed_texts(chunk_texts)
        indexed_points = []
        for chunk, embedding_vector in zip(chunks, embedding_vectors):
            indexed_points.append(
                PointStruct(
                    id=_compute_point_id(chunk),
                    vector=embedding_vector,
                    payload=chunk.model_dump(mode="json"),
                )
            )
        client.upsert(
            collection_name=collection_name,
            points=indexed_points,
        )
        logger.info(
            "Indexed %d application chunks into collection %s",
            len(chunks),
            collection_name,
        )

    @_vector_store_retry
    def search_similar_chunks(
        self,
        collection_name: str,
        query_text: str,
        result_limit: int,
    ) -> list[tuple[Chunk, float]]:
        client = self._get_client()
        query_vector = embed_text(query_text)
        search_response = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=result_limit,
        )
        matches = []
        for scored_point in search_response.points:
            matches.append((
                Chunk.model_validate(scored_point.payload),
                scored_point.score,
            ))
        return matches

    @_vector_store_retry
    def get_neighbor_chunks(
        self,
        collection_name: str,
        document_path: str,
        chunk_indices: list[int],
    ) -> list[Chunk]:
        if not chunk_indices:
            return []
        client = self._get_client()
        scroll_filter = Filter(
            must=[
                FieldCondition(
                    key="document_path",
                    match=MatchValue(value=document_path),
                ),
                FieldCondition(
                    key="chunk_index",
                    match=MatchAny(any=chunk_indices),
                ),
            ]
        )
        records, _ = client.scroll(
            collection_name=collection_name,
            scroll_filter=scroll_filter,
            limit=len(chunk_indices),
        )
        return [Chunk.model_validate(record.payload) for record in records]

    @_vector_store_retry
    def delete_collection(self, collection_name: str) -> None:
        client = self._get_client()
        if collection_name in self._existing_collection_names():
            client.delete_collection(collection_name)
            logger.info("Deleted vector store collection %s", collection_name)


VECTOR_STORE_BACKENDS: dict[VectorStoreProvider, VectorStoreBackend] = {
    "qdrant": QdrantVectorStoreBackend(),
}


def _get_backend() -> VectorStoreBackend:
    return VECTOR_STORE_BACKENDS[settings.vector_store_provider]


def case_collection_name(identifier: str) -> str:
    return f"{settings.vector_store_collection_name}__{identifier}"


def reset_collection(collection_name: str, vector_size: int) -> None:
    _get_backend().reset_collection(collection_name, vector_size)


def index_chunks(collection_name: str, chunks: list[Chunk]) -> None:
    _get_backend().index_chunks(collection_name, chunks)


def search_similar_chunks(
    collection_name: str,
    query_text: str,
    result_limit: int,
) -> list[tuple[Chunk, float]]:
    return _get_backend().search_similar_chunks(
        collection_name, query_text, result_limit
    )


def get_neighbor_chunks(
    collection_name: str,
    document_path: str,
    chunk_indices: list[int],
) -> list[Chunk]:
    return _get_backend().get_neighbor_chunks(
        collection_name, document_path, chunk_indices
    )


def delete_collection(collection_name: str) -> None:
    _get_backend().delete_collection(collection_name)
