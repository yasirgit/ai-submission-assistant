"""Deterministic draft from trusted facts and retrieved excerpts.

The mock reads submission_facts and the excerpts section. It does not follow
orders that appear in the narrative or in guideline text. That is what makes
the injection tests stable without a network call.
"""

import json
import re

from app.llm.tokens import usage_from_text
from app.llm.types import LLMCompletion, TokenUsage, ToolCall
from app.security.framing import read_tool_result

_HEADER = re.compile(r"^@@ chunk_id=(\S+) document_id=(\S+) title=(.*)$", re.MULTILINE)


class MockLLMClient:
    model_name = "mock"

    def complete(self, system: str, user: str) -> LLMCompletion:
        if "<submission_facts>" not in user:
            return _tool_step(self.model_name, system, user)
        facts = _facts(user)
        excerpts = _between(user, "excerpts")
        content = json.dumps(_draft(facts, excerpts), sort_keys=True)
        usage = usage_from_text(system, user, content)
        return LLMCompletion(
            content=content,
            model=self.model_name,
            token_usage=TokenUsage(usage["prompt_tokens"], usage["completion_tokens"]),
        )


def _draft(facts: dict, excerpts: str) -> dict:
    revenue = int(facts["annual_revenue_eur"])
    employees = int(facts["employee_count"])
    claim_count = int(facts["claim_count"])
    max_claim = int(facts["max_claim_eur"])
    product = str(facts["product"])
    industry = str(facts["industry"])
    countries = [str(country) for country in facts["countries"]]
    limit = int(facts["limit_eur"])
    flags: list[dict] = []
    missing: list[str] = []

    if revenue > 25_000_000:
        flags.append(
            {
                "type": "REVENUE",
                "severity": "HIGH",
                "description": "Revenue is above €25 million.",
            }
        )
    elif revenue > 10_000_000:
        flags.append(
            {
                "type": "REVENUE",
                "severity": "MEDIUM",
                "description": "Revenue is above €10 million, so the referral threshold applies.",
            }
        )

    both_revenue_rules = "€10 million" in excerpts and "€25 million" in excerpts
    if both_revenue_rules and product == "Cyber Product X" and 10_000_000 < revenue <= 25_000_000:
        flags.append(
            {
                "type": "CONFLICTING_GUIDANCE",
                "severity": "MEDIUM",
                "description": "Retrieved guidelines disagree on the revenue band for Cyber Product X.",
            }
        )

    if industry == "Energy":
        flags.append(
            {
                "type": "INDUSTRY",
                "severity": "HIGH",
                "description": "Energy accounts require a senior underwriter.",
            }
        )
    if industry == "Healthcare":
        flags.append(
            {
                "type": "INDUSTRY",
                "severity": "MEDIUM",
                "description": "Healthcare submissions need investigation history.",
            }
        )
        missing.append("Regulatory investigations in the last five years")

    if "US" in countries:
        flags.append(
            {
                "type": "GEOGRAPHY",
                "severity": "HIGH",
                "description": "United States operations are outside this demo appetite.",
            }
        )

    if employees > 250:
        flags.append(
            {
                "type": "EMPLOYEES",
                "severity": "MEDIUM",
                "description": "Headcount is above 250.",
            }
        )
        missing.append("Name of the information security officer")
    elif employees < 25:
        flags.append(
            {
                "type": "EMPLOYEES",
                "severity": "LOW",
                "description": "Headcount is below the small-business threshold.",
            }
        )

    if max_claim >= 500_000 or claim_count >= 2:
        flags.append(
            {
                "type": "CLAIMS",
                "severity": "HIGH" if max_claim >= 500_000 else "MEDIUM",
                "description": "Prior claims need a narrative or a referral.",
            }
        )
        if claim_count >= 2:
            missing.append("Claims narrative for the last three years")

    if product == "Cyber Product X" and limit > 5_000_000:
        flags.append(
            {
                "type": "COVERAGE",
                "severity": "HIGH",
                "description": "The cyber limit is above €5 million.",
            }
        )
    if product == "Property" and industry == "Software":
        flags.append(
            {
                "type": "COVERAGE",
                "severity": "MEDIUM",
                "description": "Property cover is being requested for a software firm.",
            }
        )

    questions = [f"Please provide: {item}" for item in missing]
    if not questions:
        questions = ["Is the submission complete for a human review?"]

    confidence = 0.74
    if any(flag["type"] == "CONFLICTING_GUIDANCE" for flag in flags):
        confidence = 0.58
    if any(flag["severity"] == "HIGH" for flag in flags):
        confidence = min(confidence, 0.64)

    return {
        "summary": (
            f"Draft analysis for {facts['company_name']}. "
            f"Revenue is {revenue} EUR. Product is {product}. "
            "A human underwriter decides."
        ),
        "extracted_data": {
            "company_name": facts["company_name"],
            "industry": industry,
            "annual_revenue_eur": revenue,
            "employee_count": employees,
            "countries": countries,
            "product": product,
            "limit_eur": limit,
            "claim_count": claim_count,
            "max_claim_eur": max_claim,
        },
        "risk_flags": flags,
        "missing_information": missing,
        "follow_up_questions": questions,
        "confidence": confidence,
        "sources": _sources(excerpts),
    }


def _tool_step(model: str, system: str, user: str) -> LLMCompletion:
    call = _next_tool(user)
    content = call.name
    usage = usage_from_text(system, user, content)
    return LLMCompletion(
        content="",
        model=model,
        token_usage=TokenUsage(usage["prompt_tokens"], usage["completion_tokens"]),
        tool_call=call,
    )


def _next_tool(user: str) -> ToolCall:
    submission_id = _match(user, r"submission_id=(\S+)")
    if _tool_payload(user, "get_submission") is None:
        return ToolCall("get_submission", {"submission_id": submission_id})
    submission = _tool_payload(user, "get_submission")
    company_id = submission["company_id"]
    if _tool_payload(user, "get_company") is None:
        return ToolCall("get_company", {"company_id": company_id})
    if _tool_payload(user, "get_company_claims") is None:
        return ToolCall("get_company_claims", {"company_id": company_id})
    if _tool_payload(user, "search_underwriting_guidelines") is None:
        return ToolCall("search_underwriting_guidelines", {"query": _search_query(user)})
    raise ValueError("mock expected a draft prompt after the guideline search")


def _search_query(user: str) -> str:
    company = _tool_payload(user, "get_company") or {}
    submission = _tool_payload(user, "get_submission") or {}
    coverage = submission.get("requested_coverage") or {}
    countries = " ".join(company.get("countries") or [])
    return (
        f"{company.get('industry', '')} {countries} {coverage.get('product', '')} "
        "revenue employees claims coverage underwriting review"
    ).strip()


def _tool_payload(user: str, name: str) -> dict | None:
    return read_tool_result(user, name)


def _match(text: str, pattern: str) -> str:
    found = re.search(pattern, text)
    if found is None:
        raise ValueError(f"prompt is missing {pattern}")
    return found.group(1)


def _sources(excerpts: str) -> list[dict]:
    sources = []
    for chunk_id, document_id, title in _HEADER.findall(excerpts):
        sources.append({"document_id": document_id, "chunk_id": chunk_id, "title": title})
    return sources


def _facts(user: str) -> dict:
    raw = _between(user, "submission_facts")
    return json.loads(raw)


def _between(user: str, tag: str) -> str:
    start = user.find(f"<{tag}>")
    end = user.find(f"</{tag}>")
    if start < 0 or end < 0 or end <= start:
        raise ValueError(f"prompt is missing <{tag}>")
    return user[start + len(tag) + 2 : end]
