# ADR 005: A bounded tool loop, not an open agent

## Decision

Submission analysis runs a loop of at most six model steps. Each step may call one allow-listed tool or return the final JSON object. The tool gateway authenticates, authorizes, validates arguments, executes, and writes an audit event. The loop cannot approve or reject a submission.

## Why

The requirements ask for an agent that chooses tools, and they also ask for deterministic tests. A short allow-list with a step cap is explainable. The mock client scripts the happy-path tool order: submission, company, claims, guideline search, final JSON.

## Alternatives

- A fixed pipeline with no model-chosen tools. Easier to test, and it would not demonstrate tool calling.
- An open agent framework with planning and memory. More machinery than this slice needs, and harder to point at in an interview.

## Trade-off

The mock's scripted path can hide a real model's bad tool choices. Evaluation records the tool trace and scores expected tool usage separately from the prose summary.
