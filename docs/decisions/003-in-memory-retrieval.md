# ADR 003: In-memory retrieval, no vector database in v1

## Decision

`DocumentRetriever` is the only retrieval port. Version one ships `InMemoryRetriever`: metadata filters, then lexical overlap, then a stable top-k. A `VectorRetriever` may implement the same port later. Docker Compose does not add a vector service.

## Why

The interview problem is the pipeline (filter, top-k, untrusted context, citations), not the index product. An in-memory ranker is readable in one file and deterministic in tests. Conflicting guidelines are both returned when the query matches both.

## Alternatives

- pgvector in Postgres from day one. A good production default, extra operational surface before the entitlement and injection tests exist.
- An embedded ONNX embedding model. Better semantic recall, a large dependency, and non-obvious scores.

## Trade-off

Lexical retrieval misses paraphrases. The evaluation set will include at least one paraphrase case so that miss is visible. The permanent swap is the same port backed by pgvector on the existing Postgres, not a second database, until scale says otherwise.
