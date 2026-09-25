"""Rough token estimate when a provider does not report usage.

Four characters per token is a planning figure, not a billing figure.
"""


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def usage_from_text(system: str, user: str, completion: str) -> dict[str, int]:
    prompt = approx_tokens(system) + approx_tokens(user)
    completion_tokens = approx_tokens(completion)
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt + completion_tokens,
    }
