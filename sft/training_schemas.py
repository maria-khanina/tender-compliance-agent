"""Shared typed structures for the verdict-model SFT/DPO data pipeline."""
from typing import Literal, TypedDict

VerdictLabel = Literal[
    "compliant", "non_compliant", "insufficient_information", "contradictory",
]
EvidenceRole = Literal["supports", "contradicts", "inconclusive"]


class EvidenceQuote(TypedDict):
    """One cited chunk backing a verdict."""

    chunk_index: int
    quote: str
    role: EvidenceRole


class VerdictCompletion(TypedDict):
    """The model's (or gold) answer for a single requirement."""

    verdict: VerdictLabel
    evidence_quotes: list[EvidenceQuote]
    reasoning: str


class TrainingRow(TypedDict):
    """One labeled prompt/completion example for SFT."""

    case: str
    variant: str
    topic_id: str
    prompt: str
    completion: VerdictCompletion


class PreferencePair(TypedDict):
    """One chosen/rejected pair for DPO."""

    case: str
    variant: str
    topic_id: str
    prompt: str
    chosen: VerdictCompletion
    rejected: VerdictCompletion


class ClassMetrics(TypedDict):
    """Precision/recall/F1 for one verdict class."""

    precision: float
    recall: float
    f1: float
    support: int


class ScoreResult(TypedDict):
    """Aggregate evaluation metrics for one model on one split."""

    accuracy: float
    macro_f1: float
    per_class: dict[VerdictLabel, ClassMetrics]
    evidence_recall: float
    evidence_recall_n: int
    failed: int
    n: int


class ChatExample(TypedDict):
    """One training/validation row rendered as a chat-completion example."""

    messages: list[dict[str, object]]
    tools: list[dict[str, object]]
    topic_id: str
    case: str
    true_verdict: VerdictLabel


class TaskEvalResult(TypedDict):
    """Verdict-accuracy metrics from one evaluation pass over a split."""

    task_accuracy: float
    macro_f1: float
    n: int


class EvalHistoryEntry(TaskEvalResult):
    """One TaskEvalResult, tagged with the training step it was taken at."""

    step: int


class DpoChatExample(TypedDict):
    """One preference pair rendered as a DPOTrainer chat-completion example."""

    prompt: list[dict[str, object]]
    chosen: list[dict[str, object]]
    rejected: list[dict[str, object]]
    tools: list[dict[str, object]]
    topic_id: str
    case: str
