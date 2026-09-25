# FINLEX AI Submission Assistant

A small, interview-oriented AI application. It is a **fictional** insurance underwriting assistant built for learning production AI engineering.

This is **not** a FINLEX production system. All companies, submissions, claims, and guidelines are synthetic.

The assistant drafts an underwriting analysis. It does not approve or reject a submission. The UI and API both state: **AI-generated assistance — final decision remains with the underwriter.**

## Status

**Phase 6 is in place:** a React UI for list, draft, review, and audit; `docker compose up` for the UI, API, and Postgres; GitHub Actions for Ruff, pytest, the golden set, and the UI build. Interview notes are in [docs/interview-preparation.md](docs/interview-preparation.md).

See [docs/architecture.md](docs/architecture.md).

| Phase | What it adds | Status |
| --- | --- | --- |
| 1 | Architecture, structure, README | Done |
| 2 | PostgreSQL models, repositories, REST boundaries, entitlement tests | Done |
| 3 | RAG, `LLMClient` / `MockLLMClient`, structured output | Done |
| 4 | Tools, bounded agent, authorization on every tool call | Done |
| 5 | Prompt-injection defenses, failure simulations, evaluation suite | Done |
| 6 | React UI, Docker Compose, GitHub Actions, interview docs | Done |

## What you should be able to explain

After the later phases, the codebase is meant to answer:

- Why is the LLM here, and why is RAG in front of it?
- Why is authorization outside the model?
- How can a document perform prompt injection, and what still fails open?
- How do we evaluate retrieval and structured output without a live model?
- How do we notice a prompt change that drops a required source?
- How do we keep token use small?
- What happens when the model, the database, or retrieval fails?
- How is an AI draft audited, edited, and approved by a person?
- What would change in a real banking deployment?

## Layout

```text
backend/app/
  api/            HTTP adapters only
  domain/         Enums, status rules, entitlement rules
  models/         SQLAlchemy tables
  schemas/        Pydantic API and LLM contracts
  repositories/   Persistence, entitlement-scoped reads
  services/       Use cases
  agents/         Bounded tool loop
  tools/          Tool schemas and the authorization gateway
  rag/            DocumentRetriever and chunk ranking
  llm/            LLMClient, mock, and optional provider adapter
  evaluation/     Golden cases and scorers
  security/       Authentication, redaction, untrusted-data boundaries
  config/         Environment settings
backend/tests/    Deterministic tests; mock model only
frontend/src/     React + TypeScript + Vite
docs/             Architecture, ADRs, and later security/eval write-ups
```

## Run the tests

```bash
cd backend
uv sync --extra dev
uv run pytest
uv run ruff check app tests
```

The golden set is separate from pytest:

```bash
make eval
```

That command runs `python -m app.evaluation`. It uses the mock model and the in-memory retriever. A hard-case failure exits non-zero. The three soft cases are known lexical misses and are reported without failing the command. See [docs/evaluation.md](docs/evaluation.md).

Tests use an in-memory SQLite database so they do not need Postgres or an API key. The application default `DATABASE_URL` is Postgres.

## Run the app

Docker, from the repo root:

```bash
docker compose up --build
```

The UI is at <http://localhost:8080>. The API is at <http://localhost:8000/api/health>. Postgres stays on the Compose network. The database password is the local demo value from [.env.example](.env.example). It is set in the Compose environment, not copied into an image as a secret file. `LLM_PROVIDER` defaults to `mock`. Set `OPENAI_API_KEY` in the shell only if you point `LLM_PROVIDER` at `openai`.

Without Docker, two processes:

```bash
cd backend
DATABASE_URL=sqlite:///./local.db uv run uvicorn app.main:app --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

The Vite server is at <http://localhost:5173> and proxies `/api` to port 8000. Pick a caller in the header. Alice cannot open Bob's submissions; the page says the submission is unavailable.

## What blocks a merge

GitHub Actions runs three jobs. Ruff, pytest, and the frontend build must pass. The golden-set job is separate: a hard case failure exits 1 and blocks; the three lexical misses are printed and do not fail the job. There is no type-check step beyond `tsc` inside the UI build, because the Python package does not configure a type checker.

Seeded callers, sent as `X-User-Id`:

| Id | Role | Team |
| --- | --- | --- |
| `user-alice` | Underwriter | North |
| `user-noah` | Underwriter | North |
| `user-bob` | Underwriter | South |
| `user-mia` | Manager | North |
| `user-alex` | Admin | — |

Alice cannot read Bob's or Noah's submissions. Mia can read the North team. Alex can read all.

Secrets stay in the environment. See [.env.example](.env.example). `LLM_PROVIDER=mock` is the default and needs no API key. `LLM_PROVIDER=openai` uses `OPENAI_API_KEY`.

## Engineering rules for the rest of the build

- The model is not an authorization boundary.
- Retrieved and uploaded text is untrusted data, not instructions.
- The model never sees the full guideline corpus.
- Model JSON is validated. Citations must refer to chunks that were actually retrieved.
- Tests use `MockLLMClient` and must not call an external LLM.
- Prefer a missing feature over a second abstraction that this vertical slice does not need.
