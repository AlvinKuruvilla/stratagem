"""LLM factory for local OpenAI-compatible servers (LMStudio, Ollama, vLLM)."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI


def create_llm(
    model: str = "got-oss:20b",
    base_url: str = "http://localhost:1234/v1",
    temperature: float = 0.0,
    **kwargs,
) -> BaseChatModel:
    """Create a ChatOpenAI instance pointed at a local inference server.

    Works with LMStudio, Ollama, vLLM, or any OpenAI-compatible endpoint.
    The api_key defaults to "lm-studio" since LMStudio does not validate keys.
    """
    return ChatOpenAI(
        model=model,
        base_url=base_url,
        temperature=temperature,
        api_key=kwargs.pop("api_key", "lm-studio"),
        **kwargs,
    )
