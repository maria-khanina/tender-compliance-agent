from unittest.mock import Mock

from backends.retry import (
    _build_wait_function,
    _suggested_retry_delay_seconds,
    build_retry_decorator,
)


def _retry_state_with_exception(exception: BaseException) -> Mock:
    retry_state = Mock()
    retry_state.outcome.exception.return_value = exception
    return retry_state


def test_suggested_retry_delay_seconds_extracts_value_from_message() -> None:
    exception = RuntimeError(
        "429 RESOURCE_EXHAUSTED. {'retryDelay': '24.21860904s'}"
    )
    assert _suggested_retry_delay_seconds(exception) == 24.21860904


def test_suggested_retry_delay_seconds_returns_none_without_pattern() -> None:
    exception = ValueError("some unrelated failure")
    assert _suggested_retry_delay_seconds(exception) is None


def test_wait_function_uses_suggested_delay_when_present() -> None:
    wait_function = _build_wait_function(
        wait_minimum_seconds=1.0, wait_maximum_seconds=65.0
    )
    exception = RuntimeError("429 RESOURCE_EXHAUSTED. {'retryDelay': '5s'}")
    retry_state = _retry_state_with_exception(exception)

    assert wait_function(retry_state) == 5.0


def test_wait_function_falls_back_to_exponential_without_suggested_delay() -> None:
    wait_function = _build_wait_function(
        wait_minimum_seconds=1.0, wait_maximum_seconds=65.0
    )
    exception = ValueError("some unrelated failure")
    retry_state = _retry_state_with_exception(exception)
    retry_state.attempt_number = 1

    assert wait_function(retry_state) == 1.0


def test_retry_decorator_succeeds_after_transient_failures() -> None:
    attempts: dict[str, int] = {"count": 0}

    @build_retry_decorator(
        attempt_count=3, wait_minimum_seconds=0.001, wait_maximum_seconds=0.002
    )
    def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise ValueError("transient failure")
        return "ok"

    assert flaky() == "ok"
    assert attempts["count"] == 2
