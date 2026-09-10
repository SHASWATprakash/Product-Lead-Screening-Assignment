"""Compatibility coverage for Ollama's non-standard reasoning fields."""
from __future__ import annotations

import unittest

from app.llm_client import _message_content, _message_thinking


class _ReasoningOnlyMessage:
    content = None
    model_extra = {"reasoning_content": "<think>brief reasoning</think>{\"ready\":true}"}


class LlmClientTests(unittest.TestCase):
    def test_keeps_reasoning_separate_when_content_is_empty(self) -> None:
        self.assertEqual(_message_content(_ReasoningOnlyMessage()), "")
        self.assertEqual(_message_thinking(_ReasoningOnlyMessage()), '<think>brief reasoning</think>{"ready":true}')


if __name__ == "__main__":
    unittest.main()
