from collections.abc import Callable
import re
from typing import TypeVar

from tenacity import RetryCallState, retry, stop_after_attempt, wait_exponential

from logging_config import log_retry_attempt


ReturnType = TypeVar("ReturnType")

_RETRY_DELAY_PATTERN = re.compile(r"retryDelay['\"]:\s*['\"](\d+(?:\.\d+)?)s")


def _suggested_retry_delay_seconds(exception: BaseException) -> float | None:
    match = _RETRY_DELAY_PATTERN.search(str(exception))
    if match is None:
        return None
    return float(match.group(1))


def _build_wait_function(
    wait_minimum_seconds: float,
    wait_maximum_seconds: float,
) -> Callable[[RetryCallState], float]:
    exponential_wait = wait_exponential(
        min=wait_minimum_seconds, max=wait_maximum_seconds
    )

    def wait_function(retry_state: RetryCallState) -> float:
        if retry_state.outcome is not None:
            exception = retry_state.outcome.exception()
            if exception is not None:
                suggested_delay = _suggested_retry_delay_seconds(exception)
                if suggested_delay is not None:
                    return suggested_delay
        return exponential_wait(retry_state)

    return wait_function


def build_retry_decorator(
    attempt_count: int,
    wait_minimum_seconds: float,
    wait_maximum_seconds: float,
) -> Callable[[Callable[..., ReturnType]], Callable[..., ReturnType]]:
    return retry(
        stop=stop_after_attempt(attempt_count),
        wait=_build_wait_function(wait_minimum_seconds, wait_maximum_seconds),
        before_sleep=log_retry_attempt,
        reraise=True,
    )
