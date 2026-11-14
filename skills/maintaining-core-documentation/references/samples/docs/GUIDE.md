---
type: "Usage Guide"
title: "Dazbo Portfolio — Usage Guide & Codebase Walkthrough"
description: "Hands-on feature walkthroughs, ingestion CLI recipes, manual YAML schemas, and contributor codebase tour for dazbo-portfolio."
status: "stable"
---

# Usage Guide & Codebase Walkthrough

This guide covers hands-on feature walkthroughs, the out-of-band content ingestion CLI, and a contributor tour of the `dazbo-portfolio` codebase. For architectural rationale and data schemas, see [docs/ARCHITECTURE.md](ARCHITECTURE.md).

## Table of Contents

- [Overview](#overview)
- [Feature Walkthroughs](#feature-walkthroughs)
- [Content Ingestion CLI Pipeline](#content-ingestion-cli-pipeline)
- [Contributor Codebase Tour](#contributor-codebase-tour)
- [Troubleshooting](#troubleshooting)

## Overview

Once local setup is complete (see [README.md](../README.md)), `dazbo-portfolio` exposes two primary surfaces: the interactive React + FastAPI web application and the `app.tools.ingest` CLI used to populate and enrich portfolio content.

## Feature Walkthroughs

### 1. Visitor Portfolio Discovery & AI Chat Handover

1. Start both local servers (`make local-backend` on `:8000` and `make react-ui` on `:5173`), then open `http://localhost:5173`.
2. Browse the **Blogs** or **Projects** views; client-side navigation triggers `useSeo` to fetch route metadata from `/api/seo` and update document meta tags.
3. Open the AI Assistant panel and ask *"What Python or ADK articles have you published?"*.
4. Behind the scenes, the ADK agent calls `search_portfolio` for compact matching IDs and summaries. Ask a follow-up (*"Summarise the architecture details from the first article"*) to trigger the managed Firestore MCP `get_document` handover and stream the response via SSE.

### 2. Inspecting Server-Side SEO Injection

To verify pre-rendered crawler HTML locally without running the dev proxy:

```bash
make docker-build
make docker-run
curl -sS http://localhost:8080/blogs | grep -E "<title>|og:title"
```

## Content Ingestion CLI Pipeline

The ingestion CLI (`app/tools/ingest.py`) synchronises content from GitHub, Medium, Dev.to, and manual YAML definitions into Firestore.

### Running a Safe Dry Run First

Always preview changes with `--simulate` before writing to Firestore:

```bash
uv run python -m app.tools.ingest \
  --github-user <user-name> \
  --medium-user <user-name> \
  --medium-zip <path-to-posts.zip> \
  --devto-user <user-name> \
  --about-file <path-to-about.md> \
  --yaml-file manual_resources.yaml \
  --simulate
```

Omit `--simulate` when you are ready to persist updates.

### Connector Behaviour

- **GitHub Connector**: Fetches public repositories via the GitHub API.
- **Medium Connectors**: Combines the RSS feed (latest 10 articles) with a Medium export `posts.zip` (full archive history), converting HTML posts into Markdown via `markdownify`.
- **Dev.to Connector**: Fetches published articles and skips short boost/comment posts (`< 200` words).
- **About Ingest**: Updates the singleton `about` document in the `content` collection.
- **AI Enrichment**: New records without an `ai_summary` are summarised and tagged using `gemini-4-hydrogen` via `ContentEnrichmentService`.

### Manual Resources YAML Schema (`manual_resources.yaml`)

Use a local YAML file to curate standalone applications, external articles, or video talks:

```yaml
projects:
  - title: "Some External Project"
    description: "A project hosted outside GitHub."
    repo_url: "https://example.com/repo"
    tags: ["python", "cli"]
    featured: true
    metadata_only: true

applications:
  - title: "Advent of Code Walkthroughs"
    description: "Interactive site featuring Python walkthroughs for Advent of Code."
    demo_url: "https://aoc.just2good.co.uk/"
    image_url: "https://storage.googleapis.com/<project-id>-assets/aoc-walkthroughs.png"
    tags: ["python", "algorithms"]

videos:
  - title: "Agentic AI Architecture Talk"
    description: "Technical talk covering Google ADK multi-agent patterns."
    video_url: "https://www.youtube.com/watch?v=example"
    thumbnail_url: "https://storage.googleapis.com/<project-id>-assets/video-thumb.png"
    publish_date: "2026-03-24"

blogs:
  - title: "Understanding Python Decorators"
    summary: "A deep dive into how decorators work under the hood."
    date: "2026-04-01"
    platform: "External"
    url: "https://realpython.com/some-guest-post"
    metadata_only: true
```

### Static Assets & Safe Deletions

- **Uploading Thumbnails**: Upload screenshots to the public `<project-id>-assets` GCS bucket via `gcloud storage cp` and reference the public HTTPS URL in `image_url` (or attach it to an existing Firestore document in Cloud Console).
- **Deleting Obsolete Entries**: By design, `ingest.py` never deletes records automatically. Remove retired items explicitly via the **Google Cloud Console > Firestore**.

## Contributor Codebase Tour

- **HTTP & SPA Origin** (`app/fast_api_app.py`): Registers `/api/*` routers, `slowapi` rate limits, `serve_spa` path-traversal protection, and server-side SEO tag injection.
- **Agent & Hybrid Tools** (`app/agent.py`, `app/tools/`): Configures the ADK `Agent` with `gemini-4-hydrogen`, bespoke `search_portfolio`, and the Firestore MCP toolset.
- **Shared Services & Models** (`app/services/`, `app/models/`): Houses `FirestoreService[T]` generic CRUD, URL normalisation, and Pydantic schemas shared by runtime routes and `ingest.py`.
- **Frontend SPA** (`frontend/src/`): Organised into pages, `GlassCard` / carousel UI components, Axios API interceptors (`frontend/src/services/api.ts`), and `frontend/src/hooks/useSeo.ts`.

### Adding a New Content Connector

1. Create a connector module under `app/tools/connectors/` returning normalised Pydantic records (`Blog` or `Project`).
2. Register the CLI flag in `app/tools/ingest.py` and confirm `--simulate` prints clean diffs.
3. Add offline unit tests mocking external HTTP responses under `tests/unit/`.

## Troubleshooting

- **Vite `/api` calls fail locally**: Confirm `make local-backend` is running on port `8000` before starting `make react-ui` on `:5173`.
- **Firestore permission error during local ingestion**: Run `gcloud auth application-default login` and re-source `scripts/setup-env.sh`.
- **Chat returns `HTTP 429` during manual testing**: Wait 60 seconds for the in-memory `slowapi` per-minute window to reset, or restart the local backend server.
