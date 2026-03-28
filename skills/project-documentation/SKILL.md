---
name: project-documentation
description: Creates, maintains, and synchronizes core project documentation (README, TODO, DESIGN, Architecture, Testing, Deployment). Use when the user needs to write, update, or structure project documentation based on codebase changes.
---

# Documentation Maintenance Skill

This skill provides a comprehensive framework for the creation and maintenance of high-quality, professional technical documentation for any software project or repository.

## Triggers

This skill should be triggered whenever:

- The user requests to create or review documentation.
- The user adds / changes / deletes functionality, or makes significant changes to the codebase.
- The user makes any changes to testing.
- The user makes any changes to deployment.

## Core Principles

1.  **Persona & Style**: Maintain a tone that is professional ("Expert Architect"), technical but welcoming. Use a high-level architectural perspective when explaining the "Why" behind design decisions.
2.  **Cross-Document Synchronisation**: Changes to a core property (like a project ID, a URL, or a file path) must be propagated to *all* applicable documentation files immediately.
3.  **Read Existing Documentation**: Always read the existing documentation files to understand the current state and intent of the project.
4.  **Tech Stack**: If the file `conductor/tech-stack.md` is present, read it to understand the intended tech stack.
5.  **Technical Accuracy**: Do not assume that the existing documentation is accurate or up-to-date. Verify the codebase, configuration settings (e.g. `config.py`, `Makefile`, `*.tfvars`, `pyproject.toml`), environment variable names, and command flags, before updating documentation.
6.  **Ask About Unknowns**:
    - Ask questions to help establish design choices and technology selection.
    - Ask questions to help establish the rationale for any design decisions that are missing rationale.
7.  **Technical Writer Synergy**: When performing documentation maintenance, you MUST make use of the `technical-writer` skill IF (and only IF) the `technical-writer` skill is present. If it is not found, follow the **Technical Writer Skill Synergy** section below.

## Technical Writer Skill Synergy

If you are performing any documentation tasks (e.g. creation or updates to README, TODO, DESIGN, Architecture, Testing, Deployment) and the `technical-writer` skill is not available in your current skills toolset:

1.  **Check for existence**: Use `npx skills list` (project scope) and `npx skills ls -g` (global scope) to verify if it is missing.
2.  **Recommend**: If not yet installed, inform the user that the `technical-writer` skill provides advanced formatting and style guidance. Offer to install it.
3.  **Install**: If the user agrees, install the skill for them using this command:
    `npx skills add https://github.com/shubhamsaboo/awesome-llm-apps --skill technical-writer -g -y`
4.  **Collaborate**: Once installed, load this skill and leverage it for documentation tasks.

## Document Maintenance Guide

These are the core documents that should be maintained by this skill:

### 1. `README.md` (The "Storefront")

*   **Focus**: Rapid onboarding and high-level project purpose.
*   **Template**: [README.md.template](references/README.md.template)
*   **Sample**: [README.md](references/samples/README.md)
*   **Key Sections**: Overview, Key Links (Blogs/Live Demo), Project Structure (folder tree), Setup (One-time vs Per-session), Useful Commands (use Markdown tables).
*   **Triggers**: 
    - Adding a new top-level directory.
    - Adding a core feature.
    - Adding a `make` target.
    - Changing the local development setup workflow.

### 2. `TODO.md` (Project Plan)

*   **Focus**: Overall project roadmap and task tracking.
*   **Template**: [TODO.md.template](references/TODO.md.template)
*   **Triggers**: 
    - Completing a step or updating the project timeline.
    - If asked to create a new TODO entry.
    - Offer to mark steps as closed when done.

### 3. `docs/DESIGN.md` (Visual & UX)

*   **Focus**: Visual identity, UX components, and design tokens.
*   **Template**: [design.md.template](references/design.md.template)
*   **Sample**: [docs/DESIGN.md](references/samples/docs/DESIGN.md)
*   **Key Sections**: Visual Identity (Typography, Colours), Visual Effects (e.g. Glassmorphism), Frontend Components (Layout, Carousel, Widget, etc), CLI UX (if present).
*   **Triggers**: 
    - When implementing a UI framework (e.g. React, Vue, Angular, Svelte, etc).
    - When adding or changing any UI components.
    - Modifying visuals or style, e.g. modifying `index.css` global styles.

### 4. `docs/architecture-and-walkthrough.md` (The "Blueprint")

*   **Focus**: System-wide architectural logic and design decisions.
*   **Template**: [architecture-and-walkthrough.md.template](references/architecture-and-walkthrough.md.template)
*   **Sample**: [docs/architecture-and-walkthrough.md](references/samples/docs/architecture-and-walkthrough.md)
*   **Key Sections**: Design Decisions (ADRs in table format with Rationale), Solution Architecture, Service/Model relationships, Key User Journeys / Walkthroughs
*   **Triggers**: 
    - Adding or changing a design decision.
    - Changing a database schema.
    - Modifying agent orchestration logic.
    - Adding or changing a coding framework.
    - Changing or introducing a new infrastructure hosting service (e.g. on GCP).
    - Adding a security component or feature.
    - Adding a layer (e.g. frontend, API, backend, persistence, etc).

### 5. `docs/testing.md` (Quality Assurance)

*   **Focus**: How we verify the application's correctness.
*   **Template**: [testing.md.template](references/testing.md.template)
*   **Sample**: [docs/testing.md](references/samples/docs/testing.md)
*   **Key Sections**: Scope (e.g. Python, frontend, agents), tooling (pytest, ruff, etc.), CI/CD environment specifics (Local vs `CI=true`), Unit/Integration/E2E test descriptions, Manual verification steps (e.g., `curl` scripts for rate limiting).
*   **Triggers**: 
    - Adding / changing / removing tests.
    - Changing mock strategies.
    - Introducing new quality gating tools.

### 6. `deployment/README.md` (Infrastructure)

*   **Focus**: Provisioning and managing the infrastructure environment.
*   **Template**: [deployment-README.md.template](references/deployment-README.md.template)
*   **Sample**: [deployment/README.md](references/samples/deployment/README.md)
*   **Key Sections**: Deployment approach (e.g. scripts, Terraform, or both), Terraform structure, Prerequisites, Variable propagation (env.tfvars -> substitutions -> runtime), Secrets management, CI/CD pipelines.
*   **Triggers**: 
    - Adding a new Terraform resource.
    - Changing IAM roles.
    - Changing a deployment script.
    - Adding a new service.
    - Updating the CI/CD pipeline logic.

### 7. `conductor/` Documents (Implementation Details)

*   **Focus**: Product logic, product branding, guidelines, and tech stack details.
*   **Key Files**: `product.md`, `product-guidelines.md`, `tech-stack.md`.
*   **Maintenance Condition**: ONLY maintain these if they already exist in the codebase.
*   **Triggers**: 
    - Major tech stack shifts.
    - Product branding changes.
    - Product logic re-definition.
    - Request to audit product alignment or tech stack compliance.

## Continuous Update Workflow

> [!IMPORTANT]
> Whenever you perform a significant code change or feature addition, or you are asked to update any documentation, you MUST:
> 1.  Identify which of the core documents are impacted.
> 2.  Assess if the change introduces a new "Design Decision" (ADR) that should be recorded in `docs/architecture-and-walkthrough.md`.
> 3.  Ensure all command snippets in `README.md` or `testing.md` match the updated code behavior.
> 4.  **Always use the provided templates** in the `references/` directory when creating new documentation files.
> 5.  **Use the samples** in the `references/samples/` directory as a guide for the style and structure of the documentation files.

## Formatting Best Practices

- Use **Tables** for mapping configurations, model fields, and design decisions to improve readability.
- Always include a blank line after any markdown header (at any heading level).
- Wrap any code in a fenced code block, with an appropriate language identifier. 
