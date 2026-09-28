import threading
from functools import lru_cache

from sentence_transformers import CrossEncoder

from config import RERANKER_MODEL_NAME
from logging_config import get_logger


logger = get_logger(__name__)

_cross_encoder_inference_lock = threading.Lock()


@lru_cache(maxsize=1)
def _get_cross_encoder_model() -> CrossEncoder:
    logger.info("Loading reranker model %s", RERANKER_MODEL_NAME)
    return CrossEncoder(RERANKER_MODEL_NAME)


def score_text_pairs(pairs: list[tuple[str, str]]) -> list[float]:
    if not pairs:
        return []
    cross_encoder_model = _get_cross_encoder_model()
    with _cross_encoder_inference_lock:
        scores = cross_encoder_model.predict(pairs)
    return scores.tolist()
