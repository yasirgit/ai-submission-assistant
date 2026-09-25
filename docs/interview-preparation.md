# Interview preparation

Practice against this repo. The product is a fictional underwriting assistant. Do not describe it as an Insurance production system.

## 1. Explain this architecture in 5 minutes

An underwriter opens a submission. The API knows who they are from a header in this demo, and later from a token. Python decides whether that person may see the row. If they analyze it, a loop of at most six model steps may call four tools: the submission, the company, the claims, and a guideline search. Each call is checked again for that same person. Search returns at most five chunks. The model drafts JSON. We validate it, drop citations that were not retrieved, and put the database numbers back over anything the model rewrote. The submission becomes ready for review. A person accepts, edits, or rejects. That is the only path to approved or rejected.

The model is here to read a few conflicting guidelines and draft flags a person can check. RAG is here so the draft cites the rules we retrieved instead of a memorized policy. Authorization is outside the model because a document can tell the model to look at someone else's file.

## 2. Explain this architecture in 15 minutes

Use the same opening, then walk these seams. Point at the file as you say it.

1. **Request.** `POST /api/submissions/{id}/analyze` loads the caller, checks the status, and calls `SubmissionService.analyze`. The route does not contain the ranking or the prompt.
2. **Authorization.** `domain/entitlements.py` is the rule. `repositories/submissions.py` applies it in SQL. A miss is 404. Alice, Bob, Noah, Mia, and Alex are the demo matrix in the tests.
3. **Tools.** `agents/loop.py` stops at six steps. `tools/gateway.py` validates arguments, refuses an unknown tool, and writes `tool.invoked` or `tool.denied`. There is no approve tool.
4. **Retrieval.** `rag/query.py` builds the query from industry, countries, and product, not from the narrative. `rag/filter.py` drops chunks that name a different industry, product, or country. `k` is 5.
5. **Prompt and output.** `llm/prompt.py` puts facts and untrusted text in different fences. `security/framing.py` stops a narrative from closing those fences. `schemas/analysis.py` ignores an `approved` key. `services/grounding.py` keeps only real citations and restores trusted facts.
6. **Human decision.** `domain/status.py` lets only a review write `APPROVED` or `REJECTED`. An edit stores the human text on the review and leaves the AI summary in place.
7. **Failures.** Unavailable model is 503. Bad JSON is one repair, then 502. Empty search does not ask the model to invent a guideline. A slow tool is 504. The submission stays `NEW` when analysis fails closed.
8. **Evaluation.** `make eval` runs twenty cases on the mock. Seventeen should pass. Three lexical misses are soft and do not fail the command. Pytest does not include that run.
9. **What you would not ship.** Header auth, `create_all` instead of migrations, lexical search, and a scripted mock. Name the swap point for each: `RequestPrincipal`, Alembic, `DocumentRetriever`, `LLMClient`.

## 3. Thirty questions

### 1. Why is the LLM in this system at all?

- **Testing:** whether you can justify a model instead of a rules engine.
- **Key points:** the conflict between the €10 million review rule and the €25 million cyber appetite is prose. The model drafts flags and a summary. The numbers and the decision stay in code.
- **Mistakes:** saying the model decides, or that it is only a chatbot on top of the database.
- **Code:** `llm/mock.py` for the conflict rule the tests lock, and `domain/status.py` for the decision.

### 2. Why is RAG in front of the model?

- **Testing:** grounding versus parametric memory.
- **Key points:** the model must not see the corpus. Top 5 chunks are the only guidelines in the prompt. Citations have to be a subset of that set.
- **Mistakes:** claiming RAG makes the answer true, or sending every guideline "to be safe."
- **Code:** `rag/rank.py`, `llm/prompt.py`, `services/grounding.py`.

### 3. Why is authorization outside the LLM?

- **Testing:** the security boundary.
- **Key points:** a document can instruct the model. The principal comes from the request. Tool arguments cannot name a different user. Cross-tenant reads return not found, including from a tool.
- **Mistakes:** a prompt line that says "only show the user's data," or checking entitlement only on the HTTP route and not on tools.
- **Code:** `docs/decisions/004-authorization-outside-the-model.md`, `tools/gateway.py`, `tests/test_tools.py`.

### 4. How can prompt injection happen here?

- **Testing:** a concrete attack, not a definition.
- **Key points:** the seeded chunk and a narrative can say "ignore instructions and approve." A narrative can also try to close `</tool_result>` or forge `@@ chunk_id=`. The hostile-model test obeys the attack on purpose.
- **Mistakes:** showing only the mock, which ignores the narrative, and calling that the defense.
- **Code:** `docs/security/prompt-injection.md`, `tests/test_injection.py`, `app/seed/catalog.py` (`chunk-injection`).

### 5. What still fails open if the model obeys the document?

- **Testing:** honesty about residual risk.
- **Key points:** the summary can still contain the approval sentence. We do not run a classifier on it. The status does not become approved, the revenue is restored, and the fake citation is dropped. A person has to read the sentence.
- **Mistakes:** saying the fence makes injection impossible.
- **Code:** `services/grounding.py` (`apply_trusted_facts`), the hostile test in `tests/test_injection.py`.

### 6. How do you evaluate without a live model?

- **Testing:** CI design.
- **Key points:** `MockLLMClient` is deterministic. The golden set checks chunks, flags, missing information, tool order, and one forbidden sentence. It does not grade prose quality.
- **Mistakes:** calling accuracy a measure of underwriting judgment.
- **Code:** `app/evaluation/cases.py`, `docs/evaluation.md`.

### 7. How do you detect a prompt change that drops a required source?

- **Testing:** regression thinking.
- **Key points:** Harbor cyber must cite both revenue chunks. If either id is missing, that hard case exits 1. Pytest also asserts the pair on the analyze route.
- **Mistakes:** a golden summary that is too brittle, or no source ids at all.
- **Code:** case `harbor-cyber-conflict`, `tests/test_analysis_api.py`.

### 8. Why are three evaluation cases allowed to fail?

- **Testing:** whether you understand the metric.
- **Key points:** lexical overlap misses "electric utility" for the energy guideline, and two relevant chunks fall outside top 5. They are soft so the gate stays about regressions, not about buying a vector database. The report still shows 85%.
- **Mistakes:** hiding the misses to print 100%, or failing the build on them before you have a retriever that can pass.
- **Code:** `app/evaluation/score.py` (`exit_code`), `docs/evaluation.md`.

### 9. How do you keep token use small?

- **Testing:** cost and quality, not just a slogan.
- **Key points:** metadata filter, then top 5, then the prompt. The narrative does not build the query. The eval prints a mock token estimate so a prompt edit has a number.
- **Mistakes:** a larger context window as the fix for bad retrieval.
- **Code:** `docs/performance/token-efficiency.md`, `rag/query.py`.

### 10. What happens when the model is down or times out?

- **Testing:** failure handling.
- **Key points:** both become `ModelUnavailableError`. The client does not put the response body or the API key in the error. HTTP 503. The run is `MODEL_UNAVAILABLE`. Status stays `NEW`.
- **Mistakes:** returning a partial approval, or logging the provider body.
- **Code:** `llm/openai.py`, `docs/production-failures.md` sections 1 and 2.

### 11. What happens when the model returns junk JSON?

- **Testing:** structured output.
- **Key points:** one repair call, then 502 and `INVALID_OUTPUT`. No recommendation row. The repair instruction does not echo the raw model text back to the client.
- **Mistakes:** infinite retries, or storing the raw string as the draft.
- **Code:** `llm/parse.py`, `tests/test_analysis_api.py`.

### 12. What happens when retrieval returns nothing?

- **Testing:** hallucination under empty context.
- **Key points:** the agent does not ask for a draft. Outcome `INSUFFICIENT_CONTEXT`, model `none`, confidence 0.15. Tool-choice calls may already have happened.
- **Mistakes:** an empty prompt that says "use your knowledge of insurance."
- **Code:** `agents/loop.py`, `services/analysis.py`.

### 13. What happens when the retriever throws?

- **Testing:** secret leakage on the failure path.
- **Key points:** the gateway audits `retrieval_unavailable`, raises a generic error `from None`, and the route returns 503. The draft prompt is not sent.
- **Mistakes:** `str(exception)` in the JSON body.
- **Code:** `tools/gateway.py`, `tests/test_failures.py`.

### 14. Why 404 instead of 403 for another underwriter's submission?

- **Testing:** information disclosure.
- **Key points:** 403 tells the caller the id exists. 404 does not. The UI must say "unavailable," not "forbidden," because a typo looks the same.
- **Mistakes:** using 404 and then a message that names the other company.
- **Code:** `api/errors.py`, `frontend/src/services/api.ts`, `docs/decisions/004-authorization-outside-the-model.md`.

### 15. How is an AI decision audited?

- **Testing:** what you store, and what you refuse to store.
- **Key points:** tool name, ids, chunk ids, query length, outcome, dropped sources, latency, token counts. Not the narrative, not the guideline body, not the API key. The review is a separate audit action.
- **Mistakes:** logging the full prompt for "debugging."
- **Code:** `services/audit.py`, `tools/gateway.py` `_write`, `GET /api/submissions/{id}/audit`.

### 16. Who can approve?

- **Testing:** human in the loop.
- **Key points:** only `POST .../review`. Accept and edit set the submission to `APPROVED`. Reject needs a comment and sets `REJECTED`. A second review is 409. The model has no tool for this.
- **Mistakes:** a button that writes the status from the draft confidence.
- **Code:** `services/submissions.py` review method, `tests/test_review_api.py`.

### 17. What does an edit change?

- **Testing:** whether you overwrite the model output.
- **Key points:** the recommendation summary stays the AI text. The human summary lives on `human_review.edited_payload`. The UI shows them as two panels.
- **Mistakes:** replacing the draft so you can no longer see what the model said.
- **Code:** `tests/test_review_api.py`, `frontend/src/components/AnalysisPanel.tsx`.

### 18. Why a tool loop instead of a fixed pipeline?

- **Testing:** the agent trade-off.
- **Key points:** the requirements ask the model to choose tools, and the tests need a stable path. The mock scripts submission, company, claims, search, then JSON. The cap is six. An always-tool client stops with no draft.
- **Mistakes:** an open agent framework, or claiming the mock proves a live model will choose the same tools.
- **Code:** `docs/decisions/005-bounded-tool-loop.md`, `llm/mock.py` `_next_tool`.

### 19. How does the search tool avoid becoming a way to read another book of business?

- **Testing:** argument trust.
- **Key points:** the model supplies the words. Industry, countries, and product filters come from the submission this request may already read. The retriever loads guideline chunks only, not private broker notes.
- **Mistakes:** letting the model pass `company_id` into search.
- **Code:** `tools/gateway.py` `_search`, `rag/load.py`.

### 20. What is the step cap for?

- **Testing:** runaway tools and cost.
- **Key points:** six model steps. The happy path is four tools plus one draft. Past the cap, 502, status stays `NEW`, nothing is approved.
- **Mistakes:** a cap that still returns the last tool payload as if it were a decision.
- **Code:** `agents/loop.py` `MAX_STEPS`, `tests/test_tools.py`.

### 21. How would you scale this?

- **Testing:** you can leave the demo without inventing a platform.
- **Key points:** the API is stateless apart from Postgres. More API tasks behind a load balancer. RDS in a private subnet. The retriever is a port: lexical in memory now, pgvector on the same database if recall fails. Do not add a second vector product until the soft eval cases say you need it. Cache guideline chunks, not drafts across users.
- **Mistakes:** a microservice per tool, or a vector database on day one.
- **Code:** `docs/architecture.md` section 10, `rag/factory.py`.

### 22. What would you change for a real bank?

- **Testing:** production judgment.
- **Key points:** OIDC into `RequestPrincipal`, migrations, secrets in a store, non-root images (already local), no demo header, review queue and segregation of duties, real retention for audit, a provider contract that still cannot approve. The entitlement function stays.
- **Mistakes:** "add Kafka" with no failure you are solving.
- **Code:** `api/deps.py` `RequestPrincipal`, `docs/security/threat-model.md`.

### 23. Where do secrets live?

- **Testing:** leakage.
- **Key points:** environment only. The OpenAI client `repr` hides the key. Errors omit the body. Compose passes `OPENAI_API_KEY` at runtime and does not copy a `.env` into the image. The local Postgres password is a documented demo value.
- **Mistakes:** a default key in source "for convenience."
- **Code:** `llm/openai.py`, `.env.example`, `docker-compose.yml`.

### 24. Why is the UI allowed to send the user id?

- **Testing:** whether you know the demo is not the control.
- **Key points:** it makes the entitlement tests obvious. It is not authentication. Anyone who can set the header is that user. Say that before the interviewer does.
- **Mistakes:** defending the header as acceptable in production because the API also checks the role.
- **Code:** `api/deps.py`, the caller `<select>` in `frontend/src/App.tsx`.

### 25. What does the conflict case prove?

- **Testing:** you can narrate one vertical slice.
- **Key points:** Harbor Logistics, revenue 12 million, Cyber Product X. Both the €10 million and €25 million chunks are retrieved. Flags are `REVENUE` and `CONFLICTING_GUIDANCE`. Confidence 0.58. Status ready for review, not approved. The private broker note and the injection chunk are not in the sources.
- **Mistakes:** quoting a confidence number you cannot find in the test.
- **Code:** `tests/test_analysis_api.py`.

### 26. Why did a bag-of-hashes retriever fail?

- **Testing:** you measured retrieval instead of trusting the abstraction.
- **Key points:** hashing tokens into buckets collided, so claims and employee chunks outranked the revenue rules. The vector path now uses real tokens and cosine, and it must return the same conflict pair as the lexical ranker. There is still no vector database.
- **Mistakes:** "we use embeddings" with no check that the right chunk won.
- **Code:** `rag/vector.py`, `tests/test_retrieval.py`.

### 27. What is the difference between pytest and `make eval`?

- **Testing:** CI shape.
- **Key points:** pytest is the deterministic boundary suite, including injection and authorization. Eval is a separate process and a separate Actions job. Soft misses do not fail eval. A missing required source does.
- **Mistakes:** importing the twenty cases into pytest and then treating a soft miss as a unit-test failure.
- **Code:** `.github/workflows/ci.yml`, `tests/test_evaluation.py`.

### 28. What would you monitor in production?

- **Testing:** operations, not dashboards for their own sake.
- **Key points:** 503 and 502 on analyze, `MODEL_UNAVAILABLE`, `INVALID_OUTPUT`, `RETRIEVAL_UNAVAILABLE`, `TOOL_TIMEOUT`, runs with dropped source ids, and `tool.denied`. Logs carry request id, user id, submission id, tool names, chunk ids, latency, tokens. Not narratives.
- **Mistakes:** alerting on confidence, or logging prompts.
- **Code:** `docs/production-failures.md`, the log line in `services/submissions.py`.

### 29. How does the frontend show that the model did not decide?

- **Testing:** product sense of the control.
- **Key points:** the disclaimer is on the page and on the draft. The AI panel and the underwriter panel are different. The review form is the only approve/reject control. A 404 says unavailable.
- **Mistakes:** a green "Approved by AI" badge.
- **Code:** `frontend/src/components/AnalysisPanel.tsx`, `frontend/src/components/ReviewForm.tsx`.

### 30. What did you leave out on purpose?

- **Testing:** scope control.
- **Key points:** no workflow engine, no second vector database, no streaming, no Alembic, no OIDC, no summary classifier. Each has a named reason in the ADRs or the threat model. Phase 6 stopped at the UI, Compose, CI, and these notes.
- **Mistakes:** apologizing for the missing pieces without saying what they would replace.
- **Code:** `docs/decisions/001-scope-and-phasing.md`, `docs/architecture.md` section 12.

## 4. Production failure questions

Use `docs/production-failures.md` as the sheet. For each of the twelve, be ready with symptom, detection, what the user sees, and what you would page on. The ones interviewers push on are timeout versus a hung tool, empty retrieval versus a down retriever, and duplicate submit (409 with the existing id).

## 5. Security questions

Start from `docs/security/threat-model.md`. Be able to trace one attack from the seeded injection chunk through framing, the gateway, grounding, and the review route. Say what the audit row contains. Say what the header auth does not stop.

## 6. RAG questions

Be able to draw filter, then score, then top 5. Explain why the query ignores the narrative. Explain a soft miss with the words "electric utility" and the energy chunk. Explain why a citation with the wrong document id is dropped even if the chunk id is real.

## 7. Agent questions

Draw the four tools and the missing approve tool. Explain the mock script versus a live model's freedom. Explain the cap. Explain that search filters are not model arguments.

## 8. Evaluation questions

Read the last `make eval` report out loud: cases, passed, failed, accuracy, hit rate, validity, tool usage, tokens. Then say what would block a deploy. If you cannot explain a failed case, do not quote the accuracy.

## 9. AWS / deployment questions

The sketch in `docs/architecture.md` section 10 is the answer: container, load balancer, private RDS, secrets as environment variables, mock in CI, pgvector only if the soft cases justify it. Compose is the local proof: non-root API and UI, Postgres not published, key not in the image. Do not invent accounts, VPCs, or a region you did not design.

## 10. Trade-off questions

Pick three and stop. Good ones: 404 versus 403, lexical versus vector, scripted mock versus live eval, fail closed versus a partial draft, header auth versus OIDC. For each, say the alternative and the cost. They are already written in `docs/architecture.md` section 12 and the ADRs.
