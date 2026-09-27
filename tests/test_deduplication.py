from schemas import RequirementDraft, TextSpan
from steps.deduplication import (
    _cluster_by_citation_overlap,
    _cluster_by_similarity,
    _embedding_text,
    _merge_citation_overlap_clusters,
    _resolve_group,
)


def _draft(
    requirement_id: str,
    text: str,
    is_mandatory: bool = True,
    is_text_verifiable: bool = True,
    document_path: str = "tender.txt",
    start_char: int = 0,
    end_char: int | None = None,
) -> RequirementDraft:
    return RequirementDraft(
        requirement_id=requirement_id,
        text=text,
        is_mandatory=is_mandatory,
        is_text_verifiable=is_text_verifiable,
        citations=[TextSpan(
            document_path=document_path,
            quote=text,
            start_char=start_char,
            end_char=end_char if end_char is not None else start_char + len(text),
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


def test_citation_overlap_merges_drafts_with_overlapping_spans() -> None:
    # Same physical requirement extracted twice from overlapping chunks
    # (chunk_overlap duplication) -- their citation spans overlap in the
    # source document even though the exact quoted text may differ.
    drafts = [
        _draft("draft_a", "text a", start_char=100, end_char=200),
        _draft("draft_b", "text b", start_char=150, end_char=250),
    ]

    clusters = _cluster_by_citation_overlap(drafts)

    assert sorted(clusters[0]) == [0, 1]


def test_citation_overlap_keeps_non_overlapping_spans_separate() -> None:
    drafts = [
        _draft("draft_a", "text a", start_char=100, end_char=200),
        _draft("draft_b", "text b", start_char=500, end_char=600),
    ]

    clusters = _cluster_by_citation_overlap(drafts)

    normalized_clusters = sorted(sorted(cluster) for cluster in clusters)
    assert normalized_clusters == [[0], [1]]


def test_citation_overlap_ignores_shared_lead_in_between_requirements() -> None:
    # Several genuinely different requirements can share one lead-in
    # sentence (e.g. "the Government will not enter into a contract
    # with any corporation that--" followed by unrelated conditions).
    # A shared lead-in span must never make them look like duplicates.
    shared_lead_in = TextSpan(
        document_path="tender.txt",
        quote="shared lead-in",
        start_char=0,
        end_char=20,
        citation_verified=True,
        used_for_matching=False,
    )
    drafts = [
        RequirementDraft(
            requirement_id="draft_a",
            text="shared lead-in ... condition A",
            is_mandatory=True,
            is_text_verifiable=True,
            citations=[
                shared_lead_in,
                TextSpan(
                    document_path="tender.txt", quote="condition A",
                    start_char=100, end_char=150, citation_verified=True,
                ),
            ],
        ),
        RequirementDraft(
            requirement_id="draft_b",
            text="shared lead-in ... condition B",
            is_mandatory=True,
            is_text_verifiable=True,
            citations=[
                shared_lead_in,
                TextSpan(
                    document_path="tender.txt", quote="condition B",
                    start_char=500, end_char=550, citation_verified=True,
                ),
            ],
        ),
    ]

    clusters = _cluster_by_citation_overlap(drafts)

    normalized_clusters = sorted(sorted(cluster) for cluster in clusters)
    assert normalized_clusters == [[0], [1]]


def test_citation_overlap_requires_minimum_overlap_ratio() -> None:
    # A marginal touch between two adjacent-but-distinct requirements'
    # spans must not count as the same physical mention.
    drafts = [
        _draft("draft_a", "text a", start_char=100, end_char=200),
        _draft("draft_b", "text b", start_char=195, end_char=300),
    ]

    clusters = _cluster_by_citation_overlap(drafts)

    normalized_clusters = sorted(sorted(cluster) for cluster in clusters)
    assert normalized_clusters == [[0], [1]]


def test_citation_overlap_ignores_matching_offsets_in_different_documents() -> None:
    drafts = [
        _draft(
            "draft_a", "text a", document_path="rfq.txt",
            start_char=100, end_char=200,
        ),
        _draft(
            "draft_b", "text b", document_path="attachment.txt",
            start_char=100, end_char=200,
        ),
    ]

    clusters = _cluster_by_citation_overlap(drafts)

    normalized_clusters = sorted(sorted(cluster) for cluster in clusters)
    assert normalized_clusters == [[0], [1]]


def test_merge_citation_overlap_clusters_keeps_widest_span_text() -> None:
    # The shorter span is assumed to be a chunk-boundary truncation of
    # the same physical requirement, so the wider one wins without
    # calling an LLM.
    drafts = [
        _draft("draft_a", "truncated text", start_char=150, end_char=200),
        _draft("draft_b", "the complete text", start_char=100, end_char=250),
    ]

    merged = _merge_citation_overlap_clusters(drafts, [[0, 1]])

    assert len(merged) == 1
    assert merged[0].text == "the complete text"


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
