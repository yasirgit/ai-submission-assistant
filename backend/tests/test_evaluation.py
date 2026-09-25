"""The golden set is scored by python -m app.evaluation, not by this file."""

from app.evaluation.cases import CASES
from app.evaluation.score import exit_code, judge_analysis, judge_retrieval


def test_dataset_has_at_least_twenty_cases() -> None:
    assert len(CASES) >= 20
    assert any(case.gate == "soft" for case in CASES)
    assert any(case.forbid_phrases for case in CASES)


def test_soft_retrieval_miss_does_not_fail_the_process() -> None:
    case = next(item for item in CASES if item.id == "lexical-electric-utility")
    missed = judge_retrieval(case, [])
    assert missed.passed is False
    assert exit_code([missed]) == 0


def test_hard_case_failure_exits_nonzero() -> None:
    case = next(item for item in CASES if item.id == "harbor-cyber-conflict")
    failed = judge_analysis(
        case,
        chunk_ids=[],
        flags=[],
        missing=[],
        summary="",
        tools=[],
        outcome="COMPLETE",
        latency_ms=1,
        prompt_tokens=1,
    )
    assert failed.passed is False
    assert exit_code([failed]) == 1
