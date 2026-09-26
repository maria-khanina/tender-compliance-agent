from pydantic import BaseModel


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


class EvidenceHallucinationResult(BaseModel):
    hallucination_rate: float
    hallucinated_evidence_count: int
    total_evidence_count: int


class ContextRecallResult(BaseModel):
    recall: float
    matched_topic_count: int
    total_topic_count: int
    missed_topic_ids: list[str]


def _count_unverified(citation_verified_flags: list[bool]) -> int:
    unverified_count = 0
    for is_verified in citation_verified_flags:
        if not is_verified:
            unverified_count += 1
    return unverified_count


def compute_evidence_hallucination_rate(
    citation_verified_flags: list[bool],
) -> EvidenceHallucinationResult:
    total = len(citation_verified_flags)
    hallucinated_count = _count_unverified(citation_verified_flags)
    rate = _safe_ratio(hallucinated_count, total)
    return EvidenceHallucinationResult(
        hallucination_rate=rate,
        hallucinated_evidence_count=hallucinated_count,
        total_evidence_count=total,
    )


def _missed_topic_ids(
    true_topic_ids: list[str],
    matched_topic_ids: set[str],
) -> list[str]:
    missed = []
    for topic_id in true_topic_ids:
        if topic_id not in matched_topic_ids:
            missed.append(topic_id)
    return missed


def compute_context_recall(
    true_topic_ids: list[str],
    matched_topic_ids: set[str],
) -> ContextRecallResult:
    missed = _missed_topic_ids(true_topic_ids, matched_topic_ids)
    total = len(true_topic_ids)
    matched_count = total - len(missed)
    recall = _safe_ratio(matched_count, total)
    return ContextRecallResult(
        recall=recall,
        matched_topic_count=matched_count,
        total_topic_count=total,
        missed_topic_ids=missed,
    )
