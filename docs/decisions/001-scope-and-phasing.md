# ADR 001: One vertical slice, built in phases

## Decision

Build one underwriting-analysis path end to end, in the six phases in `requirements.md`. Stop after each phase. Do not add a workflow engine, a second vector database, or a free-form autonomous agent in version one.

## Why

The point of the project is to explain production problems: retrieval, structured output, tool authorization, injection, evaluation, and failure handling. A wide product hides those seams.

## Alternatives

- Generate the whole application in one pass. Faster to look complete, harder to review and easier to skip security boundaries.
- A larger domain (pricing, bind, documents upload pipeline). More realistic, too much surface for an interview walkthrough.

## Trade-off

Several real production pieces stay documented instead of built: OIDC, pgvector, streaming tokens, and a human queue product. Each deferred piece has a named swap point in `docs/architecture.md`.
