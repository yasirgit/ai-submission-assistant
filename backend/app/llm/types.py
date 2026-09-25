"""What the rest of the app needs from a model. Provider SDKs stay behind this."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def as_dict(self) -> dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict


@dataclass(frozen=True)
class LLMCompletion:
    content: str
    model: str
    token_usage: TokenUsage | None = None
    tool_call: ToolCall | None = None


class LLMClient(Protocol):
    model_name: str

    def complete(self, system: str, user: str) -> LLMCompletion:
        """Return raw text. The caller validates JSON."""
