from schemas import RequirementDraft, TextSpan
from steps.deduplication import (
    _cluster_by_similarity,
    _embedding_text,
    _resolve_group,
)


def _draft(
    requirement_id: str,
    text: str,
    is_mandatory: bool = True,
    is_text_verifiable: bool = True,
) -> RequirementDraft:
    return RequirementDraft(
        requirement_id=requirement_id,
        text=text,
        is_mandatory=is_mandatory,
        is_text_verifiable=is_text_verifiable,
        citations=[TextSpan(
            document_path="tender.txt",
            quote=text,
            start_char=0,
            end_char=len(text),
            citation_verified=True,
        )],
    )


def test_resolve_group_is_mandatory_is_true_if_any_member_is_mandatory() -> None:
    drafts = [
        _draft("draft_a", "text a", is_mandatory=False),
        _draft("draft_b", "text b", is_mandatory=True),
    ]

    resolved = _resolve_group(drafts, [0, 1], "merged")

    assert resolved.is_mandatory is True


def test_resolve_group_is_text_verifiable_is_false_if_any_member_is_not() -> None:
    drafts = [
        _draft("draft_a", "text a", is_text_verifiable=True),
        _draft("draft_b", "text b", is_text_verifiable=False),
    ]

    resolved = _resolve_group(drafts, [0, 1], "merged")

    assert resolved.is_text_verifiable is False


def test_resolve_group_never_reuses_a_draft_id_across_groups() -> None:
    # Regression test: at REQUIREMENT_DEDUPLICATION_SIMILARITY_THRESHOLD=0.6
    # a real run produced two RequirementGroup entries from the LLM whose
    # member_indices both started at cluster position 0, and the old
    # implementation derived each group's requirement_id from
    # drafts[group_draft_indices[0]] -- giving two unrelated final
    # requirements (shop drawings vs. capabilities statement) the exact
    # same requirement_id.
    drafts = [
        _draft("draft_a", "text a"),
        _draft("draft_b", "text b"),
        _draft("draft_c", "text c"),
    ]

    first_resolved = _resolve_group(drafts, [0], "first canonical text")
    second_resolved = _resolve_group(
        drafts, [0, 1, 2], "second canonical text"
    )

    assert first_resolved.requirement_id != second_resolved.requirement_id


def test_embedding_text_excludes_lead_in_citations() -> None:
    # Two drafts sharing an identical lead-in but with genuinely
    # different specific content must not be pulled closer together
    # in embedding space just because of the shared lead-in text.
    draft = RequirementDraft(
        requirement_id="draft_a",
        text="shared lead-in ... specific condition A",
        is_mandatory=True,
        is_text_verifiable=True,
        citations=[
            TextSpan(
                document_path="tender.txt",
                quote="shared lead-in",
                start_char=0,
                end_char=14,
                citation_verified=True,
                used_for_matching=False,
            ),
            TextSpan(
                document_path="tender.txt",
                quote="specific condition A",
                start_char=100,
                end_char=120,
                citation_verified=True,
            ),
        ],
    )
    assert _embedding_text(draft) == "specific condition A"


def test_embedding_text_falls_back_to_full_text_without_citations() -> None:
    draft = RequirementDraft(
        requirement_id="draft_a",
        text="fallback text",
        is_mandatory=True,
        is_text_verifiable=True,
        citations=[],
    )
    assert _embedding_text(draft) == "fallback text"


def test_similar_vectors_are_grouped_together() -> None:
    embedding_vectors = [
        [1.0, 0.0, 0.0],
        [0.99, 0.01, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.98, 0.02],
        [0.0, 0.0, 1.0],
    ]
    clusters = _cluster_by_similarity(embedding_vectors)
    normalized_clusters = []
    for cluster in clusters:
        normalized_clusters.append(sorted(cluster))
    normalized_clusters.sort()
    assert normalized_clusters == [[0, 1], [2, 3], [4]]
