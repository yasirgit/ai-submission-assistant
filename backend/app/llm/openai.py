"""OpenAI chat-completions adapter. The API key stays on this object."""

import json

import httpx

from app.llm.errors import InvalidModelOutputError, ModelUnavailableError
from app.llm.types import LLMCompletion, TokenUsage, ToolCall
from app.tools.schemas import openai_tool_specs


class OpenAIClient:
    def __init__(self, api_key: str, model: str, timeout_seconds: float = 20.0, transport=None) -> None:
        self._api_key = api_key
        self._model = model
        self.model_name = model
        self._http = httpx.Client(
            base_url="https://api.openai.com/v1",
            timeout=timeout_seconds,
            transport=transport,
        )

    def __repr__(self) -> str:
        return f"OpenAIClient(model={self._model})"

    def complete(self, system: str, user: str) -> LLMCompletion:
        try:
            response = self._http.post(
                "/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "temperature": 0,
                    "tools": openai_tool_specs(),
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
            )
        except httpx.TimeoutException as exc:
            raise ModelUnavailableError("timeout") from exc
        except httpx.HTTPError as exc:
            raise ModelUnavailableError("request failed") from exc
        if response.status_code >= 400:
            raise ModelUnavailableError(f"status {response.status_code}")
        try:
            body = response.json()
            message = body["choices"][0]["message"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise InvalidModelOutputError("Provider response had no message") from exc
        usage = _usage(body.get("usage") or {})
        tool_call = _tool_call(message.get("tool_calls") or [])
        if tool_call is not None:
            content = message.get("content") or ""
            return LLMCompletion(
                content=content if isinstance(content, str) else "",
                model=self._model,
                token_usage=usage,
                tool_call=tool_call,
            )
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise InvalidModelOutputError("Provider response had no message content")
        return LLMCompletion(content=content, model=self._model, token_usage=usage)


def _usage(usage_body: dict) -> TokenUsage | None:
    if "prompt_tokens" not in usage_body or "completion_tokens" not in usage_body:
        return None
    return TokenUsage(int(usage_body["prompt_tokens"]), int(usage_body["completion_tokens"]))


def _tool_call(raw_calls: list) -> ToolCall | None:
    if not raw_calls:
        return None
    try:
        function = raw_calls[0]["function"]
        name = function["name"]
        raw_args = function.get("arguments") or "{}"
    except (KeyError, TypeError) as exc:
        raise InvalidModelOutputError("Provider tool call was incomplete") from exc
    if isinstance(raw_args, str):
        try:
            arguments = json.loads(raw_args)
        except json.JSONDecodeError as exc:
            raise InvalidModelOutputError("Tool arguments were not valid JSON") from exc
    elif isinstance(raw_args, dict):
        arguments = raw_args
    else:
        raise InvalidModelOutputError("Tool arguments were not valid JSON")
    if not isinstance(arguments, dict):
        raise InvalidModelOutputError("Tool arguments were not an object")
    return ToolCall(name=name, arguments=arguments)
