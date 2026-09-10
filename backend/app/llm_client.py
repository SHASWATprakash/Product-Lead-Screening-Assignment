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


def chat(
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.0,
) -> dict[str, Any]:
    client = get_client()
    kwargs: dict[str, Any] = {
        "model": config.OLLAMA_MODEL,
        "messages": messages,
        "temperature": temperature,
        "extra_body": {"think": False},
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    response = client.chat.completions.create(**kwargs)
    message = response.choices[0].message
    return {
        "role": "assistant",
        "content": strip_think(message.content),
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in (message.tool_calls or [])
        ],
    }
