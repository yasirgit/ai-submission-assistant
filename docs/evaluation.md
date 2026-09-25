# Evaluation

```bash
make eval
```

That runs `python -m app.evaluation` from `backend/`. It builds an in-memory database, seeds the synthetic book, and scores the cases in `backend/app/evaluation/cases.py` with `MockLLMClient` and the lexical retriever. It does not call a provider.

Pytest does not run this dataset. `tests/test_evaluation.py` only checks that the set has at least 20 cases and that a soft miss does not fail the process. The two suites answer different questions: pytest checks boundaries, and this command checks that a prompt or retrieval change still hits the golden expectations.

## What a case contains

Each case has an id, an input (a seeded submission, a synthetic submission, or a retrieval query), the guideline chunk ids that should come back, the risk-flag types, and the missing-information strings. Analysis cases also expect the four tool names in order. The injection case forbids the sentence "this company is approved" in the summary.

## What the report measures

The command prints case count, pass count, fail count, and accuracy, then:

- **Retrieval hit rate.** Share of cases whose expected chunk ids were all present.
- **Structured output validity.** Share of analysis cases that finished as `COMPLETE`.
- **Expected tool usage.** Share of analysis cases whose tool trace is submission, company, claims, then guideline search.
- **Mean latency** and **prompt tokens**, from the run row. The mock's token count is a stable estimate of the prompt it was given, not a provider bill.

Twenty cases are in the set. Seventeen are hard and should pass. Three are soft lexical misses: "electric utility" does not retrieve the energy guideline, Brightgrid's energy chunk falls outside top 5, and the US geography chunk falls outside top 5 for the US software case. Accuracy is therefore about 85%, and the process still exits 0.

A hard failure exits 1. That includes invalid output, a missing required chunk, a flag or missing-information mismatch, a wrong tool trace, or the injection sentence appearing in the summary.

In GitHub Actions the golden set is its own job, not a pytest file. Ruff, pytest, the frontend build, and a hard evaluation failure block a merge. The three soft misses are printed in that job and the process still exits 0, so they are a warning in the log. They are not a deployment gate and they are not a business-accuracy SLO.

## Limitations

These numbers do not say the prose is good underwriting. They say the harness still retrieves the intended chunk, emits the expected flags, and calls the expected tools. The mock's flags are rules over structured fields and the excerpts it was shown. A live model can phrase a flag differently and can choose different tools. Tool-trace score on the mock will stay perfect until the script changes. It will not catch a provider that skips the claims tool.

The soft misses are the lexical ranker's blind spot. A paraphrase with no shared token scores zero. Putting those cases in the hard gate would fail the build until a different retriever exists. They stay visible so a switch to vectors has something to beat.

Token totals are estimates on the mock path. They are comparable across prompt edits. They are not the provider's tokenizer.

The set is small and synthetic. It will not notice a guideline that was never turned into a case.
