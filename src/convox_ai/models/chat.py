from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel

from convox_ai.settings import Settings

def parse_spec(spec: str) -> tuple[str, str]:
    """'ollama:qwen3.5:9b' -> ('ollama', 'qwen3.5:9b'). Only the first ':' separates."""
    provider, sep, name = spec.partition(":")
    if not sep or not provider or not name:
        raise ValueError(f"model spec must look like 'provider:model', got {spec!r}")
    return provider, name

def build_chat_model(spec: str, settings: Settings) -> BaseChatModel:
    provider, name = parse_spec(spec)
    m = settings.models

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=name,
            base_url=m.ollama_base_url,
            temperature=m.temperature,
            num_predict=m.max_output_tokens,
            reasoning=m.ollama_reasoning,
            keep_alive="30m",  # keep the model loaded between requests
            client_kwargs={"timeout": m.request_timeout_s},
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        if settings.anthropic_api_key is None:
            raise ValueError("CONVOX_AI_ANTHROPIC_API_KEY is required for anthropic models")
        return ChatAnthropic(
            model=name,
            anthropic_api_key=settings.anthropic_api_key,
            temperature=m.temperature,
            max_tokens=m.max_output_tokens,
            default_request_timeout=m.request_timeout_s,
            max_retries=2,
        )

    raise ValueError(f"unknown model provider {provider!r} in {spec!r}")


@dataclass(frozen=True)
class ChatModels:
    fast: BaseChatModel  # query rewriting, flags, summaries
    reply: BaseChatModel  # writing the answer


def build_chat_models(settings: Settings) -> ChatModels:
    return ChatModels(
        fast=build_chat_model(settings.models.fast, settings),
        reply=build_chat_model(settings.models.reply, settings),
    )