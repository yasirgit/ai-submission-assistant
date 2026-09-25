# Production failures

Each failure is detected in application code, written to the AI run and the audit log, and returned without a decision and without the underlying error text. Analysis does not set `APPROVED` or `REJECTED`.

## 1. LLM unavailable

- **Symptom.** `POST /analyze` returns 503. The submission stays `NEW`. The run outcome is `MODEL_UNAVAILABLE`.
- **Root cause.** The provider connection failed or returned an HTTP error.
- **Detection.** `OpenAIClient` raises `ModelUnavailableError` with the status code only. The body is discarded.
- **Mitigation.** The route returns a fixed sentence. The failed run is committed.
- **Permanent fix.** Retry with backoff on 429 and 503, and a second provider. Not in this slice.
- **Monitoring.** Count `MODEL_UNAVAILABLE` runs and 503s on `/analyze` by request id.

## 2. LLM timeout

- **Symptom.** Same as unavailable. The error text is `timeout`.
- **Root cause.** The HTTP client exceeded `LLM_TIMEOUT_SECONDS` (default 20).
- **Detection.** `httpx.TimeoutException` is mapped to `ModelUnavailableError("timeout")`. The exception text from the client is not returned.
- **Mitigation.** Same 503 path. No partial draft.
- **Permanent fix.** Separate connect and read timeouts, and a shorter budget for the repair call.
- **Monitoring.** Alert when timeout runs exceed a small fraction of analyze calls.

## 3. Malformed JSON

- **Symptom.** 502. Outcome `INVALID_OUTPUT`. Status stays `NEW`. No recommendation row.
- **Root cause.** The model returned text that is not the analysis schema.
- **Detection.** Pydantic validation. One repair call asks for JSON only. A second failure raises `InvalidModelOutputError`.
- **Mitigation.** The repair reason is a short fixed phrase, not the raw body. The HTTP detail does not say "approved".
- **Permanent fix.** Constrained decoding on the provider. The schema check stays either way.
- **Monitoring.** Count repair attempts and `INVALID_OUTPUT`.

## 4. Hallucinated citation

- **Symptom.** 200 with a draft. The unknown chunk id is absent from `source_references`. Confidence is at most 0.4. The audit records `dropped_source_ids`.
- **Root cause.** The model cited a chunk that was not in the retrieved set, or cited a real chunk with the wrong document id.
- **Detection.** `ground_sources` keeps a citation only when both ids match a retrieved chunk.
- **Mitigation.** The draft is still shown, with the citation removed. Status becomes `READY_FOR_REVIEW`, not `APPROVED`.
- **Permanent fix.** Keep this check. A model-side citation format does not replace it.
- **Monitoring.** Rate of runs with a non-empty `dropped_source_ids`.

## 5. Retrieval unavailable

- **Symptom.** 503. Outcome `RETRIEVAL_UNAVAILABLE`. Status stays `NEW`. The draft prompt is not sent.
- **Root cause.** The retriever raised. The message may contain a host or a credential.
- **Detection.** The gateway catches the exception, audits `retrieval_unavailable`, and raises `RetrievalUnavailableError` with `from None`.
- **Mitigation.** The HTTP body is a fixed sentence. The original message is not the response and is not the audit detail.
- **Permanent fix.** Health of the retriever as its own check, and a circuit breaker. This demo's retriever is in process.
- **Monitoring.** Count `RETRIEVAL_UNAVAILABLE` next to database 503s.

## 6. PostgreSQL unavailable

- **Symptom.** `GET /api/health` returns 503 with `database: unavailable`. Other routes fail their request. Nothing is approved.
- **Root cause.** The database connection or a query failed.
- **Detection.** The health handler runs a trivial query and maps any exception to the fixed payload.
- **Mitigation.** The response does not include the exception text. A failed analyze rolls back with the request session, so a half-written approval is not committed. Analyze only commits a failed run when the route catches the error and returns normally.
- **Permanent fix.** Migrations, a private database, and a readiness probe that is separate from liveness.
- **Monitoring.** Health 503s and connection errors. Do not put the DSN in the log line.

## 7. Unauthorized user

- **Symptom.** 401 without a known `X-User-Id`. 404 for a submission the caller cannot see, including through a tool. 403 only for an assignment the role is not allowed to make.
- **Root cause.** The caller is missing, or the row is outside `can_read_submission`.
- **Detection.** The repository applies the same rule as `domain/entitlements.py`. Tool reads use that repository or `has_visible_submission` before loading a company.
- **Mitigation.** The body is `Not found` or `not_found`. It does not include the other submission's narrative.
- **Permanent fix.** Replace the header with a validated token that fills `RequestPrincipal`.
- **Monitoring.** Spikes of 401 and of `tool.denied` on one user.

## 8. Prompt injection

- **Symptom.** A document or narrative tells the model the company is approved. The draft may repeat that sentence when the model obeys. The submission does not become `APPROVED`.
- **Root cause.** The model follows untrusted text.
- **Detection.** There is no classifier. The fences, the schema, the fact overwrite, and the status rule are the detection. The golden injection case forbids the approval sentence in the mock summary. The hostile-model test allows the sentence and checks the status.
- **Mitigation.** See [security/prompt-injection.md](security/prompt-injection.md).
- **Permanent fix.** The human review stays. A summary scan would be an extra signal, not the control.
- **Monitoring.** Dropped injection-chunk citations, and review edits that throw away a draft.

## 9. Empty retrieval

- **Symptom.** 200. Outcome `INSUFFICIENT_CONTEXT`. Model is `none`. Confidence is 0.15. No guideline is invented.
- **Root cause.** The search tool returned zero chunks after metadata filters and scoring.
- **Detection.** The agent checks the search outcome and returns before the draft call.
- **Mitigation.** The draft says no guideline matched. Status still becomes `READY_FOR_REVIEW` so a person can see the gap. Tool-choice calls may already have happened.
- **Permanent fix.** A query rewrite that is still not allowed to drop the metadata filter. Do not send the corpus.
- **Monitoring.** Share of runs with this outcome. A sudden rise means the filters or the corpus changed.

## 10. Conflicting guidelines

- **Symptom.** Harbor's cyber submission cites both the €10 million review rule and the €25 million cyber appetite, with `REVENUE` and `CONFLICTING_GUIDANCE`. Confidence is 0.58. Status is `READY_FOR_REVIEW`.
- **Root cause.** Two published chunks disagree, and both rank in the top 5.
- **Detection.** The mock adds the conflict flag when both euro amounts are in the excerpts and the revenue sits in that band. A live model is asked to do the same and not to pick a winner.
- **Mitigation.** Both citations are kept. Nothing is auto-declined or auto-approved.
- **Permanent fix.** A guideline owner marks which rule wins. Until then the conflict is the honest output.
- **Monitoring.** The golden case `harbor-cyber-conflict` fails if either chunk disappears.

## 11. Duplicate submission

- **Symptom.** 409 with the existing submission id. No second row.
- **Root cause.** The same company, coverage, and normalized narrative were submitted again.
- **Detection.** A unique fingerprint column. The integrity error becomes `DuplicateSubmissionError`.
- **Mitigation.** The response names the existing id and does not create a draft.
- **Permanent fix.** Show the existing file in the UI. The constraint stays.
- **Monitoring.** 409 rate. A burst can mean a broker retry loop.

## 12. Slow tool

- **Symptom.** 504. Outcome `TOOL_TIMEOUT`. Status stays `NEW`. No recommendation.
- **Root cause.** A tool's wall time exceeded `tool_timeout_seconds` (default 2). The deadline is checked after the call returns. It does not cancel the work.
- **Detection.** `ToolGateway` compares `perf_counter` with the budget and audits `error: timeout`.
- **Mitigation.** The agent stops. The draft prompt is not sent. The HTTP detail does not include the query.
- **Permanent fix.** Cancel the retriever, and put a shorter budget on search than on a primary-key read.
- **Monitoring.** `TOOL_TIMEOUT` runs and tool latency. The audit has the tool name, not the narrative.
