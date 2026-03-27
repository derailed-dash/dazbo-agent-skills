---
name: project-documentation
description: Creates, maintains, and synchronizes core project documentation (README, TODO, DESIGN, Architecture, Testing, Deployment). Use when the user needs to write, update, or structure project documentation based on codebase changes.
---

# Documentation Maintenance Skill

This skill provides a comprehensive framework for the maintenance of high-quality, professional technical documentation for the Dazbo Portfolio application and related projects. 

## Core Principles

1.  **Persona & Style**: Maintain a tone that is professional ("Expert Architect"), technical but welcoming. Use a high-level architectural perspective when explaining the "Why" behind design decisions.
2.  **Cross-Document Synchronisation**: Changes to a core property (like a project ID, a URL, or a file path) must be propagated to *all* applicable documentation files immediately.
3.  **Technical Accuracy**: Always verify the codebase, configuration settings (e.g. `config.py`, `Makefile`, `*.tfvars`, `pyproject.toml`), environment variable names, and command flags, before updating documentation.
4.  **Tech Stack**: If the file `conductor/tech-stack.md` is present, read it to understand the intended tech stack.
5.  **Ask About Unknowns**:
    - Ask questions to help establish design choices and technology selection.
    - Ask questions to help establish the rationale for any design decisions that are missing rationale.
6.  **Technical Writer Synergy**: When performing documentation maintenance, you MUST make use of the `technical-writer` skill IF (and only IF) the `technical-writer` skill is present.

## Document Maintenance Guide

### 1. `README.md` (The "Storefront")

*   **Focus**: Rapid onboarding and high-level project purpose.
*   **Template**: [README.md.template](references/README.md.template)
*   **Key Sections**: Overview, Key Links (Blogs/Live Demo), Project Structure (folder tree), Setup (One-time vs Per-session), Useful Commands (use Markdown tables).
*   **Maintenance Trigger**: Adding a new top-level directory, adding a core feature, adding a make target, or changing the local development setup workflow.

### 2. `TODO.md` (Project Plan)

*   **Focus**: Overall project roadmap and task tracking.
*   **Template**: [TODO.md.template](references/TODO.md.template)
*   **Key Sections**: Achieved goals, In-progress tasks, Future backlog.
*   **Maintenance Trigger**: Completing a step or updating the project timeline. Offer to mark steps as closed when done.

### 3. `docs/DESIGN.md` (Visual & UX)

*   **Focus**: Visual identity, UX components, and design tokens.
*   **Template**: [design.md.template](references/design.md.template)
*   **Key Sections**: Visual Identity (Typography, Colors), Visual Effects (Glassmorphism), Frontend Components (Layout, Carousel, Widget), CLI UX (Rich library progress/reporting).
*   **Maintenance Trigger**: Modifying `index.css` global styles, creating new React UI components, or adding visual console output to scripts.

### 4. `docs/architecture-and-walkthrough.md` (The "Blueprint")

*   **Focus**: System-wide architectural logic and design decisions.
*   **Template**: [architecture-and-walkthrough.md.template](references/architecture-and-walkthrough.md.template)
*   **Sample**: [docs/architecture-and-walkthrough.md](references/samples/docs/architecture-and-walkthrough.md)
*   **Key Sections**: Design Decisions (ADRs in table format with Rationale), Solution Architecture, Service/Model relationships, Key User Journeys / Walkthroughs
*   **Maintenance Trigger**: Adding or changing a design decision; changing the database schema; modifying agent orchestration logic; adding or changing a coding framework; changing or introducing a new infrastructure hosting service (e.g. on GCP); adding a security component or feature; adding a layer (e.g. API).

### 5. `docs/testing.md` (Quality Assurance)

*   **Focus**: How we verify the application's correctness.
*   **Template**: [testing.md.template](references/testing.md.template)
*   **Sample**: [docs/testing.md](references/samples/docs/testing.md)
*   **Key Sections**: Scope (e.g. Python, frontend, agents), tooling (pytest, ruff, etc.), CI/CD environment specifics (Local vs `CI=true`), Unit/Integration/E2E test descriptions, Manual verification steps (e.g., `curl` scripts for rate limiting).
*   **Maintenance Trigger**: Adding new test classes, changing mock strategies, or introducing new quality gating tools.

### 6. `deployment/README.md` (Infrastructure)

*   **Focus**: Provisioning and managing the infrastructure environment.
*   **Template**: [deployment-README.md.template](references/deployment-README.md.template)
*   **Sample**: [deployment/README.md](references/samples/deployment/README.md)
*   **Key Sections**: Deployment approach (e.g. scripts, Terraform, or both), Terraform structure, Prerequisites, Variable propagation (env.tfvars -> substitutions -> runtime), Secrets management, CI/CD pipelines, Maintenance instructions.
*   **Maintenance Trigger**: Adding a new Terraform resource (e.g., adding a secret to Secret Manager), changing IAM roles, changing a deployment script, adding a new service, or updating the CI/CD pipeline logic.

### 7. `conductor/` Documents (Implementation Details)

*   **Focus**: Product logic, product branding, guidelines, and tech stack details.
*   **Key Files**: `product.md`, `product-guidelines.md`, `tech-stack.md`.
*   **Maintenance Condition**: ONLY maintain these if they already exist in the codebase.
*   **Maintenance Trigger**: Major tech stack shifts or product logic re-definition.

## Continuous Update Workflow

> [!IMPORTANT]
> Whenever you perform a significant code change or feature addition, you MUST:
> 1.  Identify which of the core documents are impacted.
> 2.  Assess if the change introduces a new "Design Decision" (ADR) that should be recorded in `docs/architecture-and-walkthrough.md`.
> 3.  Ensure all command snippets in `README.md` or `testing.md` match the updated code behavior.
> 4.  **Always use the provided templates** in the `references/` directory when creating new documentation files.

## Formatting Best Practices

- Use **Tables** for mapping configurations, model fields, and design decisions to improve readability.
- Always include a blank line under a markdown header.
- Wrap any code in a fenced code block, with an appropriate language identifier. 
