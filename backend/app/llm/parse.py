"""Validate model text. One repair call, then fail closed."""

import json

from pydantic import ValidationError

from app.llm.errors import InvalidModelOutputError, ModelUnavailableError
from app.llm.tokens import usage_from_text
from app.llm.types import LLMClient
from app.schemas.analysis import AnalysisDraft


def generate_draft(client: LLMClient, system: str, user: str) -> tuple[AnalysisDraft, dict, int]:
    first = client.complete(system, user)
    return accept_or_repair(client, system, user, first)


def accept_or_repair(client: LLMClient, system: str, user: str, first) -> tuple[AnalysisDraft, dict, int]:
    usage = _usage(first.token_usage, system, user, first.content)
    try:
        return parse_draft(first.content), usage, 0
    except InvalidModelOutputError as exc:
        repair_user = (
            user
            + "\n\nThe previous response failed validation: "
            + _safe_reason(exc)
            + "\nReturn only the JSON object."
        )
        try:
            second = client.complete(system, repair_user)
        except ModelUnavailableError:
            raise
        usage = _add(usage, _usage(second.token_usage, system, repair_user, second.content))
        try:
            return parse_draft(second.content), usage, 1
        except InvalidModelOutputError as second_error:
            raise InvalidModelOutputError("Model output stayed invalid after one repair") from second_error


def parse_draft(raw: str) -> AnalysisDraft:
    try:
        payload = _extract_object(raw)
        return AnalysisDraft.model_validate(payload)
    except (InvalidModelOutputError, ValidationError) as exc:
        raise InvalidModelOutputError("Model output did not match the analysis schema") from exc


def _extract_object(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise InvalidModelOutputError("Model output did not contain a JSON object")
    try:
        value = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise InvalidModelOutputError("Model output was not valid JSON") from exc
    if not isinstance(value, dict):
        raise InvalidModelOutputError("Model output was not a JSON object")
    return value


def _usage(reported, system: str, user: str, content: str) -> dict:
    if reported is None:
        counted = usage_from_text(system, user, content)
        counted["repair_attempts"] = 0
        return counted
    data = reported.as_dict()
    data["repair_attempts"] = 0
    return data


def _add(left: dict, right: dict) -> dict:
    return {
        "prompt_tokens": left["prompt_tokens"] + right["prompt_tokens"],
        "completion_tokens": left["completion_tokens"] + right["completion_tokens"],
        "total_tokens": left["total_tokens"] + right["total_tokens"],
        "repair_attempts": 1,
    }


def _safe_reason(exc: Exception) -> str:
    text = str(exc).replace("\n", " ")
    return text[:300]
