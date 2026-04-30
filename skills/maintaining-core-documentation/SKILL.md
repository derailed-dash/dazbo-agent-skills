---
name: maintaining-core-documentation
description: Creates, maintains, and synchronizes core project documentation (README, TODO, DESIGN, Architecture, Testing, Deployment). Use when the user needs to write, update, or structure project documentation based on codebase changes, or whenever the user asks to perform any documentation tasks or documentation review.
---

# Maintaining Core Documentation

This skill provides a comprehensive framework for the creation and maintenance of high-quality, professional technical documentation for any software project or repository.

## Table of Contents

- [Triggers](#triggers)
- [Mandatory Initialization](#mandatory-initialization)
- [Core Principles](#core-principles)
- [Technical Writer Skill Synergy](#technical-writer-skill-synergy)
- [Document Maintenance Guide](#document-maintenance-guide)
- [Formatting Rules](#formatting-rules)
- [Documentation Review Process](#documentation-review-process)

## Triggers

This skill should be triggered whenever:

- The user requests to create or review documentation.
- The user adds / changes / deletes functionality, or makes significant changes to the codebase.
- The user makes any changes to testing.
- The user makes any changes to deployment.

## Mandatory Initialization

Before performing ANY documentation task, you MUST check for the presence of the `technical-writer` skill, by following the guidance in the `Technical Writer Skill Synergy` section below.

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

The `technical-writer` skill improves the quality of your documentation review and creation.

1. Determine `technical-writer` skill availability:
   **Skill exists?** → Load the skill and collaborate on formatting.
   **Skill missing?** → Follow the "Installation workflow" below.

2. Installation workflow:
   - Check availability using `npx skills ls -g`.
   - Recommend the skill to the user.
   - If approved, install via: `npx skills add https://github.com/shubhamsaboo/awesome-llm-apps --skill technical-writer -g -y`

## Document Maintenance Guide

Here are the core documents that should be maintained by this skill. You MUST review EACH of these core documents and update them as needed.

### 1. `README.md` (The "Storefront")

*   **Focus**: Rapid onboarding and high-level project purpose.
*   **Template**: [README.md.template](./references/README.md.template)
*   **Sample**: [README.md](./references/samples/README.md)
*   **Key Sections**: Overview, Key Links (Blogs/Live Demo), Project Structure (folder tree), Setup (One-time vs Per-session), Useful Commands (use Markdown tables).
*   **Triggers** include, but are not limited to: 
    - Adding a new top-level directory.
    - Adding a core feature.
    - Adding a `make` target.
    - Changing the local development setup workflow.

### 2. `TODO.md` (Project Plan)

*   **Focus**: Overall project roadmap and task tracking.
*   **Template**: [TODO.md.template](./references/TODO.md.template)
*   **Maintenance Condition**: Only maintain if this file already exists. You may offer to create it, for example, if tasks have been achieved and/or future tasks are being discussed.
*   **Triggers** include, but are not limited to: 
    - Completing a step or updating the project timeline.
    - If asked to create a new TODO entry.
    - Offer to mark steps as closed when done.

### 3. `docs/DESIGN.md` (Visual & UX)

*   **Focus**: Visual identity, UX components, and design tokens. Can be used by UI design integrations, e.g. Google Stitch.
*   **Template**: [design.md.template](./references/design.md.template)
*   **Sample**: [docs/DESIGN.md](./references/samples/docs/DESIGN.md)
*   **Key Sections**: Visual Identity (Typography, Colours), Visual Effects (e.g. Glassmorphism), Frontend Components (Layout, Carousel, Widget, etc), CLI UX (if present).
*   **Triggers** include, but are not limited to: 
    - When implementing a UI framework (e.g. React, Vue, Angular, Svelte, etc).
    - When adding or changing any UI components.
    - Modifying visuals or style, e.g. modifying `index.css` global styles.

### 4. `docs/architecture-and-walkthrough.md` (The "Blueprint")

*   **Focus**: System-wide architectural logic and design decisions. Assess if any change introduces a new "Design Decision" (ADR) that should be recorded in `docs/architecture-and-walkthrough.md`.
*   **Template**: [architecture-and-walkthrough.md.template](./references/architecture-and-walkthrough.md.template)
*   **Sample**: [docs/architecture-and-walkthrough.md](./references/samples/docs/architecture-and-walkthrough.md)
*   **Key Sections**: Design Decisions (ADRs in table format with Rationale), Solution Architecture, Service/Model relationships, Key User Journeys / Walkthroughs
*   **Triggers** include, but are not limited to: 
    - Adding or changing a design decision.
    - Changing a database schema.
    - Modifying agent orchestration logic.
    - Adding or changing a coding framework.
    - Changing or introducing a new infrastructure hosting service (e.g. on GCP).
    - Adding a security component or feature.
    - Adding a layer (e.g. frontend, API, backend, persistence, etc).

### 5. `docs/testing.md` (Quality Assurance)

*   **Focus**: How we verify the application's correctness.
*   **Template**: [testing.md.template](./references/testing.md.template)
*   **Sample**: [docs/testing.md](./references/samples/docs/testing.md)
*   **Key Sections**: Scope (e.g. Python, frontend, agents), tooling (pytest, ruff, etc.), CI/CD environment specifics (Local vs `CI=true`), Unit/Integration/E2E test descriptions, Manual verification steps (e.g., `curl` scripts for rate limiting).
*   **Triggers** include, but are not limited to: 
    - Adding / changing / removing tests.
    - Changing mock strategies.
    - Introducing new quality gating tools.

### 6. `deployment/README.md` (Infrastructure)

*   **Focus**: Provisioning and managing the infrastructure environment.
*   **Template**: [deployment-README.md.template](./references/deployment-README.md.template)
*   **Sample**: [deployment/README.md](./references/samples/deployment/README.md)
*   **Key Sections**: Deployment approach (e.g. scripts, Terraform, or both), Terraform structure, Prerequisites, Variable propagation (env.tfvars -> substitutions -> runtime), Secrets management, CI/CD pipelines.
*   **Maintenance Condition**: All projects should have some sort of deployment documentation. If it does not exist, you should offer to create it. Update this documentation whenever you make changes to the deployment process.
*   **Triggers** include, but are not limited to: 
    - Adding a new Terraform resource.
    - Enabling APIs.
    - Changing a deployment script.
    - Adding a new service.
    - Changing or binding IAM roles.
    - Updating install pre-reqs.
    - Updating the CI/CD pipeline logic, updating GitHub Actions, updating Cloud Build, etc.

### 7. `conductor/` Documents (Implementation Details)

*   **Focus**: Product logic, product branding, guidelines, and tech stack details. These documents are automatically managed by the Gemini Conductor Extension, but if changes are done outside of Conductor, these documents should be updated to reflect the changes.
*   **Key Files**: `product.md`, `product-guidelines.md`, `tech-stack.md`.
*   **Maintenance Condition**: ONLY maintain these documents if they already exist in the codebase.
*   **Triggers** include, but are not limited to:
    - Major tech stack shifts.
    - Product branding changes.
    - Product logic re-definition.
    - Request to audit product alignment or tech stack compliance.

## Formatting Rules

*   Always use tables for configurations, model fields, and design decisions to improve readability.
*   There MUST be a blank line after every markdown header.
*   All code MUST be wrapped in fenced code blocks with appropriate language identifiers.

## Documentation Review Process

Copy this checklist and track your progress when updating documentation:

~~~
Documentation Update Progress:

- [ ] Step 1: Identify which of the core documents are impacted by code changes.
- [ ] Step 2: Assess if the change introduces a new "Design Decision" that should be recorded in `docs/architecture-and-walkthrough.md`.
- [ ] Step 3: For all identified core documents, draft updates as per Document Maintenance Guide, and using the appropriate templates in the `./references` directory and using the samples in  `./references/samples/`.
- [ ] Step 4: Review against the formatting rules in the [Formatting Rules](#formatting-rules) section.
- [ ] Step 5: Check that the identified core documents have been updated. If any changes have been missed or performed incorrectly, go back to Step 2 and repeat.
- [ ] Step 6: Only finalize and save when all requirements are met.
- [ ] Step 7: Summarise with a table of which documents were updated and what changes were made. Also include which documents (if any) were not updated and why.
~~~  

### Summary Table Format

When performing Step 7 of the Documentation Review Process, use the following table structure to summarize your work:

| Document | Status | Change Summary / Rationale |
| :--- | :--- | :--- |
| `README.md` | [Updated/No Change] | [Brief description of changes OR why no update was needed] |
| `TODO.md` | [Updated/No Change] | [e.g. Marked Step 4 as complete] |
| `docs/DESIGN.md` | [Updated/No Change] | [e.g. Added new color tokens to frontmatter] |
| ... | ... | ... |
