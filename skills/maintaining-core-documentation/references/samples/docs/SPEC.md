---
type: "Technical Specification"
title: "Dazbo Portfolio — Technical Specification"
description: "Behavioural contracts, pinned runtime/model locks, operational boundaries, and binary verification criteria for dazbo-portfolio."
status: "stable"
verified: { by: "human:dazbo", at: "2026-10-15T18:00:00Z" }
sources:
  - id: prd
    resource: PRD.md
    title: Dazbo Portfolio Product Requirements
---

# Technical Specification: dazbo-portfolio

## Objective & Scope

Deliver the `dazbo-portfolio` web application, conversational ADK assistant, and out-of-band content ingestion CLI fulfilling the product goals in [docs/PRD.md](PRD.md). This specification defines the canonical API/CLI contracts, pinned dependency and model locks, operational guardrails, and falsifiable acceptance assertions.

## Explicit Assumptions

1. Production runs as a single containerised origin on Google Cloud Run with Native-mode Firestore and GCS assets bucket provisioned in the same GCP project.
2. Public visitors require zero authentication; administrative ingestion runs strictly out-of-band via CLI using developer/service credentials.
3. Automated ingestion never deletes existing Firestore records automatically, preventing silent data loss when upstream feeds truncate history.

## Functional Requirements

| ID | Requirement | Input / Trigger | Expected Behaviour & Output |
| :--- | :--- | :--- | :--- |
| `FR-1` | **Unified Origin & API Namespace** | HTTP requests to `/api/*` or SPA routes | Serve JSON under `/api/*`; serve compiled assets under `/assets/*`; fall back valid non-API routes to `index.html`; reject traversal paths with `404`. |
| `FR-2` | **Hybrid SEO Metadata Injection** | Initial `GET` on SPA routes + `GET /api/seo` | Replace `<!-- __SEO_TAGS__ -->` in `index.html` with HTML-escaped `<title>`, OG tags, and JSON-LD; expose parity metadata via `/api/seo` and `/sitemap.xml`. |
| `FR-3` | **Deterministic Ingestion & Deduplication** | `uv run python -m app.tools.ingest` | Normalise URLs (strip query params/trailing slashes), assign `<platform>:<slug>` IDs, skip drafts and Dev.to posts `< 200` words, and merge URL duplicates preserving enriched fields. |
| `FR-4` | **Dry-Run Simulation Mode** | `--simulate` flag on ingestion CLI | Execute normalisation, filtering, and diff computation without writing to Firestore; print clear before/after change summary. |
| `FR-5` | **Hybrid ADK Portfolio Chat** | `POST /api/chat/stream` | Stream agent responses via SSE using bespoke `search_portfolio` for discovery/counting and managed Firestore MCP `get_document` for full body retrieval. |

## Non-Functional Requirements

- **Security**: Validate and constrain static SPA file resolution to `frontend/dist` (`os.path.abspath` containment check); escape all dynamic SEO strings with `html.escape()` and serialise JSON-LD with `json.dumps()`.
- **Rate Limiting & Cost Control**: Enforce `60 req/min` globally across `/api/*` and `5 req/min` per IP on `/api/chat/stream` via `slowapi`; exempt `/api/health` and static assets.
- **Stateless Scaling**: Keep Cloud Run instances stateless (`session_affinity` disabled, `InMemorySessionService` scoped per tab session) with `cpu_idle = true` and startup CPU boost enabled.
- **Offline Testability**: Unit test suites must pass 100% offline inside a sandbox without live GCP credentials, `.env` files, or network calls.

## Tech Stack, SDK & Model Locks

| Layer | Technology / Package | Pinned Version / Identifier | Notes |
| :--- | :--- | :--- | :--- |
| **Language** | Python | `>= 3.13` | Managed via `uv` and `pyproject.toml` |
| **Backend** | FastAPI + Pydantic | FastAPI + Pydantic v2 | Settings loaded via `pydantic-settings` |
| **Frontend** | React + TypeScript + Vite | React `19.x` | Native metadata hoisting; Axios API client |
| **Agent & AI SDK** | `google-adk`, `google-genai` | `google-genai >= 2.30.1` | Interactions API where applicable |
| **AI Models** | Gemini 4 Flash & Embeddings | `gemini-4-hydrogen`, `gemini-embedding-2` | Used for ADK chat, enrichment summaries, and planned vector search |
| **Persistence** | Firestore (Native) + GCS | Managed GCP services | Firestore MCP enabled for surgical reads |
| **Infrastructure** | Terraform + Cloud Build | Terraform `>= 1.0` | Hybrid shell (Terraform) + image deploy (Cloud Build) |

## Operational Boundaries

- **Always Do**: Run `make check` (`codespell`, `ruff`, `pyright`, offline `pytest`) after backend edits and `make ui-test` after frontend edits; normalise URLs before matching Firestore documents; keep `.env` out of Git (`.env.enc` encrypted via shared `git-crypt` key).
- **Ask First**: Modifying Firestore collection schemas or ID prefixes, introducing new dependencies in `pyproject.toml` or `package.json`, changing rate-limit thresholds, or running Terraform apply / Cloud Run deployments.
- **Never Do**: Hardcode project IDs or API keys in tracked files; downgrade pinned Gemini models; allow the ingestion CLI to auto-delete Firestore documents; swallow exceptions silently in API or ingestion paths.

## Acceptance Criteria & Verification Rubric

*(See [docs/TESTING.md](TESTING.md) for test file inventory, mock configuration, and manual `curl` procedures.)*

| ID | Falsifiable Condition | Verification Target |
| :--- | :--- | :--- |
| `B1` | Static gates (`codespell -s`, `ruff check`, `ruff format --check`, `pyright`) exit `0` | `make lint` / `make check` |
| `B2` | All backend offline unit tests pass without network or GCP credentials | `make test` |
| `B3` | Frontend component and page tests pass in non-interactive `CI=true` mode | `make ui-test` |
| `B4` | Path traversal requests (e.g. `/../../etc/passwd`) return `404` and never read outside `frontend/dist` | `tests/unit/test_spa_security.py` |
| `B5` | Dynamic SEO injection escapes HTML special characters and injects route-specific OG metadata | `tests/unit/test_seo_injection.py` |
| `B6` | URL normalisation strips query strings and trailing slashes consistently during deduplication | `tests/unit/test_url_normalisation.py` |
| `B7` | Ingestion `--simulate` performs zero Firestore mutations while printing accurate planned diffs | `tests/unit/test_ingest_pipeline.py` |
| `B8` | `6th` `/api/chat/stream` request within 60 seconds from one IP receives `HTTP 429` | `tests/unit/test_rate_limiting.py` + `curl` QA |

## Out of Scope & Open Questions

- **Out of Scope**: Multi-user authentication, visitor commenting, automated deletion of upstream-removed items, and custom web CMS forms.
- **Open Question**: Whether `search_portfolio` should merge `gemini-embedding-2` cosine similarity scores with the existing 5-tier recency/star ranking once vector indexes are provisioned.
