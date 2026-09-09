from schemas import (
    ComparisonOperator,
    ExtractedValue,
    NumericThresholdCondition,
    TextSpan,
)
from steps.conditions import compare_conditions


def _build_condition(
    field_name: str,
    operator: ComparisonOperator,
    value: float,
) -> NumericThresholdCondition:
    return NumericThresholdCondition(
        condition_type="numeric_threshold",
        field_name=field_name,
        operator=operator,
        value=value,
        unit="years",
    )


def _build_extracted_value(field_name: str, value: float) -> ExtractedValue:
    source_span = TextSpan(
        document_path="application.txt",
        quote="quote",
        start_char=0,
        end_char=5,
        citation_verified=True,
    )
    return ExtractedValue(
        value_type="numeric_threshold",
        field_name=field_name,
        value=value,
        unit="years",
        source=source_span,
    )


def test_compliant_when_value_meets_threshold() -> None:
    condition = _build_condition("experience_years", "gte", 5.0)
    extracted_values = [_build_extracted_value("experience_years", 7.0)]
    verdict_label = compare_conditions([condition], extracted_values)
    assert verdict_label is not None
    assert verdict_label.value == "compliant"


def test_non_compliant_when_value_below_threshold() -> None:
    condition = _build_condition("experience_years", "gte", 5.0)
    extracted_values = [_build_extracted_value("experience_years", 3.0)]
    verdict_label = compare_conditions([condition], extracted_values)
    assert verdict_label is not None
    assert verdict_label.value == "non_compliant"


def test_contradictory_when_values_disagree() -> None:
    condition = _build_condition("experience_years", "gte", 5.0)
    extracted_values = [
        _build_extracted_value("experience_years", 7.0),
        _build_extracted_value("experience_years", 3.0),
    ]
    verdict_label = compare_conditions([condition], extracted_values)
    assert verdict_label is not None
    assert verdict_label.value == "contradictory"


def test_none_when_no_extracted_values() -> None:
    condition = _build_condition("experience_years", "gte", 5.0)
    assert compare_conditions([condition], []) is None


def test_none_when_no_conditions() -> None:
    extracted_values = [_build_extracted_value("experience_years", 7.0)]
    assert compare_conditions([], extracted_values) is None


def test_and_combination_non_compliant_dominates_compliant() -> None:
    lower_bound = _build_condition("delivery_days", "gte", 20.0)
    upper_bound = _build_condition("delivery_days", "lte", 45.0)
    extracted_values = [_build_extracted_value("delivery_days", 60.0)]
    verdict_label = compare_conditions(
        [lower_bound, upper_bound], extracted_values
    )
    assert verdict_label is not None
    assert verdict_label.value == "non_compliant"


def test_and_combination_compliant_when_all_conditions_hold() -> None:
    lower_bound = _build_condition("delivery_days", "gte", 20.0)
    upper_bound = _build_condition("delivery_days", "lte", 45.0)
    extracted_values = [_build_extracted_value("delivery_days", 30.0)]
    verdict_label = compare_conditions(
        [lower_bound, upper_bound], extracted_values
    )
    assert verdict_label is not None
    assert verdict_label.value == "compliant"


def test_and_combination_contradictory_dominates_non_compliant() -> None:
    price_cap = _build_condition("price", "lte", 500.0)
    experience = _build_condition("experience_years", "gte", 5.0)
    extracted_values = [
        _build_extracted_value("price", 900.0),
        _build_extracted_value("experience_years", 7.0),
        _build_extracted_value("experience_years", 2.0),
    ]
    verdict_label = compare_conditions(
        [price_cap, experience], extracted_values
    )
    assert verdict_label is not None
    assert verdict_label.value == "contradictory"
