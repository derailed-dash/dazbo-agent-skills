---
name: maintaining-core-documentation
description: |
  Creates, maintains, and synchronises core project documentation (README, TODO, PRD, SPEC, ARCHITECTURE, DESIGN, TESTING, GUIDE, Deployment, and conditional Conductor context) using progressive disclosure, strict single-source-of-truth boundaries, and OKF v0.2 frontmatter. Use when writing, updating, auditing, or reviewing project documentation after codebase, architecture, testing, roadmap, or deployment changes.
metadata:
  author: Darren "Dazbo" Lester
  repository: https://github.com/derailed-dash/dazbo-agent-skills
---

# Maintaining Core Documentation

A structured framework for creating and synchronising technical documentation across software repositories without duplicating content or wasting context tokens.

## Table of Contents

- [Triggers](#triggers)
- [Progressive Disclosure & Selective Loading](#progressive-disclosure--selective-loading)
- [Core Principles & Anti-Redundancy](#core-principles--anti-redundancy)
- [OKF-Lite Frontmatter Standard (OKF v0.2)](#okf-lite-frontmatter-standard-okf-v02)
- [Document Routing Matrix](#document-routing-matrix)
- [Per-Document Boundaries & Notes](#per-document-boundaries--notes)
- [Formatting & Diagram Rules](#formatting--diagram-rules)
- [Documentation Review Process](#documentation-review-process)

## Triggers

Activate this skill whenever:

- The user requests documentation creation, restructuring, or an audit/review.
- Code changes introduce or alter features, public APIs, CLI commands, schemas, or architecture.
- Test suites, static quality gates, or CI workflows change.
- Infrastructure, Terraform variables, secrets, or deployment workflows change.
- Project milestones are completed or re-prioritised.

## Progressive Disclosure & Selective Loading

**Never read every documentation file, template, or sample upfront.** Follow this three-tier loading protocol so routine updates remain fast and token-efficient:

1. **Tier 1 — Triage Before Reading**:
   - Inspect `git status --short` and `git diff` (or the user request) and match impacted concerns against the [Document Routing Matrix](#document-routing-matrix) *before* opening documentation files.
   - Read **only** the existing repository documents inside the change's blast radius (plus `README.md` or `docs/SPEC.md` only if baseline project context is not yet loaded).
   - For `docs/*.md` files carrying OKF frontmatter, scan the first ~10 lines (`type`, `description`, `status`) to confirm relevance before loading the full body.
2. **Tier 2 — Templates On-Demand Only**:
   - Read a `./references/<DOC>.md.template` file **only** when creating a missing document from scratch, restructuring a stub/malformed file, or performing a full-repository documentation audit.
   - Skip reading templates during incremental edits to well-structured documents.
3. **Tier 3 — Samples Strictly as Greenfield Exemplars**:
   - Read files under `./references/samples/` **only** when authoring a substantial greenfield document that requires an exemplar for depth, tone, or YAML token schema (e.g. Stitch tokens in `DESIGN.md` or ADR tables in `ARCHITECTURE.md`).
   - **Never** read sample files during routine documentation synchronisation.

## Core Principles & Anti-Redundancy

1. **Expert Architect Tone**: Explain the *why* behind architectural choices alongside concise, accurate instructions. Ask the user whenever design rationale, scope, or trade-offs are unclear rather than inventing justification.
2. **Single Source of Truth (Minimal Overlap)**: Every fact has **one canonical owner**; cross-link rather than copying version tables, command recipes, or deployment steps across files. Root `README.md` is the sole intentional front-door exception summarising headline stack/commands and linking into `docs/` and `deployment/`.
3. **Verify Against Ground Truth**: Never assume existing docs are current. Verify paths, flags, dependencies, environment variables, and models directly against code, `pyproject.toml`, `package.json`, `Makefile`, `*.tfvars`, and `.env.template`.
4. **Brownfield Path First & Cross-Sync**: Default greenfield layout uses `docs/*.md`, root `README.md`/`TODO.md`, and `deployment/README.md`, but **always** respect existing repository locations first (e.g. root `SPEC.md`, `SPEC-<module>.md`, or root `ARCHITECTURE.md`) rather than creating duplicates. Propagate shared command, path, and environment variable updates to `.env.template` and `AGENTS.md` / `GEMINI.md` / `CLAUDE.md` where present.
5. **Clarity & Scannability**: Lead with the reader's goal using active voice, present tense, descriptive headings, bulleted lists or tables for 3+ items, and runnable examples where helpful.

## OKF-Lite Frontmatter Standard (OKF v0.2)

All documents under `docs/*.md` adopt lightweight **Open Knowledge Format (OKF v0.2)** YAML frontmatter so agents and humans can triage purpose and lifecycle state from the file header alone:

```yaml
---
type: "Technical Specification"   # REQUIRED: Human-readable doc kind
title: "Project — Technical Specification"
description: "One-sentence summary used for triage and indexing."
status: "stable"                  # draft | stable | deprecated
# Optional provenance & sign-off:
# verified: { by: "human:<id>", at: "YYYY-MM-DDTHH:MM:SSZ" }
# sources:
#   - id: prd
#     resource: PRD.md
#     title: Product Requirements
---
```

- **`docs/DESIGN.md` Compatibility**: OKF v0.2 preserves producer extension keys, so merge `type`, `title`, `description`, and `status` cleanly alongside Google Stitch design token keys (`version`, `name`, `colors`, `typography`, `rounded`, `spacing`, `components`).
- **Frontmatter-Free Landing Pages**: Keep `README.md`, `TODO.md`, and `deployment/README.md` **without** YAML frontmatter so GitHub renders them cleanly as repository and folder landing pages.
- **No Unnecessary Bundle Files**: Omit `docs/index.md` and `docs/log.md` in standard repositories (root `README.md` already indexes docs and Git tracks history). Defer full Knowledge Catalog OKF bundles (`_links.yaml`, `Attested Computation`) to `curate-context`.

## Document Routing Matrix

Identify impacted documents from your change set before reading or editing:

| Target Path (Default) | Policy | Primary Trigger Signals | Canonical Ownership (What Lives Here) | Template & Sample |
| :--- | :--- | :--- | :--- | :--- |
| `README.md` | **Core** (offer if missing) | New top-level dir, `make` target, setup step, headline stack shift | Front-door overview, doc index table, folder tree, quick start, headline commands & deploy summary | [README.md.template](./references/README.md.template) / [Sample](./references/samples/README.md) |
| `TODO.md` | **Optional** (if present, or offer) | Milestone completed, new backlog item discussed | High-level roadmap & feature backlog checkboxes (`[x]`, `[~]`, `[ ]`) | [TODO.md.template](./references/TODO.md.template) / [Sample](./references/samples/TODO.md) |
| `docs/PRD.md` | **Conditional** (product/app repos) | Vision, persona, metric, MVP vs future scope, or non-goal change | Product *why & who*: problem, personas, success metrics, user stories, explicit non-goals (zero tech stack) | [PRD.md.template](./references/PRD.md.template) / [Sample](./references/samples/docs/PRD.md) |
| `docs/SPEC.md` | **Core (SDD)** | New feature/contract, SDK/model lock change, boundary or `B1`–`Bn` change | Engineering contract: objective, optional capability map, FR/NFRs, pinned locks, *Always/Ask/Never*, binary rubric | [SPEC.md.template](./references/SPEC.md.template) / [Sample](./references/samples/docs/SPEC.md) |
| `docs/ARCHITECTURE.md` | **Core** (multi-module repos) | New ADR, schema/model change, layer/API boundary, security or cloud topology | Blueprint: ADR table, component/runtime PNG diagrams, data schemas, security/CORS/rate-limit, concise lifecycles | [ARCHITECTURE.md.template](./references/ARCHITECTURE.md.template) / [Sample](./references/samples/docs/ARCHITECTURE.md) |
| `docs/DESIGN.md` | **Conditional** (UI or rich CLI) | UI framework, CSS/theme tokens, component library, or CLI `rich` UX change | Stitch YAML tokens, colours, typography, layout, elevation, UI components, Do's/Don'ts, CLI UX | [DESIGN.md.template](./references/DESIGN.md.template) / [Sample](./references/samples/docs/DESIGN.md) ([Swiss](./references/samples/docs/DESIGN-exemplar-swiss.md)) |
| `docs/TESTING.md` | **Core** (tested repos) | New/changed tests, static gates, `CI=true`/mock rules, QA recipes | Static gates, local vs CI behaviour, test inventory table, targeted test commands, manual `curl`/QA checks | [TESTING.md.template](./references/TESTING.md.template) / [Sample](./references/samples/docs/TESTING.md) |
| `docs/GUIDE.md` | **Optional** (complex apps/CLIs) | Complex feature flow, CLI flags/YAML schema, contributor onboarding tour | Hands-on user/feature walkthroughs, CLI pipeline recipes, YAML schemas, contributor codebase tour | [GUIDE.md.template](./references/GUIDE.md.template) / [Sample](./references/samples/docs/GUIDE.md) |
| `deployment/README.md` | **Core** (deployable repos) | Terraform, APIs, IAM, `.tfvars`/`.env` propagation, `git-crypt`, CI/CD change | Infra directory tree, `.tfvars` -> runtime flow, secrets handling, Terraform/deploy commands, CI/CD & IAM | [DEPLOYMENT-README.md.template](./references/DEPLOYMENT-README.md.template) / [Sample](./references/samples/deployment/README.md) |
| `conductor/` (3 files) | **Conditional** (only if present) | Out-of-Conductor tech stack, branding, or product shift | Sync `product.md`, `product-guidelines.md`, `tech-stack.md` only | *(Conductor-managed)* |

## Per-Document Boundaries & Notes

- **`docs/ARCHITECTURE.md` vs `docs/GUIDE.md` (No Monolith)**: Keep `ARCHITECTURE.md` strictly structural (ADRs, diagrams, data schemas, security controls, brief component lifecycles). Put step-by-step feature tutorials, CLI flags, sample import YAML schemas, and codebase tours in `docs/GUIDE.md`. Note that persistent `docs/GUIDE.md` is distinct from Antigravity's ephemeral per-task `walkthrough.md` session artefacts.
- **ADR Alignment**: Record high-signal decisions in `ARCHITECTURE.md`'s ADR table. If the repository already maintains standalone numbered ADR files (`docs/adr/` or `docs/decisions/`), keep the table concise and link each row to its ADR file rather than duplicating full prose.
- **Conductor Coexistence**: If `conductor/` is active, **do not** create duplicate root/docs `PRD.md` or `SPEC.md` files where `conductor/product.md` and `conductor/tracks/<track_id>/spec.md` already own them. **Never** modify `conductor/workflow.md`, `conductor/tracks.md`, `conductor/setup_state.json`, `conductor/code_styleguides/`, or `conductor/archive/`.
- **Task Tracking Boundary**: Keep high-level feature milestones in `TODO.md`; leave fine-grained implementation slices in `tasks/plan.md`, `tasks/todo.md`, or Conductor track plans. Offer to mark matching `TODO.md` milestones complete (`[x]`) when finished.
- **Rubric Tagging (`[det]` / `[arch]` / `[ui]`)**: Tag every `B1`–`Bn` row in `SPEC.md` (`[det]`, `[arch]`, or `[ui]`/`[mech]`/`[docs]`) using clean single-wrapper IDs (e.g. `` `B1 [det]` ``) so automated loop runners (`tiered-rubric-loop`) route checks accurately without ambiguity while preserving human readability.

## Formatting & Diagram Rules

- **Headings**: Every Markdown heading (`#`, `##`, `###`, `####`) MUST be followed immediately by a blank line.
- **Links**: Always use clickable relative Markdown paths (e.g. `[docs/SPEC.md](docs/SPEC.md)`); **never** use absolute `file` scheme URIs.
- **Tables & Code Fences**: Present structured inventories, configs, commands, and ADRs as Markdown tables; wrap all commands/snippets in language-tagged fenced code blocks.
- **Diagrams (`NEVER` Use Mermaid or ASCII Box Diagrams)**:
  - **NEVER** insert `mermaid` code blocks (` ```mermaid `) or ASCII/Unicode box-and-arrow diagrams in any documentation file.
  - Standard ` ```text ` directory trees using `├──`, `│`, and `└──` inside `Project Structure` sections are permitted and expected.
  - For architecture, component, sequence, or deployment topology diagrams, generate PNG assets saved inside the repo (e.g. `docs/images/` or `media/`) and embed them via relative links (`![Component Architecture](images/component-architecture.png)`).

## Documentation Review Process

Track progress cleanly when updating documentation:

```text
Documentation Update Progress:
- [ ] Step 1: Triage impacted docs via the Document Routing Matrix (read only affected files).
- [ ] Step 2: Confirm excluded Conductor/ephemeral paths are left untouched.
- [ ] Step 3: Load `.md.template` (and `.md` sample only if greenfield) on demand; verify facts against code/config.
- [ ] Step 4: Update impacted docs preserving single-source-of-truth boundaries, OKF-Lite frontmatter on `docs/*.md`, and cross-links.
- [ ] Step 5: Validate formatting (blank line after headings, relative links only, zero `mermaid` or ASCII flow diagrams).
- [ ] Step 6: Run applicable project checks (e.g. `codespell -s`, plus `uv run --offline ~/.gemini/config/skills/tiered-rubric-loop/scripts/eval_rubric.py --dry-run --json` whenever `SPEC.md` or `docs/SPEC.md` is authored/updated) and present the Summary Table.
```

### Summary Table Format

| Document | Status | Change Summary / Rationale |
| :--- | :--- | :--- |
| `README.md` | Updated / No Change | [Brief summary of update OR why no change was needed] |
| `docs/SPEC.md` | Updated / No Change / N/A | [e.g. Added `FR-4` and `B7` for new `--simulate` flag] |
| `docs/ARCHITECTURE.md` | Updated / No Change | [e.g. Recorded ADR for rate-limiting strategy] |
