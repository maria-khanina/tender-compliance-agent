from collections import defaultdict
import itertools
import uuid

import numpy as np
from pydantic import BaseModel

from backends.embeddings import embed_texts
from backends.llm_client import get_structured_chat_model, invoke_structured
from config import REQUIREMENT_DEDUPLICATION_SIMILARITY_THRESHOLD
from logging_config import get_logger
from prompts import DEDUP_GROUPING_PROMPT
from schemas import RequirementDraft, TextSpan


logger = get_logger(__name__)


class RequirementGroup(BaseModel):
    member_indices: list[int]
    canonical_text: str
    is_mandatory: bool
    is_text_verifiable: bool


class RequirementGroupList(BaseModel):
    groups: list[RequirementGroup]


def _cosine_similarity(
    first_vector: list[float],
    second_vector: list[float],
) -> float:
    first_array = np.array(first_vector)
    second_array = np.array(second_vector)
    dot_product = np.dot(first_array, second_array)
    first_norm = np.linalg.norm(first_array)
    second_norm = np.linalg.norm(second_array)
    return float(dot_product / (first_norm * second_norm))


def _find_root(parent_by_index: list[int], index: int) -> int:
    while parent_by_index[index] != index:
        parent_by_index[index] = parent_by_index[parent_by_index[index]]
        index = parent_by_index[index]
    return index


def _union_indices(
    parent_by_index: list[int],
    first_index: int,
    second_index: int,
) -> None:
    first_root = _find_root(parent_by_index, first_index)
    second_root = _find_root(parent_by_index, second_index)
    if first_root != second_root:
        parent_by_index[first_root] = second_root


def _union_similar_pairs(
    embedding_vectors: list[list[float]],
    parent_by_index: list[int],
    similarity_threshold: float,
) -> None:
    candidate_count = len(embedding_vectors)
    index_pairs = itertools.combinations(range(candidate_count), 2)
    for first_index, second_index in index_pairs:
        similarity = _cosine_similarity(
            embedding_vectors[first_index],
            embedding_vectors[second_index],
        )
        if similarity >= similarity_threshold:
            _union_indices(parent_by_index, first_index, second_index)


def _group_by_root(
    parent_by_index: list[int],
    candidate_count: int,
) -> list[list[int]]:
    clusters_by_root: dict[int, list[int]] = defaultdict(list)
    for index in range(candidate_count):
        root = _find_root(parent_by_index, index)
        clusters_by_root[root].append(index)
    return list(clusters_by_root.values())


def _cluster_by_similarity(
    embedding_vectors: list[list[float]],
    similarity_threshold: float = (
        REQUIREMENT_DEDUPLICATION_SIMILARITY_THRESHOLD
    ),
) -> list[list[int]]:
    candidate_count = len(embedding_vectors)
    parent_by_index = list(range(candidate_count))
    _union_similar_pairs(
        embedding_vectors, parent_by_index, similarity_threshold
    )
    return _group_by_root(parent_by_index, candidate_count)


def _format_numbered_candidates(
    drafts: list[RequirementDraft],
    indices: list[int],
) -> str:
    lines = []
    for position, draft_index in enumerate(indices):
        lines.append(f"{position}. {drafts[draft_index].text}")
    return "\n".join(lines)


def _merge_citations(
    drafts: list[RequirementDraft],
    indices: list[int],
) -> list[TextSpan]:
    citations = []
    for draft_index in indices:
        citations.extend(drafts[draft_index].citations)
    return citations


def _merge_applicability_condition(
    drafts: list[RequirementDraft],
    indices: list[int],
) -> TextSpan | None:
    for draft_index in indices:
        condition = drafts[draft_index].applicability_condition_citation
        if condition is not None:
            return condition
    return None


def _resolve_group(
    drafts: list[RequirementDraft],
    cluster_indices: list[int],
    group: RequirementGroup,
) -> RequirementDraft:
    group_draft_indices = []
    for member_position in group.member_indices:
        group_draft_indices.append(cluster_indices[member_position])
    merged_citations = _merge_citations(drafts, group_draft_indices)
    merged_condition = _merge_applicability_condition(
        drafts, group_draft_indices
    )
    return RequirementDraft(
        requirement_id=str(uuid.uuid4()),
        text=group.canonical_text,
        is_mandatory=group.is_mandatory,
        is_text_verifiable=group.is_text_verifiable,
        citations=merged_citations,
        applicability_condition_citation=merged_condition,
    )


def _resolve_cluster(
    drafts: list[RequirementDraft],
    cluster_indices: list[int],
) -> list[RequirementDraft]:
    if len(cluster_indices) == 1:
        return [drafts[cluster_indices[0]]]
    numbered_candidates = _format_numbered_candidates(
        drafts, cluster_indices
    )
    prompt_text = DEDUP_GROUPING_PROMPT.format(
        numbered_candidates=numbered_candidates
    )
    structured_model = get_structured_chat_model(RequirementGroupList)
    grouping_result = invoke_structured(structured_model, prompt_text)
    resolved_drafts = []
    for group in grouping_result.groups:
        resolved_drafts.append(
            _resolve_group(drafts, cluster_indices, group)
        )
    return resolved_drafts


def _embedding_text(draft: RequirementDraft) -> str:
    matching_quotes = [
        citation.quote
        for citation in draft.citations
        if citation.used_for_matching
    ]
    if not matching_quotes:
        return draft.text
    return " ".join(matching_quotes)


def deduplicate_requirements(
    drafts: list[RequirementDraft],
    similarity_threshold: float = (
        REQUIREMENT_DEDUPLICATION_SIMILARITY_THRESHOLD
    ),
) -> list[RequirementDraft]:
    if not drafts:
        return []
    draft_texts = [_embedding_text(draft) for draft in drafts]
    embedding_vectors = embed_texts(draft_texts)
    clusters = _cluster_by_similarity(embedding_vectors, similarity_threshold)
    deduplicated_drafts = []
    for cluster_indices in clusters:
        deduplicated_drafts.extend(
            _resolve_cluster(drafts, cluster_indices)
        )
    logger.info(
        "Deduplicated %d requirement candidates into %d requirements "
        "across %d clusters",
        len(drafts),
        len(deduplicated_drafts),
        len(clusters),
    )
    return deduplicated_drafts
