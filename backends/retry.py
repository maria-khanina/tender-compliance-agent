from collections.abc import Callable
from typing import TypeVar

from tenacity import retry, stop_after_attempt, wait_exponential

from logging_config import log_retry_attempt


ReturnType = TypeVar("ReturnType")


def build_retry_decorator(
    attempt_count: int,
    wait_minimum_seconds: float,
    wait_maximum_seconds: float,
) -> Callable[[Callable[..., ReturnType]], Callable[..., ReturnType]]:
    return retry(
        stop=stop_after_attempt(attempt_count),
        wait=wait_exponential(
            min=wait_minimum_seconds, max=wait_maximum_seconds
        ),
        before_sleep=log_retry_attempt,
        reraise=True,
    )
