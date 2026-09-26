from evaluation.evidence_metrics import (
    compute_context_recall,
    compute_evidence_hallucination_rate,
)


def test_evidence_hallucination_rate() -> None:
    result = compute_evidence_hallucination_rate(
        [True, True, False, True]
    )
    assert result.hallucination_rate == 1 / 4
    assert result.hallucinated_evidence_count == 1
    assert result.total_evidence_count == 4


def test_context_recall_forward_only() -> None:
    result = compute_context_recall(
        ["topic_a", "topic_b", "topic_c"], {"topic_a", "topic_c"}
    )
    assert result.recall == 2 / 3
    assert result.missed_topic_ids == ["topic_b"]
