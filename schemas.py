from enum import Enum
from typing import Literal

from pydantic import BaseModel


ConditionType = Literal["numeric_threshold"]
ComparisonOperator = Literal["gte", "lte", "gt", "lt", "eq"]
MatchPrecision = Literal["precise", "fuzzy"]


class DocumentSource(str, Enum):
    REQUIREMENTS = "requirements"
    APPLICATION = "application"


class DocumentInput(BaseModel):
    path: str
    text: str


class Chunk(BaseModel):
    document_source: DocumentSource
    document_path: str
    chunk_index: int
    text: str
    start_char: int
    end_char: int


class TextSpan(BaseModel):
    document_path: str
    quote: str
    start_char: int | None
    end_char: int | None
    citation_verified: bool
    match_precision: MatchPrecision | None = None
    used_for_matching: bool = True


class EvidenceRole(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    INCONCLUSIVE = "inconclusive"


class Evidence(TextSpan):
    role: EvidenceRole


class NumericThresholdCondition(BaseModel):
    condition_type: Literal["numeric_threshold"]
    field_name: str
    operator: ComparisonOperator
    value: float
    unit: str | None


ConditionSpec = NumericThresholdCondition


class ExtractedValue(BaseModel):
    value_type: ConditionType
    field_name: str
    value: float
    unit: str | None
    source: TextSpan


class RequirementDraft(BaseModel):
    requirement_id: str
    text: str
    is_mandatory: bool
    is_text_verifiable: bool
    citations: list[TextSpan]
    applicability_condition_citation: TextSpan | None = None


class Requirement(RequirementDraft):
    conditions: list[ConditionSpec]


class VerdictLabel(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    INSUFFICIENT_INFORMATION = "insufficient_information"
    CONTRADICTORY = "contradictory"


class Verdict(BaseModel):
    requirement_id: str
    requirement_text: str
    verdict: VerdictLabel
    evidence: list[Evidence]
    reasoning: str
    condition_holds: bool


class RetrievedContextRecord(BaseModel):
    requirement_id: str
    retrieved_context: list[Chunk]


class PipelineResult(BaseModel):
    report: str
    requirements: list[Requirement]
    verdicts: list[Verdict]
    retrieved_context: list[RetrievedContextRecord]
