# Threat model

This is a synthetic demo. The threats below are the ones the code is arranged around. It is not a bank's threat model.

The asset is a submission file: company facts, a narrative, claims, and the draft an underwriter will read. The decision to approve or reject is the consequential action. Guideline text is shared reference data and is still untrusted as instructions.

Callers are the seeded roles: an underwriter, that underwriter's manager, and an admin. The model is not a caller.

| Threat | What we do | What is still open |
| --- | --- | --- |
| Prompt injection | Fenced untrusted text, counted tool frames, schema validation, trusted-fact overwrite, human review. See [prompt-injection.md](prompt-injection.md). | The summary can repeat the injected sentence. |
| Data leakage across assignees | SQL scope on every read. A miss is 404. Company and claims tools require a visible submission for that company. | Demo auth is a header. Anyone who can set `X-User-Id` is that user. |
| Unauthorized tool use | Four-tool allow-list. Unknown tools are audited and not run. Arguments are Pydantic models with `extra=forbid`. | The model chooses the query words. Filters still come from the submission already in scope. |
| Excessive permissions | The model cannot approve, assign, or pick the caller. Admin is a role on the user row, not a tool argument. | A stolen admin header sees every submission. |
| Malicious documents | Guideline and narrative text are `UNTRUSTED`. Private broker notes are not loaded into the retriever. | A document can still waste the top-k slots or bias a live model's prose. |
| Insecure object references | Submission, company, and claims ids from the model are checked against the caller before a row is returned. | Ids that exist and are in scope are returned, which is the point of the tool. |
| Secret leakage | The provider key stays on the client object. Errors report a status code or the word `timeout`, not the response body. Health and retrieval failures do not return the underlying message. Logs store ids, tool names, latency, and token counts. | Server tracebacks can still contain a cause if a new path chains the original exception. The retrieval path raises `from None`. |

Authentication is a stand-in: `X-User-Id` loads a user. The swap point is `RequestPrincipal`. Entitlement rules do not read the header themselves.

There is no approve tool, no vector database credential in source, and no customer data. Docker hardening is Phase 6.
