from pydantic import BaseModel


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


class EvidenceResult(BaseModel):
    citation_verified_rate: float
    unverified_evidence_count: int
    total_evidence_count: int


class EvidenceRecallResult(BaseModel):
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


def compute_evidence_citation_verified_rate(
    citation_verified_flags: list[bool],
) -> EvidenceResult:
    total = len(citation_verified_flags)
    unverified_count = _count_unverified(citation_verified_flags)
    rate = _safe_ratio(total - unverified_count, total)
    return EvidenceResult(
        citation_verified_rate=rate,
        unverified_evidence_count=unverified_count,
        total_evidence_count=total,
    )


def _missed_topic_ids(
    expected_topic_ids: list[str],
    matched_topic_ids: set[str],
) -> list[str]:
    missed = []
    for topic_id in expected_topic_ids:
        if topic_id not in matched_topic_ids:
            missed.append(topic_id)
    return missed


def compute_evidence_recall(
    expected_topic_ids: list[str],
    matched_topic_ids: set[str],
) -> EvidenceRecallResult:
    missed = _missed_topic_ids(expected_topic_ids, matched_topic_ids)
    total = len(expected_topic_ids)
    matched_count = total - len(missed)
    recall = _safe_ratio(matched_count, total)
    return EvidenceRecallResult(
        recall=recall,
        matched_topic_count=matched_count,
        total_topic_count=total,
        missed_topic_ids=missed,
    )
