"""Thin wrapper around an OpenAI-compatible chat completions endpoint.

Ollama exposes /v1/chat/completions. Qwen3.5 enables thinking by default;
we turn it off so extracts stay JSON-shaped and latency stays usable on a
4B local model.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from openai import OpenAI

from app import config

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    return OpenAI(
        base_url=config.OLLAMA_BASE_URL,
        api_key=config.LLM_API_KEY,
        timeout=config.LLM_REQUEST_TIMEOUT_SECONDS,
    )


def strip_think(text: str | None) -> str:
    if not text:
        return ""
    return _THINK_RE.sub("", text).strip()


def _message_content(message: Any) -> str:
    if message.content:
        return strip_think(message.content)
    return ""


def _message_thinking(message: Any) -> str:
    extra = getattr(message, "model_extra", {}) or {}
    for field in ("reasoning_content", "reasoning", "thinking"):
        value = getattr(message, field, None) or extra.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def chat(
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.0,
    json_mode: bool = False,
    max_tokens: int | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    client = get_client()
    kwargs: dict[str, Any] = {
        "model": config.OLLAMA_MODEL,
        "messages": messages,
        "temperature": temperature,
        "extra_body": {
            "think": False,
            "reasoning_effort": "none",
            "keep_alive": "10m",
            **({"format": "json", "options": {"num_predict": max_tokens}} if json_mode and max_tokens else {}),
        },
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    if timeout:
        kwargs["timeout"] = timeout
    response = client.chat.completions.create(**kwargs)
    message = response.choices[0].message
    return {
        "role": "assistant",
        "content": _message_content(message),
        "thinking": _message_thinking(message),
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in (message.tool_calls or [])
        ],
    }
