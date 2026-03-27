# Deployment & Infrastructure

This directory contains the Terraform configuration for provisioning and managing the Google Cloud Platform (GCP) infrastructure for the Dazbo Portfolio application.

## Overview

The infrastructure is designed to be serverless, scalable, and secure, leveraging GCP's managed services. It follows a modular approach with separate configurations for development and multi-environment (Staging/Production) deployments.

### Key Components

- **Cloud Run:** Hosts the containerized FastAPI backend and agent.
- **Google Firestore:** Serverless NoSQL document database in **Native Mode** for portfolio content and session management.
- **Cloud Storage (GCS):** Used for storing static assets and telemetry logs.
- **Artifact Registry:** Stores Docker images for the application.
- **Cloud Build:** Manages the CI/CD pipeline for automated deployments.
- **Cloud Logging & Trace:** Provides observability and long-term telemetry storage.


## Project Structure

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

### Variable Propagation

Configuration flows from Terraform through to the runtime environment:

1.  **Definition**: Variables (e.g., `model`, `service_name`, `log_level`) are defined in `variables.tf` and populated via `env.tfvars`.
2.  **Build Configuration**: Terraform injects these values into the **Cloud Build Trigger** via substitutions (see `build_triggers.tf`).
3.  **Deployment**: When the trigger fires, Cloud Build receives these substitutions and passes them to the `gcloud run deploy` command (see `.cloudbuild/deploy-to-prod.yaml`).
4.  **Runtime**: The variables are set as **Environment Variables** on the Cloud Run service, accessible to the application at runtime.

### Configuration Sources (Why duplication?)

You may notice similar variables in `env.tfvars` and your local `.env` file. They serve distinct purposes:

-   **`deployment/terraform/vars/env.tfvars` (Infrastructure & CI/CD)**:
    -   Used by Terraform to configure the **Cloud Build Trigger**.
    -   Values are baked into the pipeline definition.
    -   *Source of Truth for automated deployments.*

-   **`.env` (Local Development)**:
    -   Used by your local runtime (`uvicorn`, `docker run`).
    -   Not visible to Terraform or Cloud Build.
    -   *Source of Truth for local testing.*
    -   **Note**: This file is encrypted in the repository using `git-crypt`. In CI/CD environments (detected via `CI=true`), the application skips loading this file to prevent compatibility issues. Ensure all required values are provided as environment variables in the pipeline.

-   **`Makefile` (Bridging the gap)**:
    -   The `deploy-cloud-run` target uses conditional assignment (`NAME ?= value`).
    -   It allows you to use your local `.env` values (via `source .env`) to perform manual deployments that match the production configuration.

### Terraform vs. Cloud Build Responsibilities

We use a **Hybrid Deployment Pattern**:

1.  **Terraform** defines the "Shell":
    -   Creates the Cloud Run service resource.
    -   Sets IAM policies (who can invoke it).
    -   Configures networking and base resource limits.
    -   Deploys a placeholder image (e.g., `hello-world`) initially.
    -   *Crucially*, it is configured to **ignore changes** to the container image and environment variables (via `lifecycle { ignore_changes = [...] }`).

2.  **Cloud Build** manages the "Content":
    -   Builds the actual application Docker image.
    -   Deploys the new image to the Cloud Run service.
    -   Injects runtime configuration as Environment Variables (e.g., `MODEL`, `COMMIT_SHA`).

This separation allows Terraform to manage the stable infrastructure while Cloud Build handles the dynamic application deployment without Terraform trying to "revert" the active configuration.

#### Why Include it in Terraform?

It might seem redundant to define the service in Terraform if Cloud Build deploys it, but this setup provides critical benefits:

1.  **Anchor for Dependencies**: Other resources need the Service to exist *before* deployment.
    -   **IAM & Permissions**: Terraform needs the service identity (`google_cloud_run_v2_service.app.name`) to create IAM bindings (e.g., granting `roles/run.invoker` to `allUsers`).
    -   **Service Accounts**: Binding the custom Service Account to the Cloud Run service happens at creation time.

2.  **Infrastructure vs. Application Code**:
    -   Terraform builds the "House" (Permissions, Networking, Resource Limits).
    -   Cloud Build provides the "Furniture" (Container Image, Application Code).
    -   Without Terraform, you'd have no "house" to deploy into, forcing you to script complex infrastructure setup into your CI/CD pipeline.

3.  **Drift Detection**: Terraform protects the *configuration*.
    -   If someone manually changes critical settings (e.g., Memory Limits, Ingress restrictions) in the Cloud Console, Terraform will detect this deviation during the next plan/apply cycle. Cloud Build only cares about the image, not the infrastructure settings.

## Prerequisites

1.  **GCP Projects:**
    -   **Single Project Architecture:** The configuration uses a single `project_id` for resources. You can deploy to different environments by using different `env.tfvars` files, but the logical definition is unified.
2.  **Tools:**
    -   [Terraform](https://www.terraform.io/downloads) (>= 1.0.0)
    -   [gcloud CLI](https://cloud.google.com/sdk/docs/install)
3.  **Authentication:**
    ```bash
    gcloud auth application-default login
    ```
4.  **GCS Bucket for Terraform State:**
    ```bash
    gcloud storage buckets create -p $GOOGLE_CLOUD_PROJECT gs://${GOOGLE_CLOUD_PROJECT}-tf-state
    ```

## Deployment Instructions

The easiest way to manage the infrastructure is using the provided `Makefile` in the project root.

### Quick Start (Makefile)

```bash
# Plan
make tf-plan

# Apply changes
make tf-apply
```

### Manual Terraform Usage

If you prefer to run Terraform directly:

```bash
cd deployment/terraform

# Plan changes
terraform plan -var-file="vars/env.tfvars"

# Apply changes
terraform apply -var-file="vars/env.tfvars"
```

## Maintenance & Cleanup

### Removing Legacy Resources

The infrastructure has been migrated from PostgreSQL to Firestore. Legacy SQL resources have been removed from the Terraform configuration. If you are cleaning up a pre-migration environment, `terraform apply` will automatically identify and propose the destruction of these resources.

### Firestore MCP Integration

The application utilizes a Google-managed Model Context Protocol (MCP) server to allow the Gemini agent to interact directly with Firestore.

#### Enablement (Manual Step)

While basic APIs are enabled via Terraform, the Firestore MCP service currently requires a one-time manual enablement using the `gcloud` CLI:

```bash
# Enable the managed Firestore MCP server
gcloud beta services mcp enable firestore.googleapis.com
```

#### Verification
To verify that the MCP server is accessible to the application:
1. Ensure the application service account has the following roles assigned (managed in `iam.tf`):
   - `roles/mcp.toolUser`
   - `roles/datastore.user`
2. Check the application logs for successful tool discovery during startup.

### Telemetry & Observability

Telemetry data (prompts, responses, and traces) is captured and routed to dedicated Cloud Logging buckets with 10-year retention. This data can be queried directly via Cloud Logging or exported for further analysis.

## Security

- **Least Privilege:** Service accounts are assigned only the roles necessary for their function (e.g., `roles/aiplatform.user`, `roles/logging.logWriter`).
- **Identity-Aware Proxy (IAP):** Can be optionally enabled for Cloud Run services (see `service.tf`).
- **Deletion Protection:** Firestore databases are configured with `delete_protection_state = "DELETE_PROTECTION_DISABLED"` for development ease, but should be enabled for critical production environments.
