"""Small text helpers shared by the rankers. No model and no database."""

import re

_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw in _TOKEN.findall(text.lower()):
        tokens.add(raw)
        if len(raw) > 3 and raw.endswith("s"):
            tokens.add(raw[:-1])
    return tokens


def excerpt(content: str, limit: int = 180) -> str:
    collapsed = " ".join(content.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1] + "…"
