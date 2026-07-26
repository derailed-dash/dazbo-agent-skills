---
name: organise-agent-skills
description: Standardised workflow for auditing, pruning, and organising agent skills in agentic development environments, such as Antigravity. Use when reviewing installed skills, pruning token overhead, disabling sub-skills managed by meta-skills, or adding on-demand activation rules to GEMINI.md or AGENTS.md.
metadata:
  author: Darren "Dazbo" Lester
  version: "1.0.0"
---

# Organising Agent Skills

> [!IMPORTANT]
> **Mandatory User Confirmation Guardrail**: The agent MUST NOT delete any skill directories, disable/enable skills in configuration files (`skills.json`), or mutate configuration/rules documents (`GEMINI.md`, `AGENTS.md`, `README.md`) without first presenting the audit findings, proposed actions, and token metrics to the user and receiving explicit confirmation to proceed.

This skill provides a repeatable, structured workflow for auditing, pruning, and organising agent skills in Antigravity and Gemini environments. It ensures your prompt context window remains lean (~30–50 active skills / ~3,000 tokens overhead per interaction turn) while retaining full access to all installed skills.


## Table of Contents

- [Overview & Token Budgeting](#overview--token-budgeting)
- [Workflow Phase 1: Audit & Discovery](#workflow-phase-1-audit--discovery)
- [Workflow Phase 2: Meta-Skill Delegation](#workflow-phase-2-meta-skill-delegation)
- [Workflow Phase 3: On-Demand Rules (`GEMINI.md` / `AGENTS.md`)](#workflow-phase-3-on-demand-rules-geminimd--agentsmd)
- [Workflow Phase 4: Portability & `skills.json` Exclusions](#workflow-phase-4-portability--skillsjson-exclusions)
- [Workflow Phase 5: Documentation Update](#workflow-phase-5-documentation-update)

---

## Overview & Token Budgeting

When an agent turn starts, the `name` and `description` of **every active skill** are injected into the system prompt context. 

* **The Problem**: Over-accumulating skills (100+ active skills) injects 6,000–10,000+ tokens into every single interaction turn, wasting context budget and causing LLM decision fatigue (hallucinating or picking the wrong skill due to description overlap).
* **The Target State**: Maintain a **lean core of ~30 to 50 active skills** (~3,000 tokens prompt overhead), using meta-skill routing and `GEMINI.md` activation rules for everything else.

---

## Workflow Phase 1: Audit & Discovery

1. **Count Skills**:
   - Total skills on disk in `~/.gemini/config/skills/`.
   - Active skills (enabled in `skills.json`).
   - Inactive skills (excluded in `skills.json`).

2. **Measure Prompt Footprint**:
   - Sum word/token count of descriptions across all active skills.

3. **Identify Legacy & Duplicates**:
   - Check for byte-for-byte duplicate skills or deprecated SDK guides.
   - Delete obsolete skill directories from disk.

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

## Workflow Phase 4: Portability & `skills.json` Exclusions

### Antigravity `skills.json` Syntax
- **Location**: `~/.gemini/config/skills.json` (or workspace `.agents/skills.json`).
- **Disabled Skill**: Plain string in `exclude` array (e.g. `"alloydb-basics"`).
- **Enabled Skill**: `//` prefix in `exclude` array (e.g. `"//bigquery-sql"`). The `//` breaks exact string match, causing the loader to treat the skill as active.

#### Example `skills.json`:
```json
{
  "exclude": [
    "accidental-data-loss-prevention", // DISABLED / EXCLUDED (no // prefix)
    "//agent-aware-cli",               // ENABLED / ACTIVE (// prefix workaround)
    "//using-agent-skills",            // ENABLED (Master Meta-Skill)
    "spec-driven-development"          // DISABLED (Sub-skill leveraged on-demand)
  ]
}
```


### Portability Notes
- `skills.json` is the native exclusion mechanism for **Antigravity** environments.
- For other agent frameworks (e.g. Claude Code, Cursor, Windsurf), skill exclusion is managed via workspace `.agents/` boundaries or tool configuration files. Disabling via meta-skills and on-demand file reading remains 100% portable across all LLM agents.

---

## Workflow Phase 5: User Response & Documentation Update

1. **Pre-Execution Proposal**:
   Present the audit findings and proposed actions to the user with a summary proposal table:

   | Metric | Baseline | Proposed | Delta |
   | :--- | :---: | :---: | :---: |
   | **Active Skills** | *N* | *M* | *-X* |
   | **Excluded Skills** | *N* | *M* | *+X* |
   | **Prompt Token Overhead** | *~A tokens* | *~B tokens* | *-C tokens* |

   Ask the user for explicit confirmation before proceeding with any file deletions or configuration changes.

2. **Post-Execution Summary Table**:
   Once approved and executed, present the final metrics table showing exact deltas alongside a clear breakdown of what was done:
   * **Active Core Skills**: Skills pre-loaded into prompt context.
   * **Disabled Sub-Skills**: Skills read on demand by parent meta-skills.
   * **Disabled On-Demand Skills**: Skills activated via `GEMINI.md` / `AGENTS.md` rules.
   * **Disabled Domain Skills**: Niche/specialised skills kept excluded until requested.
   * **Deleted / Retired Skills**: Obsolete or duplicate skills removed from disk.

3. **Documentation Update**:
   Always update the project `README.md` to document the active skill profile and meta-skill hierarchy.

