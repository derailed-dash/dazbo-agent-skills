# Deployment & Infrastructure

This directory contains the Terraform configuration for provisioning and managing the Google Cloud Platform (GCP) infrastructure for the `dazbo-portfolio` application. For runtime component topology, data models, and application security controls, see [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).

## Overview

The infrastructure uses a **Hybrid Deployment Pattern** designed to be serverless, scalable, and reproducible:

1. **Terraform** defines the stable infrastructure shell: provisions the Cloud Run service, enables GCP APIs, sets IAM policies and custom service accounts, creates Firestore and GCS storage resources, configures Cloud Build triggers, and deploys an initial placeholder image while ignoring later container image and runtime environment updates (`lifecycle { ignore_changes = [...] }`).
2. **Cloud Build** manages application content: compiles the unified React + FastAPI container image on GitHub pushes and rolls out new Cloud Run revisions with updated `MODEL` and `COMMIT_SHA` environment variables.

## Infrastructure Directory Structure

```text
deployment/terraform/
├── vars/
│   └── env.tfvars        # Environment-specific variable values
├── apis.tf               # Google Cloud API enablement
├── build_triggers.tf     # Cloud Build trigger definitions for CI/CD
├── github.tf             # GitHub repository and connection configuration
├── iam.tf                # IAM bindings and permissions
├── locals.tf             # Local variable definitions and helpers
├── providers.tf          # Terraform provider configuration
├── service.tf            # Cloud Run service definition
├── service_accounts.tf   # Service Account definitions
├── storage.tf            # GCS buckets, Artifact Registry, and Firestore
├── telemetry.tf          # Cloud Logging buckets and telemetry sinks
└── variables.tf          # Input variable definitions
```

## Configuration, Secrets & Variable Propagation

### Variable Propagation

1. **Definition**: Variables (e.g. `model`, `service_name`, `log_level`) are declared in `variables.tf` and populated in `vars/env.tfvars`.
2. **Build Configuration**: Terraform injects these values into the Cloud Build trigger via substitutions (`build_triggers.tf`).
3. **Deployment**: Cloud Build forwards substitutions to `gcloud run deploy` (`.cloudbuild/deploy-to-prod.yaml`).
4. **Runtime**: Values become environment variables on the Cloud Run revision.

### Configuration Sources (IaC vs Local `.env`)

- **`deployment/terraform/vars/env.tfvars` (Infrastructure & CI/CD)**: Source of truth for Terraform and automated Cloud Build triggers.
- **`.env` / `.env.enc` (Local Development)**: Source of truth for local runs (`uvicorn`, `docker run`), encrypted in Git via `git-crypt` (`~/localdev/git-crypt-key`) and skipped when `CI=true`.
- **`Makefile` (Bridging the Gap)**: Uses `-include .env.template` and `-include .env` alongside unambiguous defaults such as `SERVICE_NAME ?= dazbo-portfolio` (never `NAME` or `LANG` overrides, which collide with Linux/WSL host environment variables).

## Prerequisites

1. **Tools**: Install [Terraform](https://developer.hashicorp.com/terraform/downloads) (`>= 1.0.0`) and [Google Cloud CLI (`gcloud`)](https://cloud.google.com/sdk/docs/install).
2. **Authentication**:

    ```bash
    gcloud auth application-default login
    ```

3. **GCS Bucket for Terraform State**:

    ```bash
    gcloud storage buckets create -p $GOOGLE_CLOUD_PROJECT gs://${GOOGLE_CLOUD_PROJECT}-tf-state
    ```

## Provisioning & Deployment Commands

### Infrastructure (Terraform)

```bash
make tf-plan
make tf-apply
```

Or run Terraform directly from `deployment/terraform/`:

```bash
cd deployment/terraform
terraform plan -var-file="vars/env.tfvars"
terraform apply -var-file="vars/env.tfvars"
```

### Manual Application Deployment

```bash
gcloud config set project <your-dev-project-id>
make deploy-cloud-run
```

## CI/CD Pipelines & Security Controls

### Firestore MCP Integration

While core GCP APIs are enabled via `apis.tf`, the managed Firestore MCP server requires a one-time manual enablement step:

```bash
gcloud beta services mcp enable firestore.googleapis.com
```

#### Verification

1. Confirm the application service account holds `roles/mcp.toolUser` and `roles/datastore.user` (defined in `iam.tf`).
2. Check Cloud Run startup logs for successful MCP tool discovery.

### Security & Observability Controls

- **Least Privilege**: Service accounts receive only required permissions (`roles/aiplatform.user`, `roles/logging.logWriter`, `roles/datastore.user`, `roles/mcp.toolUser`).
- **Identity-Aware Proxy (IAP)**: Optional ingress protection configured in `service.tf`.
- **Deletion Protection**: Set `delete_protection_state = "DELETE_PROTECTION_ENABLED"` in `storage.tf` for production Firestore databases.
- **Telemetry**: Prompts, responses, and traces route to dedicated Cloud Logging buckets with 10-year retention (`telemetry.tf`).
