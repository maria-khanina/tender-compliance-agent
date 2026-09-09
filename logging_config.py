import logging

from tenacity import RetryCallState

from config import LOG_FORMAT


_retry_logger = logging.getLogger("retry")


def configure_logging(log_level: int = logging.INFO) -> None:
    logging.basicConfig(level=log_level, format=LOG_FORMAT)


def get_logger(module_name: str) -> logging.Logger:
    return logging.getLogger(module_name)


def log_retry_attempt(retry_state: RetryCallState) -> None:
    failure_reason = None
    if retry_state.outcome is not None:
        failure_reason = retry_state.outcome.exception()
    _retry_logger.warning(
        "Call failed (attempt %d), retrying: %s",
        retry_state.attempt_number,
        failure_reason,
    )
