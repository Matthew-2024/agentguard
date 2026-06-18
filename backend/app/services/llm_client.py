from __future__ import annotations

from typing import Any, Dict, Protocol


class LLMClient(Protocol):
    def json_completion(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        ...


class MockLLMClient:
    """Deterministic placeholder so runtime prompt calls can be mocked in tests."""

    def json_completion(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        return {
            "mocked": True,
            "system_prompt_chars": len(system_prompt),
            "user_message_chars": len(user_message),
        }

