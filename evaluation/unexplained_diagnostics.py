import numpy as np

from backends.embeddings import embed_texts
from config import REQUIREMENT_DEDUPLICATION_CANDIDATE_SIMILARITY_THRESHOLD
from evaluation.fixtures import TrueRequirementsFixture
from evaluation.matching import MatchGroup
from schemas import Requirement
from steps.deduplication import _embedding_text


def _cosine_similarity(first: list[float], second: list[float]) -> float:
    first_array = np.array(first)
    second_array = np.array(second)
    return float(
        np.dot(first_array, second_array)
        / (np.linalg.norm(first_array) * np.linalg.norm(second_array))
    )


def _dedup_visibility_note(
    unexplained_vector: list[float],
    top_topic_id: str,
    group_by_topic: dict[str, MatchGroup],
    predicted_vectors_by_id: dict[str, list[float]],
) -> str:
    group = group_by_topic.get(top_topic_id)
    if group is None or not group.predicted_node_ids:
        return (
            "that true topic has no matched predicted requirement in this "
            "run, so there was nothing for dedup to compare it against"
        )
    best_sibling_id = None
    best_similarity = -1.0
    for sibling_id in group.predicted_node_ids:
        sibling_vector = predicted_vectors_by_id.get(sibling_id)
        if sibling_vector is None:
            continue
        similarity = _cosine_similarity(unexplained_vector, sibling_vector)
        if similarity > best_similarity:
            best_similarity = similarity
            best_sibling_id = sibling_id
    if best_sibling_id is None:
        return "could not compare against the matched predicted requirement"
    would_cluster = (
        best_similarity >= REQUIREMENT_DEDUPLICATION_CANDIDATE_SIMILARITY_THRESHOLD
    )
    verdict = (
        "would likely have been clustered together and compared by the "
        "dedup LLM call" if would_cluster else
        "dedup's cosine pre-filter would NOT have clustered these -- the "
        "dedup LLM call never saw them side by side"
    )
    short_id = best_sibling_id[:8]
    return (
        f"vs matched predicted [{short_id}]: cosine={best_similarity:.2f} "
        f"({'>=' if would_cluster else '<'} dedup threshold "
        f"{REQUIREMENT_DEDUPLICATION_CANDIDATE_SIMILARITY_THRESHOLD}) -> {verdict}"
    )


def annotate_unexplained_requirements(
    unexplained_requirement_ids: list[str],
    all_predicted_requirements: list[Requirement],
    fixture: TrueRequirementsFixture,
    group_by_topic: dict[str, MatchGroup],
) -> dict[str, str]:
    """For each unexplained predicted requirement, mechanically (no LLM
    judgment call) find its closest true topic by embedding cosine
    similarity, and check whether dedup's own similarity pre-filter would
    have clustered it with whatever predicted requirement DID match that
    topic -- i.e. whether the dedup LLM call ever had a chance to compare
    them at all.
    """
    if not unexplained_requirement_ids or not fixture.requirements:
        return {}

    topic_ids = [topic.topic_id for topic in fixture.requirements]
    topic_texts = [topic.description for topic in fixture.requirements]
    predicted_ids = [req.requirement_id for req in all_predicted_requirements]
    predicted_texts = [
        _embedding_text(req) for req in all_predicted_requirements
    ]

    all_vectors = embed_texts(topic_texts + predicted_texts)
    topic_vectors = all_vectors[:len(topic_texts)]
    predicted_vectors = all_vectors[len(topic_texts):]
    predicted_vectors_by_id = dict(zip(predicted_ids, predicted_vectors))

    annotations: dict[str, str] = {}
    for requirement_id in unexplained_requirement_ids:
        unexplained_vector = predicted_vectors_by_id.get(requirement_id)
        if unexplained_vector is None:
            continue
        similarities = [
            _cosine_similarity(unexplained_vector, topic_vector)
            for topic_vector in topic_vectors
        ]
        best_index = max(range(len(similarities)), key=similarities.__getitem__)
        top_topic_id = topic_ids[best_index]
        top_score = similarities[best_index]
        dedup_note = _dedup_visibility_note(
            unexplained_vector, top_topic_id, group_by_topic,
            predicted_vectors_by_id,
        )
        annotations[requirement_id] = (
            f"closest true topic: `{top_topic_id}` (cosine={top_score:.2f}); "
            f"{dedup_note}"
        )
    return annotations
