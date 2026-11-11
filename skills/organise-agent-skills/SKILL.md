---
name: organise-agent-skills
description: |
  Standardised workflow for auditing, pruning, and organising agent skills in agentic development environments, such as Antigravity. Use when reviewing installed skills, pruning token overhead, disabling sub-skills managed by meta-skills, or adding on-demand activation rules to modular rules (config/rules/on-demand-skills.md), GEMINI.md, or AGENTS.md.
metadata:
  author: Darren "Dazbo" Lester
  repository: https://github.com/derailed-dash/dazbo-agent-skills
---

# Organising Agent Skills

> [!IMPORTANT]
> **Mandatory User Confirmation Guardrail**: The agent MUST NOT delete any skill directories, disable/enable skills in configuration files (`skills.json`), or mutate configuration/rules documents (`config/rules/*.md`, `GEMINI.md`, `AGENTS.md`, `README.md`) without first presenting the audit findings, proposed actions, and token metrics to the user and receiving explicit confirmation to proceed.

This skill provides a repeatable, structured workflow for auditing, pruning, and organising agent skills in Antigravity and Gemini environments. It ensures your prompt context window remains lean (~30–50 active skills / ~3,000 tokens overhead per interaction turn) while retaining full access to all installed skills.


## Table of Contents

- [Overview & Token Budgeting](#overview--token-budgeting)
- [Skill Lifecycle & States](#skill-lifecycle--states)
- [Workflow Phase 1: Audit & Discovery](#workflow-phase-1-audit--discovery)
- [Workflow Phase 2: Meta-Skill Delegation](#workflow-phase-2-meta-skill-delegation)
- [Workflow Phase 3: On-Demand Rules (`config/rules/on-demand-skills.md` / `AGENTS.md`)](#workflow-phase-3-on-demand-rules-configruleson-demand-skillsmd--agentsmd)
- [Workflow Phase 4: Portability & `skills.json` Standalone Inventory](#workflow-phase-4-portability--skillsjson-standalone-inventory)
- [Workflow Phase 5: Documentation Update](#workflow-phase-5-documentation-update)

---

## Overview & Token Budgeting

When an agent turn starts, the `name` and `description` of every **Installed and inactive (discoverable)** skill are injected into the system prompt context. 

* **The Problem**: Over-accumulating skills (100+ discoverable skills) injects 6,000–10,000+ tokens into every single interaction turn, wasting context budget and causing LLM decision fatigue (hallucinating or picking the wrong skill due to description overlap).
* **The Target State**: Maintain a **lean core of ~30 to 50 discoverable skills** (~3,000 tokens prompt overhead), placing specialised or sub-skills into an **Installed and excluded** state, using meta-skill routing and modular `model_decision` rules (`config/rules/on-demand-skills.md`) for everything else.

---

## Skill Lifecycle & States

Skills operate under three explicit states within agentic development environments (such as Antigravity):

1. **Installed and inactive (discoverable)**: These skills are present on disk and discoverable by our agent. When the agent (e.g. Antigravity) starts, their frontmatter (Level 1) is automatically read into context. In `skills.json`, these entries are prefixed with `//` or unexcluded.
2. **Installed and excluded**: These skills reside in your disk library but are _excluded_ from automatic Level 1 loading. For these, the agent does not automatically read their frontmatter and is therefore not *directly* aware of them during your conversation with it. But because they are present on disk and available to the agent, they can still be explicitly activated. In `skills.json`, these entries are listed as plain strings without `//`.
3. **Activated**: This is the runtime state when a skill's full `SKILL.md` body is actively loaded into the current turn context. I.e. Level 2 loading, and Level 3, where supporting files are present and appropriate.

---

## Workflow Phase 1: Audit & Discovery

1. **Filesystem Auto-Discovery & Full Inventory Audit**:
   - **Standalone Skills**: List all skill directories present on disk under `~/.gemini/config/skills/` (and `.agents/skills/` if in a workspace).
   - **Packaged Plugin Skills**: Inspect all bundled skills inside `~/.gemini/config/plugins/*/skills/` and parked skills in `~/.gemini/config/plugins/*/skills.all/`. Note that `skills.json` strictly filters **standalone skills** in `config/skills/` — never add plugin skill names to `skills.json` (they are no-ops). Antigravity loads **all** skills inside an enabled plugin's `skills/` directory as a bundle. Large plugins (such as `data-agent-kit-plugin`, 40 skills) should be disabled (`"enabled": false` in `config/config.json`), and specialised plugin sub-skills (e.g. inside `chrome-devtools-plugin` or `google-cloud-developer`) can be parked into `skills.all/` via `scripts/sync_skills.sh` so they remain readable on demand at zero startup token cost.
   - **Marketplace Auto-Updates on Disabled Plugins**: Antigravity updates installed Marketplace plugins on disk even when `"enabled": false` in `config/config.json`. When a plugin auto-updates, the upstream archive replaces the plugin directory without `skills.all/` and may bundle new skills that collide with standalone skills in `config/skills/`. Always run `./scripts/sync_skills.sh` (which invokes `scripts/reconcile_skills.py --write`) to restore `skills.all/`, re-park sub-skills, remove newly duplicated standalone skills, and prune retired skill entries.
   - Read `skills.json` (`~/.gemini/config/skills.json`) and compare all standalone `config/skills/` directories against entries in the `exclude` array.
   - **Identify Discrepancies**:
     - **Newly Discovered Standalone Skills**: Standalone skill folders present in `config/skills/` but missing from `skills.json`.
     - **Active Plugin Skills**: Plugin skills inside enabled `config/plugins/*/skills/` (counted towards the active Level 1 prompt budget, managed via plugin enablement or `skills.all/` parking rather than `skills.json`).
     - **Orphaned or No-Op Plugin Entries**: Entries in `skills.json` (with or without `//`) whose standalone directory no longer exists in `config/skills/` (including plugin skill names that do not belong in `skills.json`).
     - **Installed and Excluded Skills**: Standalone skills listed in `skills.json` without the `//` string prefix.
     - **Installed and Inactive (Discoverable) Skills**: Standalone skills listed in `skills.json` with the `//` string prefix.

2. **Measure Prompt Footprint**:
   - Sum word/token count of descriptions across all active discoverable skills (including unlisted plugin skills).
   - Check if total discoverable skills exceed the 30–50 skill sweet spot (~3,000–3,500 tokens), which triggers automatic skill dropping by Antigravity's context budget manager.

3. **Mandatory Semantic & Functional Overlap Audit**:
   The agent MUST systematically inspect the skill inventory for duplicate, legacy, or redundant skills. **Do NOT rely solely on literal folder names or string distance matching.**
   
   - **Semantic & Methodological Analysis**:
     Parse the YAML frontmatter (`description`), primary headings, and operational directives of each skill. Look for shared software engineering methodologies or overlapping tools disguised by differing folder names.
     *Example*: An extension plugin named `conductor` duplicates a standalone skill named `spec-driven-development` because both implement Spec-Driven Development (SDD) workflows.
   
   - **Functional Domain Clustering**:
     Group skills into semantic domain clusters and flag clusters where multiple active skills compete or create routing collisions:
     * **Gemini API & SDK**: e.g. `gemini-api` vs `gemini-api-dev` / `gemini-interactions-api`.
     * **Spec-Driven Development & Planning**: e.g. `spec-driven-development` vs `conductor` / `planning-and-task-breakdown`.
     * **Browser DevTools & Automation**: e.g. `chrome-devtools` vs `browser-testing-with-devtools` / `playwright-cli`.
     * **Cloud Authentication**: e.g. `gcloud-auth-verification` vs `google-cloud-auth-verification`.
     * **Workflow Orchestration**: e.g. `gcp-composer-troubleshooting` vs `managed-airflow-dag-troubleshooting`.
     * **Data Platforms & Storage**: e.g. BigQuery, Spark, Dataproc, GCS.
   
   - **Packaged Plugin Supersession**:
     Cross-reference standalone skills against official packaged extension plugins (`config/plugins/`). When an upstream plugin bundles skills covering a domain, the standalone copies are obsolete:
     * Flag obsolete standalone skills for deletion from disk.
     * Ensure deleted skills are pruned from `~/.agents/.skill-lock.json` so `npx skills update -g -y` does not re-download them.
     * Ensure `.gitignore` contains regex patterns (`[-_]`) ignoring standalone versions of plugin skills.

   - **Action**: Explicitly propose deleting redundant skill directories and disabling overlapping variants in the Pre-Execution Proposal.

---

## Workflow Phase 2: Meta-Skill Delegation

Identify master meta-skills that orchestrate sub-skills:

1. **Master Routers**:
   - E.g. the skill `using-agent-skills` orchestrates the 23 senior engineering SDLC sub-skills.
   - E.g. the skill `google-agents-cli-workflow` orchestrates ADK agent development sub-skills (`scaffold`, `code`, `deploy`, `eval`, `observability`).
   - E.g. the skill `gcp-data-pipelines` orchestrates Dataflow, Dataform, dbt, Dataproc, and BigQuery data pipeline tools.

2. **Action**:
   - Keep the master meta-skill **enabled** in `skills.json` (e.g. `"//using-agent-skills"`).
   - Disable child sub-skills in `skills.json` (plain string without `//`).
   - The master meta-skill will instruct the agent to inspect and read sub-skill files from disk on demand.

---

## Workflow Phase 3: On-Demand Rules (`config/rules/on-demand-skills.md` / `AGENTS.md`)

Whenever disabling a specialised or niche domain skill in `skills.json` (skills that are not sub-skills of an active master meta-skill), ensure an on-demand routing entry exists in a modular `model_decision` rule (`config/rules/on-demand-skills.md` globally, or workspace `.agents/rules/` / `AGENTS.md`) rather than bloating always-on `GEMINI.md`:

1. **Disable in `skills.json`**:
   - Exclude the standalone domain skill from automatic Level 1 prompt injection (plain string in `exclude`).

2. **Curated Domain Table + Automated Self-Maintenance**:
   - Group related excluded skills into a concise domain routing table inside `config/rules/on-demand-skills.md` (`trigger: model_decision` with a broad domain-agnostic trigger description so newly installed skills in new domains remain activatable without editing the trigger).
   - Run `uv run scripts/reconcile_skills.py --write` (or `./scripts/sync_skills.sh`), which automatically appends any newly excluded standalone skills not yet referenced in `config/rules/on-demand-skills.md` between `<!-- AUTO-GENERATED-EXCLUDED-SKILLS:START -->` and `<!-- AUTO-GENERATED-EXCLUDED-SKILLS:END -->` using each skill's frontmatter summary.

---

## Workflow Phase 4: Portability & `skills.json` Standalone Inventory

To ensure maximum visibility and effortless toggling without no-op clutter, `skills.json` is treated as an **explicit full inventory control panel for standalone skills** in `config/skills/` (never plugin-bundled skills).

### Antigravity `skills.json` Mechanics

- **Location**: `~/.gemini/config/skills.json` (or workspace `.agents/skills.json`).
- **Installed and excluded**: Plain string in `exclude` array (e.g. `"alloydb-basics"`). Exact match evaluates to `true`, excluding the standalone skill from Level 1 prompt loading.
- **Installed and inactive (discoverable)**: `//` prefix in `exclude` array (e.g. `"//bigquery-basics"`). The `//` prefix breaks exact string match (`exclude.includes("bigquery-basics")` evaluates to `false`), causing the loader to treat the standalone skill as discoverable (frontmatter automatically read into Level 1 prompt context).

### Reconciliation & Auto-Sync Procedure

When executing `organise-agent-skills` (or via `./scripts/sync_skills.sh` and `uv run scripts/reconcile_skills.py --write`):
1. **Auto-Register Missing Standalone Skills**: Add any standalone skill folder found in `config/skills/` that is absent from `skills.json` (defaulting to excluded unless explicitly enabled with `//`).
2. **Prune Orphaned & Plugin Entries**: Remove entries from `skills.json` whose standalone directory in `config/skills/` no longer exists, as well as any no-op plugin skill names.
3. **Sync On-Demand Rule**: Populate any unmapped excluded standalone skills into `config/rules/on-demand-skills.md`.
4. **Sort Alphabetically**: Maintain the `exclude` array sorted alphabetically (ignoring leading `//`) so scanning and diffing remain clean and predictable.

#### Example `skills.json`:
```json
{
  "exclude": [
    "accidental-data-loss-prevention", // INSTALLED AND EXCLUDED (no // prefix)
    "//agent-aware-cli",               // INSTALLED AND INACTIVE / DISCOVERABLE (// prefix workaround)
    "//using-agent-skills",            // INSTALLED AND INACTIVE / DISCOVERABLE (Master Meta-Skill)
    "spec-driven-development"          // INSTALLED AND EXCLUDED (Sub-skill activated on-demand)
  ]
}
```

### Portability Notes

- `skills.json` is the native exclusion mechanism for **Antigravity** environments.
- For other agent frameworks (e.g. Claude Code, Cursor, Windsurf), skill exclusion is managed via workspace `.agents/` boundaries or tool configuration files. Disabling via meta-skills and on-demand file reading remains 100% portable across all LLM agents.

---

## Workflow Phase 5: User Response & Documentation Update

1. **Pre-Execution Proposal**:
   Present the audit findings, redundant skill breakdown, and proposed actions to the user with a summary proposal table:

   | Metric | Baseline (Unoptimised) | Proposed (Optimised) | Delta |
   | :--- | :---: | :---: | :---: |
   | **Installed Skill Directories** | *N* | *M* | *-X* |
   | **Installed & Discoverable Skills** | *N* | *M* | *-X* |
   | **Installed & Excluded Skills** | *N* | *M* | *+X* |
   | **Prompt Token Overhead** | *~A tokens* | *~B tokens* | *-C tokens* |

   Ask the user for explicit confirmation before proceeding with any file deletions or configuration changes.

2. **Post-Execution Summary Table**:
   Once approved and executed, present the final metrics table showing exact deltas alongside a clear breakdown of what was done:
   * **Installed & Discoverable Skills**: Skills whose frontmatter is pre-loaded into Level 1 prompt context.
   * **Installed & Excluded Sub-Skills**: Skills read and activated on demand by parent meta-skills.
   * **Installed & Excluded On-Demand Skills**: Skills activated via `config/rules/on-demand-skills.md`, `GEMINI.md`, or `AGENTS.md` rules.
   * **Installed & Excluded Domain Skills**: Niche/specialised skills kept excluded until explicitly activated.
   * **Deleted / Retired Skills**: Obsolete or duplicate skills removed from disk.

3. **Documentation Update**:
   Always update the project `README.md` to document the active skill profile and meta-skill hierarchy.
