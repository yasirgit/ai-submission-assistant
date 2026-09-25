"""Score one evaluation case. The command, not pytest, runs the dataset."""

from dataclasses import dataclass

from app.evaluation.cases import EXPECTED_TOOLS, EvalCase


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    gate: str
    passed: bool
    reasons: tuple[str, ...]
    retrieval_hit: bool
    structured_valid: bool | None
    tools_match: bool | None
    latency_ms: int | None
    prompt_tokens: int | None


def judge_analysis(
    case: EvalCase,
    *,
    chunk_ids: list[str],
    flags: list[str],
    missing: list[str],
    summary: str,
    tools: list[str],
    outcome: str,
    latency_ms: int,
    prompt_tokens: int,
) -> CaseResult:
    reasons: list[str] = []
    if outcome != "COMPLETE":
        reasons.append(f"outcome {outcome}")
    absent = [chunk_id for chunk_id in case.expected_chunks if chunk_id not in chunk_ids]
    if absent:
        reasons.append("missing chunks " + ", ".join(absent))
    if set(flags) != set(case.expected_flags):
        reasons.append(f"flags {sorted(flags)}")
    if set(missing) != set(case.expected_missing):
        reasons.append(f"missing information {missing}")
    lowered = summary.casefold()
    for phrase in case.forbid_phrases:
        if phrase.casefold() in lowered:
            reasons.append(f"forbidden phrase {phrase}")
    tools_match = list(tools) == list(EXPECTED_TOOLS)
    if not tools_match:
        reasons.append(f"tools {tools}")
    return CaseResult(
        case_id=case.id,
        gate=case.gate,
        passed=not reasons,
        reasons=tuple(reasons),
        retrieval_hit=not absent,
        structured_valid=outcome == "COMPLETE",
        tools_match=tools_match,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
    )


def judge_retrieval(case: EvalCase, chunk_ids: list[str]) -> CaseResult:
    absent = [chunk_id for chunk_id in case.expected_chunks if chunk_id not in chunk_ids]
    reasons = () if not absent else (f"missing chunks {', '.join(absent)}",)
    return CaseResult(
        case_id=case.id,
        gate=case.gate,
        passed=not reasons,
        reasons=reasons,
        retrieval_hit=not absent,
        structured_valid=None,
        tools_match=None,
        latency_ms=None,
        prompt_tokens=None,
    )


def exit_code(results: list[CaseResult]) -> int:
    if any(not result.passed and result.gate == "hard" for result in results):
        return 1
    return 0


def format_report(results: list[CaseResult]) -> str:
    total = len(results)
    passed = sum(1 for result in results if result.passed)
    failed = total - passed
    accuracy = 100.0 * passed / total if total else 0.0
    retrieval_hits = sum(1 for result in results if result.retrieval_hit)
    structured = [result.structured_valid for result in results if result.structured_valid is not None]
    tool_rows = [result.tools_match for result in results if result.tools_match is not None]
    latencies = [result.latency_ms for result in results if result.latency_ms is not None]
    tokens = [result.prompt_tokens for result in results if result.prompt_tokens is not None]
    lines = [
        "Evaluation Results",
        "------------------",
        f"Cases: {total}",
        f"Passed: {passed}",
        f"Failed: {failed}",
        f"Accuracy: {accuracy:.0f}%",
        "",
        f"Retrieval hit rate: {_percent(retrieval_hits, total)}",
        f"Structured output validity: {_percent(sum(1 for item in structured if item), len(structured))}",
        f"Expected tool usage: {_percent(sum(1 for item in tool_rows if item), len(tool_rows))}",
        f"Mean latency ms: {_mean(latencies):.0f}",
        f"Prompt tokens: {sum(tokens)}",
    ]
    failures = [result for result in results if not result.passed]
    if failures:
        lines.append("")
        lines.append("Failed cases")
        for result in failures:
            detail = "; ".join(result.reasons)
            lines.append(f"- {result.case_id} ({result.gate}): {detail}")
    return "\n".join(lines)


def _percent(hits: int, total: int) -> str:
    if total == 0:
        return "n/a"
    return f"{100.0 * hits / total:.0f}%"


def _mean(values: list[int]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
