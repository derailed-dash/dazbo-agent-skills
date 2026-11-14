---
type: "Testing Strategy"
title: "Dazbo Portfolio — Testing & Quality Assurance"
description: "Static gates, unit and integration test inventory, CI-aware execution, and manual API verification checks for dazbo-portfolio."
status: "stable"
---

# Testing & Quality Assurance

This document defines the verification strategy, offline test isolation, test suite inventory, and manual QA procedures for `dazbo-portfolio`.

## Table of Contents

- [Static Gates & Verification Tiers](#static-gates--verification-tiers)
- [Local vs CI Execution](#local-vs-ci-execution)
- [Backend Test Suite Inventory](#backend-test-suite-inventory)
- [Frontend Testing Strategy](#frontend-testing-strategy)
- [Running Tests](#running-tests)
- [Manual QA & API Verification](#manual-qa--api-verification)

## Static Gates & Verification Tiers

`dazbo-portfolio` separates fast deterministic offline verification from cloud-authenticated integration checks:

- **Static Quality Gates (`make lint`)**: Runs `uv run codespell -s`, `uv run ruff check --diff .`, `uv run ruff format --check --diff .`, and `uv run pyright`.
- **Offline Unit Tests (`make test`)**: Exercises FastAPI routing, SEO injection, path-traversal guards, rate limiting, URL normalisation, search ranking, and ingestion dry-run logic with mocked Firestore and Gemini clients.
- **Cloud Integration & ADK Evals (`make test-all`)**: Verifies live Firestore persistence, MCP retrieval, and multi-turn ADK agent responses against a configured GCP project.
- **Frontend UI Tests (`make ui-test`)**: Runs component and route tests using Vitest and React Testing Library.

## Local vs CI Execution

- **CI Mode (`CI=true`)**: When `CI=true` is set, `app/config.py` skips loading `.env` (relying strictly on pipeline environment variables), and frontend Vitest runs in single-pass mode without interactive watch prompts.
- **Offline Fixtures (`tests/conftest.py`)**: Supplies deterministic test settings, temporary `frontend/dist/index.html` fixtures for SPA/SEO tests, and in-memory mocks for `FirestoreService` and `ContentEnrichmentService`.
- **Ingestion Simulation**: The `--simulate` CLI flag runs full connector parsing and deduplication logic locally without mutating Firestore.

## Backend Test Suite Inventory

| File / Path | Tier | Scope & Behaviours Verified |
| :--- | :--- | :--- |
| `tests/unit/test_config.py` | Unit | Validates `pydantic-settings` defaults, `.env` loading, and `CI=true` bypass logic. |
| `tests/unit/test_seo_injection.py` | Unit | Verifies `<!-- __SEO_TAGS__ -->` replacement, `html.escape()` XSS protection, JSON-LD serialisation, and `/api/seo` parity. |
| `tests/unit/test_spa_security.py` | Unit | Confirms `serve_spa` blocks traversal attempts (`/../../etc/passwd`) with `404` and falls back valid SPA routes to `index.html`. |
| `tests/unit/test_rate_limiting.py` | Unit | Validates global `60 req/min` `/api/*` limits, strict `5 req/min` `/api/chat/stream` limits (`HTTP 429`), and `/api/health` exemption. |
| `tests/unit/test_url_normalisation.py` | Unit | Verifies query-parameter and trailing-slash stripping plus `<platform>:<slug>` ID generation. |
| `tests/unit/test_search_ranking.py` | Unit | Tests `search_portfolio` tier ordering (direct ID match, recent starred repos, star fallback, blog recency) and URL deduplication. |
| `tests/unit/test_ingest_pipeline.py` | Unit | Verifies draft filtering, Dev.to `< 200`-word quickie filtering, duplicate merging, and `--simulate` non-mutation guarantees. |
| `tests/integration/test_chat_stream.py` | Integration | Exercises `/api/chat/stream` SSE streaming, ADK `InMemorySessionService`, and hybrid MCP `get_document` handover. |

## Frontend Testing Strategy

- **Stack**: React 19, TypeScript, Vite, Vitest, and React Testing Library (`frontend/src/__tests__/`).
- **Focus**: Tests validate rendered behaviour, client-side `useSeo` metadata updates, Axios `429` error handling, and responsive carousel states rather than internal component implementation details.

## Running Tests

```bash
# Full offline static gate + backend unit tests
make check

# Backend unit tests only
make test

# Backend unit + GCP integration tests (requires ADC and project env)
make test-all

# Targeted test file with verbose output
uv run pytest -v tests/unit/test_spa_security.py

# Frontend tests (single-pass in CI)
CI=true make ui-test
```

## Manual QA & API Verification

With the local backend running (`make local-backend` on port `8000`) or unified container running (`make docker-run` on port `8080`):

### 1. Health & API Check

```bash
curl -sS http://localhost:8000/api/health
curl -sS "http://localhost:8000/api/blogs?limit=3"
```

### 2. Path Traversal Rejection

```bash
curl -i "http://localhost:8000/%2e%2e/%2e%2e/etc/passwd"
```

**Expected Outcome**: `HTTP/1.1 404 Not Found`.

### 3. Chat Stream & Rate-Limit Verification

Send six rapid requests to verify streaming and `slowapi` `5 req/min` protection:

```bash
for i in 1 2 3 4 5 6; do
  curl -s -o /dev/null -w "Request $i -> HTTP %{http_code}\n" \
    -X POST "http://localhost:8000/api/chat/stream" \
    -H "Content-Type: application/json" \
    -d '{"message": "Summarise your Gemini agent blogs"}'
done
```

**Expected Outcome**: Requests 1–5 return `HTTP 200`; request 6 returns `HTTP 429`.
