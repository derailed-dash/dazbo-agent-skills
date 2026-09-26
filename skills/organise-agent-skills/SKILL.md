---
name: organise-agent-skills
description: |
  Standardised workflow for auditing, pruning, and organising agent skills in agentic development environments, such as Antigravity. Use when reviewing installed skills, pruning token overhead, disabling sub-skills managed by meta-skills, or adding on-demand activation rules to GEMINI.md or AGENTS.md.
metadata:
  author: Darren "Dazbo" Lester
  repository: https://github.com/derailed-dash/dazbo-agent-skills
---

# Organising Agent Skills

> [!IMPORTANT]
> **Mandatory User Confirmation Guardrail**: The agent MUST NOT delete any skill directories, disable/enable skills in configuration files (`skills.json`), or mutate configuration/rules documents (`GEMINI.md`, `AGENTS.md`, `README.md`) without first presenting the audit findings, proposed actions, and token metrics to the user and receiving explicit confirmation to proceed.

This skill provides a repeatable, structured workflow for auditing, pruning, and organising agent skills in Antigravity and Gemini environments. It ensures your prompt context window remains lean (~30–50 active skills / ~3,000 tokens overhead per interaction turn) while retaining full access to all installed skills.


## Table of Contents

- [Overview & Token Budgeting](#overview--token-budgeting)
- [Skill Lifecycle & States](#skill-lifecycle--states)
- [Workflow Phase 1: Audit & Discovery](#workflow-phase-1-audit--discovery)
- [Workflow Phase 2: Meta-Skill Delegation](#workflow-phase-2-meta-skill-delegation)
- [Workflow Phase 3: On-Demand Rules (`GEMINI.md` / `AGENTS.md`)](#workflow-phase-3-on-demand-rules-geminimd--agentsmd)
- [Workflow Phase 4: Portability & `skills.json` Exclusions](#workflow-phase-4-portability--skillsjson-exclusions)
- [Workflow Phase 5: Documentation Update](#workflow-phase-5-documentation-update)

---

## Overview & Token Budgeting

When an agent turn starts, the `name` and `description` of every **Installed and inactive (discoverable)** skill are injected into the system prompt context. 

* **The Problem**: Over-accumulating skills (100+ discoverable skills) injects 6,000–10,000+ tokens into every single interaction turn, wasting context budget and causing LLM decision fatigue (hallucinating or picking the wrong skill due to description overlap).
* **The Target State**: Maintain a **lean core of ~30 to 50 discoverable skills** (~3,000 tokens prompt overhead), placing specialised or sub-skills into an **Installed and excluded** state, using meta-skill routing and `GEMINI.md` activation rules for everything else.

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
   - **Packaged Plugin Skills**: Inspect all bundled skills inside `~/.gemini/config/plugins/*/skills/`. (Packaged plugin skills that are unlisted in `skills.json` are treated by Antigravity as discoverable by default and contribute silently to prompt overhead).
   - Read `skills.json` (`~/.gemini/config/skills.json`) and compare all disk directories against entries in the `exclude` array.
   - **Identify Discrepancies**:
     - **Newly Discovered Skills**: Standalone skill folders present on disk but missing from `skills.json`.
     - **Unlisted Plugin Skills**: Plugin skills present on disk but absent from `skills.json`.
     - **Orphaned Entries**: Entries in `skills.json` (with or without `//`) whose directory no longer exists on disk.
     - **Installed and Excluded Skills**: Skills listed in `skills.json` without the `//` string prefix.
     - **Installed and Inactive (Discoverable) Skills**: Skills listed in `skills.json` with the `//` string prefix.

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

## Workflow Phase 3: On-Demand Rules (`GEMINI.md` / `AGENTS.md`)

Whenever disabling a specialised or niche domain skill in `skills.json` (skills that are not sub-skills of a master meta-skill), you **MUST** ensure an activation rule exists in `GEMINI.md` or `AGENTS.md` so the agent knows when to enable or inspect it on demand.

1. **Disable in `skills.json`**:
   - Exclude the domain skills from automatic prompt injection by default (e.g. plain string in `exclude`).

2. **Mandatory Rule Generation in `GEMINI.md` or `AGENTS.md`**:
   - Inspect `GEMINI.md` (or `AGENTS.md` for workspace skills) under `## Knowledge Rules`.
   - If an activation rule for the disabled domain skill does **not** already exist, you **MUST** draft and append an activation rule using the following template:

   ```markdown
   ### <Domain / Skill Name> Activation Rule

   The `<skill-name>` skill is disabled by default in `skills.json` to keep context window overhead lean.

   **Activation Rule**: Activate or inspect `<skill-name>` (by adding `//` in `skills.json` or reading on demand) whenever <specific scenario, task type, or trigger conditions>.
   ```

   *Examples*:
   - **GCS Security Assessment** (`gcs-security-assessment`): Activate whenever auditing bucket access controls, storage security posture, or SAIF compliance.
   - **NotebookLM Auth** (`notebooklm-auth`): Activate whenever diagnosing or resolving NotebookLM MCP cookie or authentication errors.

---

## Workflow Phase 4: Portability & `skills.json` Full-Inventory Management

To ensure maximum visibility and effortless toggling, `skills.json` is treated as an **explicit full inventory control panel** for all installed skills rather than a partial list of exclusions.

### Antigravity `skills.json` Mechanics

- **Location**: `~/.gemini/config/skills.json` (or workspace `.agents/skills.json`).
- **Installed and excluded**: Plain string in `exclude` array (e.g. `"alloydb-basics"`). Exact match evaluates to `true`, excluding the skill from Level 1 prompt loading.
- **Installed and inactive (discoverable)**: `//` prefix in `exclude` array (e.g. `"//bigquery-sql"`). The `//` prefix breaks exact string match (`exclude.includes("bigquery-sql")` evaluates to `false`), causing the loader to treat the skill as discoverable (frontmatter automatically read into Level 1 prompt context).

### Reconciliation & Auto-Sync Procedure

When executing `organise-agent-skills`:
1. **Auto-Register Missing Skills**: Add any skill folder found on disk that is absent from `skills.json`. Default newly registered skills to discoverable (`"//skill-name"`) or excluded (`"skill-name"`) based on user preference or token budget strategy.
2. **Prune Orphaned Entries**: Remove entries from `skills.json` whose corresponding directory on disk no longer exists.
3. **Sort Alphabetically**: Maintain the `exclude` array sorted in alphabetical order so that scanning and diffing remain clean and predictable.

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
   * **Installed & Excluded On-Demand Skills**: Skills activated via `GEMINI.md` / `AGENTS.md` rules.
   * **Installed & Excluded Domain Skills**: Niche/specialised skills kept excluded until explicitly activated.
   * **Deleted / Retired Skills**: Obsolete or duplicate skills removed from disk.

3. **Documentation Update**:
   Always update the project `README.md` to document the active skill profile and meta-skill hierarchy.

