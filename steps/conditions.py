from collections.abc import Callable
from operator import eq, ge, gt, le, lt

from pydantic import BaseModel

from backends.llm_client import get_structured_chat_model, invoke_structured
from config import CONDITION_EXTRACTION_ENABLED
from logging_config import get_logger
from prompts import CONDITION_EXTRACTION_PROMPT
from schemas import (
    ComparisonOperator,
    ConditionSpec,
    ConditionType,
    ExtractedValue,
    Requirement,
    RequirementDraft,
    VerdictLabel,
)


ConditionChecker = Callable[
    [ConditionSpec, list[ExtractedValue]], VerdictLabel | None
]

VERDICT_COMBINATION_PRIORITY = [
    VerdictLabel.CONTRADICTORY,
    VerdictLabel.NON_COMPLIANT,
]

COMPARISON_FUNCTIONS: dict[ComparisonOperator, Callable[[float, float], bool]] = {
    "gte": ge,
    "lte": le,
    "gt": gt,
    "lt": lt,
    "eq": eq,
}

logger = get_logger(__name__)


class ExtractedNumericCondition(BaseModel):
    field_name: str
    operator: ComparisonOperator
    value: float
    unit: str | None


class ConditionExtractionResult(BaseModel):
    conditions: list[ExtractedNumericCondition]


def apply_operator(
    operator: ComparisonOperator,
    actual_value: float,
    threshold_value: float,
) -> VerdictLabel:
    comparison_function = COMPARISON_FUNCTIONS[operator]
    if comparison_function(actual_value, threshold_value):
        return VerdictLabel.COMPLIANT
    return VerdictLabel.NON_COMPLIANT


def _compare_numeric_threshold(
    condition: ConditionSpec,
    extracted_values: list[ExtractedValue],
) -> VerdictLabel | None:
    matching_values = []
    for extracted_value in extracted_values:
        if extracted_value.field_name == condition.field_name:
            matching_values.append(extracted_value.value)
    if not matching_values:
        return None
    distinct_value_count = len(set(matching_values))
    if distinct_value_count > 1:
        return VerdictLabel.CONTRADICTORY
    return apply_operator(
        condition.operator, matching_values[0], condition.value
    )


CONDITION_CHECKERS: dict[ConditionType, ConditionChecker] = {
    "numeric_threshold": _compare_numeric_threshold,
}


def compare_condition(
    condition: ConditionSpec,
    extracted_values: list[ExtractedValue],
) -> VerdictLabel | None:
    checker = CONDITION_CHECKERS[condition.condition_type]
    return checker(condition, extracted_values)


def _combine_verdict_labels(
    results: list[VerdictLabel | None],
) -> VerdictLabel | None:
    for priority_label in VERDICT_COMBINATION_PRIORITY:
        if priority_label in results:
            return priority_label
    if None in results:
        return None
    return VerdictLabel.COMPLIANT


def compare_conditions(
    conditions: list[ConditionSpec],
    extracted_values: list[ExtractedValue],
) -> VerdictLabel | None:
    if not conditions:
        return None
    results = []
    for condition in conditions:
        results.append(compare_condition(condition, extracted_values))
    return _combine_verdict_labels(results)


def _build_condition_spec(
    extracted: ExtractedNumericCondition,
) -> ConditionSpec:
    return ConditionSpec(
        condition_type="numeric_threshold",
        field_name=extracted.field_name,
        operator=extracted.operator,
        value=extracted.value,
        unit=extracted.unit,
    )


def _extract_conditions_from_text(text: str) -> list[ConditionSpec]:
    structured_model = get_structured_chat_model(
        ConditionExtractionResult
    )
    prompt_text = CONDITION_EXTRACTION_PROMPT.format(
        requirement_text=text
    )
    result = invoke_structured(structured_model, prompt_text)
    conditions = []
    for extracted in result.conditions:
        conditions.append(_build_condition_spec(extracted))
    return conditions


def _build_requirement(draft: RequirementDraft) -> Requirement:
    conditions: list[ConditionSpec] = []
    if CONDITION_EXTRACTION_ENABLED:
        conditions = _extract_conditions_from_text(draft.text)
    return Requirement(
        requirement_id=draft.requirement_id,
        text=draft.text,
        is_mandatory=draft.is_mandatory,
        is_text_verifiable=draft.is_text_verifiable,
        citations=draft.citations,
        conditions=conditions,
    )


def _count_with_conditions(requirements: list[Requirement]) -> int:
    count = 0
    for requirement in requirements:
        if requirement.conditions:
            count += 1
    return count


def extract_conditions(
    drafts: list[RequirementDraft],
) -> list[Requirement]:
    requirements = []
    for draft in drafts:
        requirements.append(_build_requirement(draft))
    condition_count = _count_with_conditions(requirements)
    logger.info(
        "Extracted checkable condition(s) for %d out of %d requirements",
        condition_count,
        len(requirements),
    )
    return requirements
