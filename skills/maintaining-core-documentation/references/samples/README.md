# dazbo-portfolio

This is a developer portfolio site designed to showcase technical blogs, applications, and public code repositories, while serving as a practical reference implementation built with Google agentic tooling.

The portfolio platform provides:

- A React and Vite frontend served alongside a Python FastAPI backend
- A Gemini conversational assistant powered by Google ADK
- Automated multi-source ingestion of blogs, videos, and GitHub repositories
- AI-powered technical summarisation and tag enrichment
- Dynamic server-side SEO tag injection for Single Page Application (SPA) routes

It includes Terraform Infrastructure as Code (IaC) and Cloud Build pipelines for serverless deployment to Google Cloud Run, Firestore, Cloud Storage, and Secret Manager.

## Repo Metadata

- Author: Darren "Dazbo" Lester
- Repository: https://github.com/derailed-dash/dazbo-portfolio

## Table of Contents

- [Key Project Documentation](#key-project-documentation)
- [Key Links](#key-links)
- [Project Structure](#project-structure)
- [Architecture & Tech Stack — At a Glance](#architecture--tech-stack--at-a-glance)
- [Quick Start: Working With This Repo](#quick-start-working-with-this-repo)
- [Useful Commands](#useful-commands)
- [Deployment](#deployment)

## Key Project Documentation

| Document | Description |
| :--- | :--- |
| [README.md](README.md) | This file — the developer front door |
| [TODO.md](TODO.md) | Project roadmap and feature backlog |
| [docs/PRD.md](docs/PRD.md) | Product vision, target personas, metrics, and non-goals |
| [docs/SPEC.md](docs/SPEC.md) | Technical specification, pinned locks, boundaries, and acceptance criteria |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture, ADRs, component diagrams, and data models |
| [docs/DESIGN.md](docs/DESIGN.md) | Visual identity, design tokens, UI components, and CLI UX |
| [docs/TESTING.md](docs/TESTING.md) | Static gates, automated test suites, and manual QA verification |
| [docs/GUIDE.md](docs/GUIDE.md) | Feature walkthroughs, ingestion CLI pipeline, and contributor codebase tour |
| [deployment/README.md](deployment/README.md) | Infrastructure provisioning, secrets management, and CI/CD pipelines |
| `GEMINI.md` | Repository guidance and verification rules for AI coding agents (when present) |

## Key Links

- Read the accompanying [blog post](https://dev.to/gde/building-my-portfolio-site-in-2-days-using-gemini-cli-antigravity-conductor-and-agent-starter-3bke).
- Visit the live [portfolio site](https://darrenlester.net).

## Project Structure

```text
dazbo-portfolio/
├── app/                       # Core backend and ADK agent code
│   ├── agent.py               # Main Gemini ADK agent logic
│   ├── fast_api_app.py        # FastAPI server and SPA origin
│   ├── models/                # Pydantic schemas
│   ├── services/              # Firestore and AI enrichment services
│   └── tools/                 # Ingestion CLI and bespoke agent tools
├── .cloudbuild/               # Google Cloud Build CI/CD pipeline definitions
├── conductor/                 # Conductor project context and tracks
├── deployment/                # Infrastructure and deployment automation
│   ├── terraform/             # Terraform IaC configuration
│   └── README.md              # Deployment and CI/CD guide
├── docs/                      # Project documentation (PRD, SPEC, ARCHITECTURE, DESIGN, TESTING, GUIDE)
├── frontend/                  # React + Vite TypeScript frontend
├── notebooks/                 # Prototyping and evaluation notebooks
├── scripts/                   # Local environment and helper scripts
├── tests/                     # Automated test suites
│   ├── unit/                  # Offline unit tests
│   └── integration/           # Service and end-to-end integration tests
├── .env.template              # Sanitised environment variable template
├── .envrc                     # Optional direnv environment loader
├── GEMINI.md                  # Guidance for Gemini and coding agents
├── Makefile                   # Self-documenting project automation targets
├── pyproject.toml             # Python dependencies and static gate configuration
├── README.md                  # This file
└── TODO.md                    # High-level roadmap and backlog
```

## Architecture & Tech Stack — At a Glance

| Component / Pattern | Summary |
| :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, Glassmorphism UI |
| **Backend** | Python 3.13, FastAPI, Pydantic v2 |
| **AI / Agent** | Google ADK, Gemini 4 (`gemini-4-hydrogen`), `google-genai` SDK |
| **Persistence** | Google Firestore (Native Mode) and Cloud Storage (GCS) |
| **Infra / DevOps** | Terraform (IaC), Cloud Build (CI/CD), Docker, `uv` |
| **Unified Origin** | Single FastAPI service serving both `/api/*` endpoints and the React SPA |
| **Hybrid Agent Tooling** | Managed Firestore MCP + bespoke Python discovery and counting tools |
| **Automated Ingestion** | Out-of-band CLI pipeline harvesting GitHub, Medium, Dev.to, and manual YAML |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for architectural rationale, diagrams, and schemas, and [docs/SPEC.md](docs/SPEC.md) for pinned SDK and model locks.

## Quick Start: Working With This Repo

### Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)**: Fast Python package and virtual environment management.
- **[Google Cloud CLI (`gcloud`)](https://cloud.google.com/sdk/docs/install)**: For GCP authentication and project targeting.
- **[Terraform](https://developer.hashicorp.com/terraform/downloads)**: For provisioning cloud infrastructure.
- **[Docker](https://docs.docker.com/get-docker/)**: Optional, for building and verifying the unified container locally.
- **[GNU Make](https://www.gnu.org/software/make/)**: For running standardised development and verification targets.

### One-Time Setup

1. Create a Google Cloud project and link an active billing account.
2. Enable the required Google Cloud APIs (`run.googleapis.com`, `firestore.googleapis.com`, `aiplatform.googleapis.com`, `cloudbuild.googleapis.com`, `secretmanager.googleapis.com`, `storage.googleapis.com`, `artifactregistry.googleapis.com`, `logging.googleapis.com`, `cloudtrace.googleapis.com`).
3. Copy `.env.template` to `.env` (or unlock `.env.enc` via `git-crypt`) and configure your project values and Gemini API key.
4. Create the Native-mode Firestore database (if not provisioning via Terraform):

    ```bash
    gcloud firestore databases create --location=europe-west1 --type=firestore-native
    ```

### Per Dev Session

Source the environment setup script before starting local servers or running cloud tests:

```bash
source scripts/setup-env.sh [--noauth]
```

If using [direnv](https://direnv.net/), run `direnv allow` once at the repository root to load `.envrc` automatically.

## Useful Commands

| Command | Description |
| :--- | :--- |
| `make help` | Display all available Makefile targets |
| `make install` | Install Python and frontend dependencies |
| `make check` | Run offline static gates (`codespell`, `ruff`, `pyright`) and unit tests |
| `make test` | Run backend unit and integration tests |
| `make ui-test` | Run frontend Vitest and React Testing Library checks |
| `make local-backend` | Launch local FastAPI development server with hot reload |
| `make react-ui` | Launch Vite frontend development server with `/api` proxy |
| `make playground` | Launch local ADK Web UI for interactive agent debugging |
| `make docker-build` | Build the unified production container image |
| `make docker-run` | Run the unified container locally on `http://localhost:8080` |
| `uv run python -m app.tools.ingest --simulate` | Preview content ingestion changes without writing to Firestore |

For full CLI flags, dry-run recipes, and `manual_resources.yaml` usage, see [docs/GUIDE.md](docs/GUIDE.md).

## Deployment

Infrastructure is provisioned declaratively with Terraform (Cloud Run service shell, Firestore, GCS, IAM, and Cloud Build triggers), whilst Cloud Build compiles the unified container image and rolls out new revisions automatically on GitHub pushes.

See [deployment/README.md](deployment/README.md) for Terraform instructions, variable propagation, secrets handling, and CI/CD pipeline details.
