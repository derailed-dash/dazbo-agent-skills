---
type: "Architecture"
title: "Dazbo Portfolio — System Architecture"
description: "Architectural design decisions (ADRs), component and runtime topology, Firestore data models, security controls, and key execution lifecycles."
status: "stable"
---

# System Architecture: dazbo-portfolio

## Table of Contents

- [Architectural Overview](#architectural-overview)
- [Design Decisions (ADRs)](#design-decisions-adrs)
- [Solution & Component Architecture](#solution--component-architecture)
- [Runtime & Cloud Topology](#runtime--cloud-topology)
- [Data Model & Persistence](#data-model--persistence)
- [Cross-Cutting Concerns](#cross-cutting-concerns)
- [Agent Integration Architecture](#agent-integration-architecture)
- [Key System Lifecycles](#key-system-lifecycles)

## Architectural Overview

`dazbo-portfolio` uses a layered, **Unified Origin Architecture** in which a single FastAPI service hosts both the `/api/*` REST/SSE backend and the compiled React SPA assets, while an out-of-band ingestion CLI shares the same domain models and Firestore service layer. For pinned package versions and acceptance criteria, see [docs/SPEC.md](SPEC.md); for CLI usage and a contributor codebase tour, see [docs/GUIDE.md](GUIDE.md).

## Design Decisions (ADRs)

| Decision | Status | Context & Rationale | Trade-offs |
| :--- | :--- | :--- | :--- |
| **Use Gemini (`gemini-4-hydrogen`) for LLM** | Accepted | Native multimodal capabilities, fast streaming latency, and large context window via Google ADK. | Managed external API dependency; mitigated via strict rate limiting. |
| **Use Google ADK for Agent Orchestration** | Accepted | Production-grade multi-turn runner, clean tool registration, and native ADK evaluation tooling. | Couples agent lifecycle to ADK runner conventions. |
| **Unified Origin & Single Container Image** | Accepted | FastAPI serves both REST APIs and built React assets, eliminating production CORS complexity and ensuring atomic deployments. | Frontend and backend release together on every container rollout. |
| **Vite Dev Proxy for Local Parity** | Accepted | Vite (`:5173`) proxies `/api` to FastAPI (`:8000`), mirroring single-origin routing without permissive backend CORS headers. | Requires running two local dev servers during UI development. |
| **Use Firestore (Native Mode) & GCS** | Accepted | Serverless schema-flexible storage for heterogeneous blogs/projects alongside public GCS hosting for media assets. | No relational joins; addressed via platform-scoped IDs and deduplication. |
| **Platform-Scoped IDs & URL Normalisation** | Accepted | `<platform>:<slug>` IDs let identically titled articles coexist across Medium and Dev.to while normalised URLs prevent duplicates. | Migration pass required when renaming legacy unprefixed documents. |
| **In-Memory Sessions & Rate Limiting** | Accepted | `InMemorySessionService` and in-memory `slowapi` counters give minimal latency without managing a Redis cluster. | Sessions and rate limits are per Cloud Run instance rather than globally shared. |
| **Hybrid Agent Tooling (MCP + Python)** | Accepted | Combines bespoke `search_portfolio` discovery/counting with managed Firestore MCP `get_document` for full Markdown reads. | Requires a small `mcp-python-sdk` schema patch for `null` optional fields. |
| **Hybrid SSR/SPA SEO Tag Injection** | Accepted | FastAPI injects route-specific OG/JSON-LD tags into `index.html` on first load while `useSeo` updates client-side navigations. | SEO map must stay aligned between server and `/api/seo`. |
| **Deploy via Cloud Run + Terraform + Cloud Build** | Accepted | Serverless scale-to-zero (`cpu_idle = true`, startup CPU boost, domain mapping without a Load Balancer) with clean infra/app separation. | Two-stage setup (Terraform shell first, Cloud Build image revisions second). |
| **Never Auto-Delete Ingested Records** | Accepted | Ingestion only creates/updates documents; obsolete items are deleted manually in Firestore to prevent accidental feed-truncation wipes. | Requires occasional manual cleanup for retired items. |

## Solution & Component Architecture

![Component Architecture](images/component-architecture.png)

*   **Web Application Layer**: The React UI (`frontend/`) communicates over `/api` HTTP/JSON and SSE with `app/fast_api_app.py`, which injects domain services (`app/dependencies.py`) and mounts the ADK agent (`app/agent.py`).
*   **CLI / Ingestion Layer**: The out-of-band ingestion CLI (`app/tools/ingest.py`) synchronises external connectors and performs AI enrichment via `ContentEnrichmentService`.
*   **Shared Service & Model Layer**: Both runtime routes and the ingestion CLI share Pydantic models (`app/models/`) and `FirestoreService[T]` (`app/services/firestore_base.py`), guaranteeing consistent schema validation and URL normalisation.

## Runtime & Cloud Topology

![Runtime and Deployment Architecture](images/runtime-deployment-architecture.png)

*   **Cloud Run Service**: Runs Uvicorn + FastAPI inside a unified container (`session_affinity` disabled for even load distribution, `cpu_idle = true` verified safe during active SSE streams, startup CPU boost enabled).
*   **Managed Google Cloud Services**: Business logic persists records in Firestore (Native Mode), media assets in public GCS buckets, and traces/logs in Cloud Logging; the ADK agent calls the managed Firestore MCP server for surgical document reads.
*   **Deployment Boundary**: Terraform provisions the service shell, IAM bindings, and build triggers, whilst Cloud Build builds and deploys container revisions. See [../deployment/README.md](../deployment/README.md) for provisioning steps and pipeline details.

## Data Model & Persistence

Data is organised into five top-level Firestore collections: `projects`, `applications`, `blogs`, `experience`, and `content` (singleton pages such as `about`).

*   **Document ID Scheme**: `<platform>:<slug>` (e.g. `medium:my-article`, `github:my-repo`), generated deterministically from platform and slugified title.
*   **URL Normalisation & Deduplication**: Strips query parameters (e.g. `?source=rss`) and trailing slashes before matching; merges duplicates by retaining the record with complete `ai_summary` and `markdown_content`.

### Blog Model Fields (`blogs` collection)

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `title` | `String` | Post title | RSS / Medium export HTML |
| `date` | `String` | Publication date (`YYYY-MM-DD`) | RSS / Medium export `time` tag |
| `url` | `String` | Normalised canonical article URL | RSS / Connector API |
| `platform` | `String` | Source platform (`Medium`, `Dev.to`, `External`) | Connector |
| `summary` | `String` | Short subtitle for list views; falls back to `ai_summary` | RSS / Subtitle |
| `ai_summary` | `String` | Concise technical summary | `ContentEnrichmentService` |
| `markdown_content` | `String` | Full post body converted to Markdown | `markdownify` HTML conversion |
| `tags` | `Array<String>` | Technical classification tags | Source tags or AI-generated |
| `is_private` | `Boolean` | Member-only / paywalled flag | Content heuristic |
| `is_manual` | `Boolean` | `true` when sourced from manual YAML | Ingestion pipeline |
| `source_platform` | `String` | Specific connector (`medium_rss`, `medium_archive`, etc.) | Ingestion pipeline |

### Content Model Fields (`content` collection)

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `title` | `String` | Page title (e.g. `About Me`) | Manual / About ingest |
| `body` | `String` | Full Markdown page body | Manual / About ingest |
| `last_updated` | `Timestamp` | Last modification timestamp | Ingestion / Manual entry |

## Cross-Cutting Concerns

*   **Configuration Management**: `app/config.py` defines a typed `pydantic-settings` `Settings` model reading injected environment variables in Cloud Run or `.env` locally (skipped when `CI=true`).
*   **Rate Limiting**: `slowapi` enforces a global `60 req/min` limit on `/api/*` and `5 req/min` per client IP on `/api/chat/stream` (exempting `/api/health` and static assets); an Axios interceptor handles `429` responses in the frontend.
*   **Path Traversal Defence**: `serve_spa` resolves requested paths relative to `frontend/dist` using `os.path.abspath`, verifies containment within the static root, and rejects out-of-bounds requests with `404`.
*   **XSS Protection**: Dynamic SEO injection escapes all interpolated fields (`title`, `description`, `url`) with `html.escape()` and serialises structured JSON-LD via `json.dumps()`.

## Agent Integration Architecture

The assistant combines **bespoke Python discovery tools** with the **managed Firestore MCP server**:

1.  **Context Efficiency**: Managed MCP `list_documents` returns full document bodies (bloating context by tens of thousands of tokens on broad queries); `search_portfolio` returns only concise metadata and IDs.
2.  **Deterministic Counting**: Counting items in Python eliminates slow LLM loops and off-by-one counting errors.
3.  **Schema Robustness**: A targeted `mcp-python-sdk` client patch prevents validation crashes when optional Firestore fields arrive as JSON `null`.
4.  **Surgical Retrieval**: Once specific IDs are selected, the agent delegates full Markdown retrieval to MCP `get_document`.

### Search Ranking Tiers (`search_portfolio`)

1.  **Direct ID Matches**: Exact document ID matches rank first.
2.  **Recent Starred GitHub Projects**: Repositories updated within 45 days with at least one star.
3.  **Star Count Fallback**: Older projects ordered by GitHub star count.
4.  **Blog Recency**: Articles ordered descending by ISO publication date.
5.  **Cross-Platform Deduplication**: Identical normalised URLs collapse to the entry with richer AI summary/Markdown content.

## Key System Lifecycles

1.  **Initial SPA Load & SEO Hydration**: Browser requests route -> FastAPI `serve_spa` validates path, replaces `<!-- __SEO_TAGS__ -->` with escaped route metadata, returns `index.html` -> React mounts and `useSeo` fetches `/api/seo` on subsequent client-side transitions.
2.  **Visitor Agent Chat**: User sends prompt -> Axios posts to `/api/chat/stream` -> `slowapi` checks `5/min` quota -> ADK Runner invokes `gemini-4-hydrogen` -> agent discovers IDs via `search_portfolio`, optionally reads full bodies via Firestore MCP `get_document`, and streams SSE chunks back to UI.
3.  **Out-of-Band Ingestion**: Developer runs `ingest.py` -> migration pass normalises IDs and merges URL duplicates -> connectors fetch GitHub/Medium/Dev.to/YAML entries -> draft & short Dev.to posts filtered -> HTML converted to Markdown and enriched via Gemini -> upserted into Firestore.
