from evaluation.evidence_metrics import (
    compute_evidence_citation_verified_rate,
    compute_evidence_recall,
)


def test_evidence_citation_verified_rate() -> None:
    result = compute_evidence_citation_verified_rate(
        [True, True, False, True]
    )
    assert result.citation_verified_rate == 3 / 4
    assert result.unverified_evidence_count == 1
    assert result.total_evidence_count == 4


def test_evidence_recall_forward_only() -> None:
    result = compute_evidence_recall(
        ["topic_a", "topic_b", "topic_c"], {"topic_a", "topic_c"}
    )
    assert result.recall == 2 / 3
    assert result.missed_topic_ids == ["topic_b"]
