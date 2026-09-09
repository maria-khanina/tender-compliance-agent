import threading
from collections.abc import Callable
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from config import EmbeddingProvider, settings
from logging_config import get_logger


logger = get_logger(__name__)

_sentence_transformers_inference_lock = threading.Lock()


@lru_cache(maxsize=1)
def _get_sentence_transformers_model() -> SentenceTransformer:
    logger.info(
        "Loading embedding model %s", settings.embedding_model_name
    )
    return SentenceTransformer(settings.embedding_model_name)


def _embed_texts_with_sentence_transformers(
    texts: list[str],
) -> list[list[float]]:
    embedding_model = _get_sentence_transformers_model()
    with _sentence_transformers_inference_lock:
        embedding_vectors = embedding_model.encode(texts)
    return embedding_vectors.tolist()


def _embedding_dimension_with_sentence_transformers() -> int:
    embedding_model = _get_sentence_transformers_model()
    dimension = embedding_model.get_embedding_dimension()
    if dimension is None:
        raise RuntimeError(
            "Embedding model "
            f"{settings.embedding_model_name} does not expose its "
            "output dimension."
        )
    return dimension


EMBEDDING_TEXT_ENCODERS: dict[
    EmbeddingProvider, Callable[[list[str]], list[list[float]]]
] = {
    "sentence_transformers": _embed_texts_with_sentence_transformers,
}

EMBEDDING_DIMENSION_PROVIDERS: dict[
    EmbeddingProvider, Callable[[], int]
] = {
    "sentence_transformers": _embedding_dimension_with_sentence_transformers,
}


def embed_texts(texts: list[str]) -> list[list[float]]:
    encoder = EMBEDDING_TEXT_ENCODERS[settings.embedding_provider]
    return encoder(texts)


def embed_text(text: str) -> list[float]:
    embedding_vectors = embed_texts([text])
    return embedding_vectors[0]


def get_embedding_dimension() -> int:
    dimension_provider = EMBEDDING_DIMENSION_PROVIDERS[
        settings.embedding_provider
    ]
    return dimension_provider()
