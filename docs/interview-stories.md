# Interview stories

These are prompts. Answer them in the first person, from the code you can open. Do not invent a timeline, a teammate, or a production incident that is not in this repo.

For each prompt, cover what you implemented, what broke, the trade-off, what you would change, and how you knew it worked.

## 1. The Harbor conflict

Open `tests/test_analysis_api.py` and analyze `sub-alice-harbor-cyber` in the UI as Alice.

Say why both revenue guidelines have to appear, why the status is ready for review, and why confidence is 0.58 rather than a high score. If you cannot point at the assertion, do not quote the number.

What broke while ranking this: a hash-bucket embedding ranked the wrong chunks above the two revenue rules. The fix is a token vocabulary and cosine in `rag/vector.py`, checked by `tests/test_retrieval.py` for both retrievers.

Trade-off: lexical search is readable and misses paraphrases. Those misses are the three soft eval cases, not a hidden failure.

You would change the guideline owner marking which rule wins, instead of asking the model to pick.

Success: the API test and the hard case `harbor-cyber-conflict` both require the two chunk ids and both flag types.

## 2. Authorization is not a prompt

Open `domain/entitlements.py` and `tests/test_authorization.py`.

Say the rule in one sentence: an underwriter sees assigned files, a manager sees the team, an admin sees all. Then show that the same miss is a 404 from the HTTP route and from `ToolGateway`, with no narrative in the body.

What broke as a design, before it was a bug: checking only the route would leave `get_company` as a second door. The gateway calls `has_visible_submission` before it loads the company.

Trade-off: 404 hides existence. The UI therefore says "unavailable," in `frontend/src/services/api.ts`.

You would change the header for OIDC and keep `RequestPrincipal`. You would not move the rule into the prompt.

Success: Alice cannot read Bob or Noah. Mia reads North. Alex reads all. A model that asks for Bob's id while analyzing Alice's file is audited as `tool.denied`.

## 3. The document that says "approved"

Open `docs/security/prompt-injection.md` and `tests/test_injection.py`.

Tell the attack first: the chunk text, the fence break with a fake `get_company`, and a model that obeys. Then the controls: counted frames, neutralized `<` and forged citation lines, schema ignoring `approved`, trusted facts copied back, no approve tool, review as the only status write.

What broke: the first frame reader found the fake `<tool_result tool_name=get_company` inside the narrative and ignored the real company tool. The loop hit the step cap. The fix walks frames by character count and does not scan inside a body.

Trade-off: the summary can still contain the sentence. Stripping the word "approved" would hide the attack from the underwriter.

You would add a review-queue check that a person saw the draft, not a classifier as the control.

Success: the hostile test keeps Harbor's revenue, drops the injection citation, and leaves the submission ready for review. The mock injection case in eval forbids the sentence in the scripted summary.

## 4. Empty search versus a down retriever

Open `agents/loop.py` and `tests/test_failures.py`.

Contrast them. Zero chunks means `INSUFFICIENT_CONTEXT`, low confidence, and no draft call. A thrown retriever means 503, a generic body, and no secret from the exception. A slow tool means 504 and status `NEW`.

What you gave up: a partial draft when search fails. A banker might want one. This slice would rather show nothing than a draft that skipped retrieval.

Success: the tests assert the status stays `NEW` or the model field is `none`, and the outage response does not contain the planted password string.

## 5. The golden set is not the unit tests

Run `make eval`. Read the failed soft cases before you mention 85%.

Say what a hard failure is: missing required chunk, wrong flags, wrong tools, invalid output, or the injection sentence in the mock summary. Say why pytest does not run the twenty cases: the suites answer different questions, and the Actions workflow keeps them in different jobs.

What you would change: a provider smoke test that is manual and does not block CI, because a live model will not match the scripted tool order.

Success: hard cases pass, soft misses stay visible, and a deleted Harbor chunk fails the eval process.

## 6. The screen does not decide

Open `frontend/src/components/AnalysisPanel.tsx` and click through Alice's Harbor file: analyze, then accept or edit.

Say what the two panels are for. The AI summary remains after an edit. The human text is on the review. The disclaimer is on both the shell and the draft.

What you would change in a bank: real login, and a rule that the reviewer is not the only person who can see the audit. You would not add a confidence threshold that auto-approves.

Success: after accept, the submission status is `APPROVED`, the recommendation status is `ACCEPTED`, and the audit action is `submission.reviewed`. Bob still cannot open the file.
