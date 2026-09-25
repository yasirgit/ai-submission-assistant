# ADR 002: LLMClient, mock by default

## Decision

Business logic depends on an `LLMClient` interface. `MockLLMClient` is the default and the only client used in tests. A provider adapter is constructed only when `LLM_PROVIDER` and an API key are set. Keys stay in the environment.

## Why

The suite must be deterministic and must run in CI without a paid API. Interview discussion still needs a real adapter shape so the mock is not a dead end.

## Alternatives

- Call the provider SDK from the agent. Simple until the first test, then every test needs network or a patch scatter.
- Record/replay HTTP cassettes of a real model. More realistic output, brittle when prompts change, and easy to leak fixture data.

## Trade-off

The mock encodes the expected tool sequence and JSON. It will not catch a provider's formatting quirks. Those are covered by a small contract test that can be skipped when no key is present, plus the malformed-JSON failure simulation using a fake client.
