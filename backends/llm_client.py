from collections.abc import Callable
from functools import lru_cache
from typing import TypedDict, TypeVar, cast

from langchain_core.language_models import LanguageModelInput
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr

from backends.retry import build_retry_decorator
from config import (
    LANGUAGE_MODEL_RETRY_ATTEMPT_COUNT,
    LANGUAGE_MODEL_RETRY_WAIT_MAXIMUM_SECONDS,
    LANGUAGE_MODEL_RETRY_WAIT_MINIMUM_SECONDS,
    LANGUAGE_MODEL_TEMPERATURE,
    LanguageModelProvider,
    settings,
)
from logging_config import get_logger


StructuredSchema = TypeVar("StructuredSchema", bound=BaseModel)

logger = get_logger(__name__)


class ChatTemplateKwargs(TypedDict):
    enable_thinking: bool


class OpenAICompatibleExtraBody(TypedDict):
    chat_template_kwargs: ChatTemplateKwargs


@lru_cache(maxsize=8)
def _build_openai_compatible_chat_model(
    temperature: float,
    seed: int | None,
    disable_thinking: bool,
) -> BaseChatModel:
    logger.info(
        "Building chat model %s at %s (temperature=%s, seed=%s, "
        "disable_thinking=%s)",
        settings.language_model_name,
        settings.language_model_base_url,
        temperature,
        seed,
        disable_thinking,
    )
    extra_body: OpenAICompatibleExtraBody | None = None
    if disable_thinking:
        extra_body = {"chat_template_kwargs": {"enable_thinking": False}}
    return ChatOpenAI(
        base_url=settings.language_model_base_url,
        api_key=SecretStr(settings.language_model_api_key),
        model=settings.language_model_name,
        temperature=temperature,
        seed=seed,
        extra_body=extra_body,
    )


@lru_cache(maxsize=8)
def _build_google_genai_chat_model(
    temperature: float,
    seed: int | None,
    disable_thinking: bool,
) -> BaseChatModel:
    del seed, disable_thinking
    logger.info(
        "Building Gemini chat model %s (temperature=%s)",
        settings.language_model_name,
        temperature,
    )
    return ChatGoogleGenerativeAI(
        model=settings.language_model_name,
        google_api_key=SecretStr(settings.language_model_api_key),
        temperature=temperature,
    )


LANGUAGE_MODEL_FACTORIES: dict[
    LanguageModelProvider, Callable[[float, int | None, bool], BaseChatModel]
] = {
    "openai_compatible": _build_openai_compatible_chat_model,
    "google_genai": _build_google_genai_chat_model,
}


def get_chat_model(
    temperature: float = LANGUAGE_MODEL_TEMPERATURE,
) -> BaseChatModel:
    factory = LANGUAGE_MODEL_FACTORIES[settings.language_model_provider]
    return factory(
        temperature,
        settings.language_model_seed,
        settings.language_model_disable_thinking,
    )


def get_structured_chat_model(
    output_schema: type[StructuredSchema],
) -> Runnable[LanguageModelInput, StructuredSchema]:
    chat_model = get_chat_model()
    structured_model = chat_model.with_structured_output(output_schema)
    return cast(
        Runnable[LanguageModelInput, StructuredSchema], structured_model
    )


@build_retry_decorator(
    LANGUAGE_MODEL_RETRY_ATTEMPT_COUNT,
    LANGUAGE_MODEL_RETRY_WAIT_MINIMUM_SECONDS,
    LANGUAGE_MODEL_RETRY_WAIT_MAXIMUM_SECONDS,
)
def invoke_structured(
    structured_model: Runnable[LanguageModelInput, StructuredSchema],
    prompt_text: str,
) -> StructuredSchema:
    return structured_model.invoke(prompt_text)
