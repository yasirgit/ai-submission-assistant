"""Keep untrusted text inside the fences that wrap it.

Tool results carry a character count so a narrative cannot close the
frame early. Citation headers and angle brackets inside documents are
rewritten before they are placed in the draft prompt.
"""

import json
import re

_FAKE_HEADER = re.compile(r"(?m)^@@[ \t]*chunk_id=")


def neutralize(text: str) -> str:
    """Leave the words readable and remove the characters that close our frames."""
    flattened = text.replace("<", "&lt;")
    return _FAKE_HEADER.sub("@@ data ", flattened)


def neutralize_data(value):
    if isinstance(value, str):
        return neutralize(value)
    if isinstance(value, list):
        return [neutralize_data(item) for item in value]
    if isinstance(value, dict):
        return {str(key): neutralize_data(item) for key, item in value.items()}
    return value


def render_tool_result(name: str, payload: dict) -> str:
    body = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return f"\n<tool_result tool_name={name} chars={len(body)}>\n{body}\n</tool_result>\n"


def read_tool_result(text: str, name: str) -> dict | None:
    """Read the first real frame for this tool. Bodies are not scanned for more frames."""
    for frame_name, body in _frames(text):
        if frame_name != name:
            continue
        try:
            value = json.loads(body)
        except json.JSONDecodeError:
            return None
        if not isinstance(value, dict):
            return None
        return value
    return None


def _frames(text: str):
    pos = 0
    prefix = "<tool_result tool_name="
    while True:
        start = text.find(prefix, pos)
        if start < 0:
            return
        header_end = text.find(">", start)
        if header_end < 0:
            return
        header = text[start + len(prefix) : header_end]
        frame_name, separator, raw_count = header.partition(" chars=")
        if separator == "":
            pos = start + len(prefix)
            continue
        try:
            count = int(raw_count)
        except ValueError:
            pos = start + len(prefix)
            continue
        body_at = header_end + 1
        if text.startswith("\n", body_at):
            body_at += 1
        body = text[body_at : body_at + count]
        if len(body) != count:
            return
        yield frame_name, body
        pos = body_at + count
