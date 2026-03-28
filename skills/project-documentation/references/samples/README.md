# dazbo-portfolio

This is a development portfolio site. Its purpose is to showcase my blogs, projects and public code repos. But this repo and associated blog is a demonstration in building applications like this using Google agentic tools.

The portfolio site has:

- React/Vite frontend
- Python backend
- Gemini Chatbot using Google ADK
- Automated ingestion of content from blogs, GitHub, etc
- AI-based content summarisation and metadata extraction
- Dynamic SEO tag injection (SSR for SPA)

In includes Terraform IaC for deployment to Google Cloud, using:

- Cloud Run for the containerised application
- Google Firestore for storing ingested content, AI summaries and metadata
- Google Cloud Storage for static assets, like website images
- Google Secret Manager for sensitive content

## Repo Metadata

- Author: Darren "Dazbo" Lester
- Repo: https://github.com/derailed-dash/dazbo-portfolio

## Table of Contents

- [Key Project Documentation](#key-project-documentation)
- [Key Links](#key-links)
- [Project Structure](#project-structure)
- [Architecture and Tech Stack - at a Glance](#architecture-and-tech-stack---at-a-glance)
- [Quick Start: Working With This Repo](#quick-start-working-with-this-repo)
- [Useful Commands](#useful-commands)
- [Ingestion Tool](#ingestion-tool)
- [Deployment](#deployment)

## Key Project Documentation

| Document | Description |
| --- | --- |
| [README.md](README.md) | This file - the developer front door |
| [TODO.md](TODO.md) | TODO list / feature backlog |
| [docs/architecture-and-walkthrough.md](docs/architecture-and-walkthrough.md) | Architecture and walkthrough, including design decisions and data models |
| [docs/DESIGN.md](docs/DESIGN.md) | UI design, visual identity, and frontend UI components |
| [docs/testing.md](docs/testing.md) | Testing docs, including descriptions of all tests |
| [deployment/README.md](deployment/README.md) | Deployment guidance, including Terraform, and CI/CD |
| [GEMINI.md](GEMINI.md) | Guidance for Gemini or other LLMs |

## Key Links

- Check out the related [blog post](https://dev.to/gde/building-my-portfolio-site-in-2-days-using-gemini-cli-antigravity-conductor-and-agent-starter-3bke).
- See the [portfolio site](https://darrenlester.net).

## Project Structure

```
dazbo-portfolio/
├── app/                       # Core agent code
│   ├── agent.py               # Main agent logic
│   ├── fast_api_app.py        # FastAPI Backend server
│   └── app_utils/             # App utilities and helpers
├── .cloudbuild/               # CI/CD pipeline configurations for Google Cloud Build
├── conductor/                 # Conductor tracks
├── deployment/                # Infrastructure and deployment scripts
│   ├── terraform/             # Terraform configuration
│   └── README.md              # Deployment documentation
├── docs/                      # Project documentation
├── frontend/                  # Frontend React application
├── notebooks/                 # Jupyter notebooks for prototyping and evaluation
├── scripts/                   # Convenience scripts, e.g. for environment setup
├── tests/                     # Unit, integration, and load tests
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── .env.template              # .env template file
├── .envrc                     # Optional auto env configuration file
├── GEMINI.md                  # Guidance for Gemini
├── Makefile                   # Development commands
├── pyproject.toml             # Project Python dependencies and configuration
├── README.md                  # This file
└── TODO.md                    # TODO list
```

## Architecture and Tech Stack - at a Glance

| Component / Pattern | Details |
| :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, Glassmorphism UI |
| **Backend** | Python 3.12, FastAPI, Pydantic v2 |
| **AI / Agent** | Google ADK, Gemini 3, `google-genai` SDK |
| **Database** | Google Firestore (Native Mode) |
| **Infra / DevOps** | Terraform (IaC), Cloud Build (CI/CD), Docker, `uv` |
| **Unified Origin** | Single FastAPI backend serving both REST API and React SPA |
| **Hybrid Agent Tooling** | Managed Firestore MCP + bespoke Python tools for discovery and ranking |
| **Serverless Foundation** | Fully managed GCP deployment via Cloud Run and Firestore |
| **Automated Ingestion** | CLI harvesting tool with AI-powered enrichment for GitHub, Medium, and Dev.to |

For a deep dive into implementation, see [docs/architecture-and-walkthrough.md](docs/architecture-and-walkthrough.md).

## Quick Start: Working With This Repo

### Prerequisites

Before you begin, ensure you have the following installed and configured:

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)**: Fast Python package and environment management.
- **[Google Cloud CLI (gcloud)](https://cloud.google.com/sdk/docs/install)**: For interacting with Google Cloud services.
- **[Terraform](https://developer.hashicorp.com/terraform/downloads)**: For infrastructure as code.
- **[Docker](https://docs.docker.com/get-docker/)**: For building and running unified container images. (It is not essential, but useful for local testing.)
- **[GNU Make](https://www.gnu.org/software/make/)**: For running automated development tasks. (Though you can always run the commands manually.)

### One-Time Setup

1. Create a Google Cloud project and attach a billing account.
2. Enable the required APIs.

    ```bash
    gcloud services enable --project=$GOOGLE_CLOUD_PROJECT \
      artifactregistry.googleapis.com \
      cloudbuild.googleapis.com \
      secretmanager.googleapis.com \
      run.googleapis.com \
      logging.googleapis.com \
      aiplatform.googleapis.com \
      serviceusage.googleapis.com \
      storage.googleapis.com \
      cloudtrace.googleapis.com \
      geminicloudassist.googleapis.com \
      firestore.googleapis.com
    ```

3. Create your API key, e.g. at https://aistudio.google.com/api-keys

4. Set up Firestore.

    ```bash
    # If NOT using Terraform
    gcloud firestore databases create --location=europe-west1 --type=firestore-native
    ```

5. (Optional) If you plan to deploy manually from your local machine using `make deploy-cloud-run`, grant your user account the `iam.serviceAccountUser` role on the application Service Account.

    ```bash
    gcloud iam service-accounts add-iam-policy-binding dazbo-portfolio-app@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
      --member="user:$(gcloud config get-value account)" \
      --role="roles/iam.serviceAccountUser"
    ```

### Per Dev Session (Once One-Time Setup Tasks Have Been Completed)

**DO THIS STEP BEFORE EACH DEV SESSION**

To configure your shell for a development session, **source** the `scripts/setup-env.sh` script. This will handle authentication, set the correct Google Cloud project, install dependencies, and activate the Python virtual environment.

```bash
source scripts/setup-env.sh [--noauth]
```

### Using Direnv

Note that you can automate loading the `setup-env.sh` script by installing [direnv](https://direnv.net/), and then including the `.envrc` in the project folder. E.g.

```bash
sudo apt install direnv

# Add eval "$(direnv hook bash)" to your .bashrc
echo "eval \"\
$(direnv hook bash)\"" >> ~/.bashrc

# Then, from this project folder:
direnv allow
```

## Useful Commands

| Command                 | Description                                                   |
| ----------------------- | ------------------------------------------------------------- |
| `make install`          | Install dependencies using uv                                 |
| `make playground`       | Launch local development environment using ADK Web UI. (Select the `app` folder when prompted) |
| `make lint`             | Run code quality checks                                       |
| `make test`             | Run unit and integration tests                                |
| `make deploy-cloud-run` | Deploy agent to Cloud Run                                     |
| `make local-backend`    | Launch local development server with hot-reload               |
| `make react-ui`         | Launch React frontend development server                      |
| `make ui-test`          | Run frontend UI tests                                         |
| `make docker-build`     | Build the unified production container image                  |
| `make docker-run`       | Run the unified container locally                             |
| `make tf-plan`          | Plan Terraform deployment                                     |
| `make tf-apply`         | Deploy environment resources using Terraform                  |
| `uv run python -m app.tools.ingest` | Run ingestion tool                                |

Many common tasks have been automated using `make`. If you work in an environment that doesn't support `make`, you can find the equivalent commands in the [Makefile](Makefile).

### Ingestion Tool

The ingestion tool supports a `--simulate` flag. Use `uv run python -m app.tools.ingest --simulate [OPTIONS]` to perform a dry run without modifying the Firestore database. This mode will print before and after snapshots showing exactly what actions would be performed.

## Deployment

### Dev Environment

You can test deployment towards a Dev Environment using the following command:

```bash
gcloud config set project <your-dev-project-id>
make deploy-cloud-run
```

The repository includes a Terraform configuration for the setup of the Dev Google Cloud project.
See [deployment/README.md](deployment/README.md) for instructions.

### Running in a Local Container

The application is unified into a single container image. To build and run it:

```bash
# Build the image
make docker-build

# Run the container (includes credential mounting for Firestore access)
make docker-run
```

Access the application at `http://localhost:8080`. The container implementation uses a hybrid SSR/SPA approach to inject SEO tags dynamically on the first request, ensuring optimal crawling and social previews.

### Production Deployment

The repository includes a Terraform configuration for the setup of a production Google Cloud project. Refer to [deployment/README.md](deployment/README.md) for detailed instructions on how to deploy the infrastructure and application.
