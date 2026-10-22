---
name: local-code-review
description: |
  Conducts a rigorous, multi-axis local code, documentation, and architecture review in any project (GitHub, Bitbucket, GitLab, or a local directory). Supports both Diff/Change Review Mode (uncommitted changes, branches, commit ranges) and Whole-Codebase Audit Mode (reviewing an entire repository or module without relying on Git diffs). Evaluates correctness, simplicity, architecture, security, performance, test quality, documentation alignment, and visual assets using Dazbo's core review rubric and anti-hallucination guardrails.
metadata:
  author: Darren "Dazbo" Lester
  repository: https://github.com/derailed-dash/dazbo-agent-skills
  cli:
    - git
---

# Local Code & Technical Review (`local-code-review`)

Conducts a high-signal, multi-dimensional review of code, tests, documentation, configuration, and visual diagrams in any local workspace—whether hosted on GitHub, Bitbucket, GitLab, or not yet under version control.

Supports two operating modes:
- **Mode A — Diff / Change Review**: Reviews uncommitted work, staged diffs, a feature branch, or a specific commit range.
- **Mode B — Whole-Codebase / Module Audit**: Reviews an entire repository, package, or directory from top to bottom without relying on Git diffs.

## Table of Contents

- [Triggers](#triggers)
- [Review Workflow](#review-workflow)
- [Mode A: Diff / Change Discovery](#mode-a-diff--change-discovery)
- [Mode B: Whole-Codebase / Module Discovery](#mode-b-whole-codebase--module-discovery)
- [Review Standards & Five-Axis Evaluation](#review-standards--five-axis-evaluation)
- [Structural Remedies & Hygiene](#structural-remedies--hygiene)
- [Change Sizing & Splitting Heuristics](#change-sizing--splitting-heuristics)
- [Critical Anti-Hallucination Guardrails](#critical-anti-hallucination-guardrails)
- [Output Format](#output-format)

---

## Triggers

Activate this skill whenever:
- The user asks for a **local code review**, **diff review**, **branch review**, or **pre-commit / pre-push review**.
- The user asks to **review the whole codebase**, **audit a repository**, or **review a specific module/directory**.
- You or another agent have completed a non-trivial feature, refactor, or bug fix and need a structured quality gate before committing or merging.
- The user pastes a diff inline or asks to review changes in a project that does not use GitHub Actions (e.g. Bitbucket or local repositories).

---

## Review Workflow

Copy and follow this checklist in order:

```text
Local Review Progress:
- [ ] Step 1: Select review mode (Mode A: Diff Review vs Mode B: Whole-Codebase Audit) and gather target files
- [ ] Step 2: Load repository rules, core documentation, and architectural context
- [ ] Step 3: Evaluate tests, documentation alignment, and visual assets
- [ ] Step 4: Perform the Five-Axis Evaluation & check structural remedies
- [ ] Step 5: Verify findings against actual file contents on disk (anti-hallucination pass)
- [ ] Step 6: Present severity-ranked review and offer to apply fixes
```

### Step 1: Select Mode & Gather Target Files

Determine whether the user wants a **Diff / Change Review (Mode A)** or a **Whole-Codebase / Module Audit (Mode B)**:
- Choose **Mode B (Whole-Codebase Audit)** if the user explicitly asks to review the whole codebase/project/module, if there is no Git repository, or if the working tree is clean on the default branch (`main`/`master`) with no commit range specified.
- Choose **Mode A (Diff Review)** if the user asks to review recent changes, uncommitted work, a branch, or a PR/commit range, or if `git status --short` / `git diff` shows active local work.

Follow the corresponding discovery procedure below ([Mode A](#mode-a-diff--change-discovery) or [Mode B](#mode-b-whole-codebase--module-discovery)).

### Step 2: Assemble Project & Domain Context

Always load the repository's rules and architectural intent before judging code:

1. **Project Guidelines & Core Docs**:
   - Read `AGENTS.md`, `GEMINI.md`, or `CLAUDE.md` (at root or `.agents/`) to learn repository-specific conventions, coding standards, and architectural rules.
   - Read `README.md`, `ARCHITECTURE.md`, `DESIGN.md`, `SPEC.md`, `TODO.md`, and package manifests (`pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, etc.) where present.
2. **Custom Review Instructions**:
   - Check for optional repository-specific reviewer guardrails in `review-instruction-additions.md`, `.agents/review-instructions.md`, or `.github/review-instruction-additions.md`.
3. **Domain Skills & Official Documentation**:
   - Check if any installed workspace or global agent skills apply to the technologies used in the project.
   - If the code touches Google Cloud (Cloud Run, GKE, BigQuery, Cloud Logging, IAM), Firebase, Vertex AI, or Gemini SDKs, use the Google Developer Knowledge MCP tools (`search_documents`, `get_documents`) to verify current API best practices and model identifiers.

### Step 3: Evaluate Tests, Documentation, & Visual Assets

1. **Review Tests & Verification Coverage**:
   - Do tests exist for the critical behaviours and edge cases?
   - Do they test **actual behaviour** rather than mocking away implementation details?
   - **Active Verification**: Run the test suite locally if fast and safe. For critical logic changes, check whether inverting a key condition causes a test failure; a condition that can be inverted while the test suite stays green reveals a missing test case.
2. **Holistic Documentation & Configuration Review**:
   - Verify that `README.md`, `ARCHITECTURE.md`, `TODO.md`, CLI help text, and deployment/config files accurately reflect the implementation on disk. Flag documentation drift or stale instructions as concrete findings.
3. **Multimodal & Visual Inspection**:
   - Inspect any added, modified, or Markdown-referenced image assets and architectural diagrams (`![...](path/to/diagram.png)`) using multimodal file viewing.
   - In **Mode A**, compare modified images against their baseline (`git show <base>:<path>`) to check for visual regressions.
   - In **Mode B**, verify that architecture/design diagrams match the actual module structure and data flows in the codebase.

---

## Mode A: Diff / Change Discovery

When reviewing a changeset:

1. **Inspect Working Tree & Untracked Files**:
   - Run `git status --short` to identify modified, staged, and **untracked (`??`)** files.
   - Standard `git diff` ignores untracked files. Always read untracked source, test, and documentation files that are part of the new work.
2. **Resolve the Diff Target**:
   - **Explicit ref/branch/commit**: Run `git diff <ref>...HEAD` (or `git diff <commit>`).
   - **Uncommitted working tree changes**: Inspect both staged (`git diff --cached`) and unstaged (`git diff HEAD`) changes.
   - **Feature branch with a clean working tree**: Compare against the default branch (`git diff main...HEAD` or `git diff master...HEAD`).
3. **Read Full Current Files & Direct Neighbours**:
   - Read the **full current file content** of every modified file (not just the diff hunk) plus direct callers/imports so you understand surrounding control flow and line numbers.
4. **Filter Noise**:
   - Skip generated lockfiles (`uv.lock`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `cargo.lock`, `go.sum`), binaries, minified bundles (`*.min.js`), and encrypted secrets (`*.enc`, `.env`), except to confirm lockfile synchronisation when manifests change.
5. **Diff Scope Discipline**:
   - Focus inline findings on the changed lines and their direct blast radius (broken callers, missing tests, or doc drift caused by the diff).

---

## Mode B: Whole-Codebase / Module Discovery

When reviewing an entire codebase or specific directory without relying on Git diffs:

1. **Inventory the Codebase**:
   - If inside a Git repository, run `git ls-files` to list tracked files cleanly. If not a Git repository, list files recursively while excluding `.git/`, `.venv/`, `venv/`, `node_modules/`, `dist/`, `build/`, `__pycache__/`, lockfiles, and binary/encrypted files.
   - If the user scoped the review to a specific package or directory, restrict the primary inventory to that path while still reading root guidelines (`AGENTS.md`, `README.md`, `pyproject.toml`).
2. **Systematic Top-Down Traversal**:
   - Group and inspect files in logical architectural order:
     1. **Manifests, Entrypoints & Configuration** (`pyproject.toml`, CLI/app entrypoints, config loaders, CI/deployment configs).
     2. **Core Domain & Business Logic Modules** (data models, schemas, core services, state machines, prompts/agents).
     3. **External Boundaries & Integrations** (API clients, database queries, auth, file I/O, shell execution).
     4. **Shared Utilities & Helpers** (checking for cross-module duplication, leaky abstractions, or dead helpers).
     5. **Test Suite & Fixtures** (assessing coverage gaps, brittle mocks, and missing edge-case tests).
     6. **Documentation & Visual Diagrams** (`README.md`, `ARCHITECTURE.md`, `docs/*.md`, and embedded images).
3. **Cross-Cutting Synthesis**:
   - In Whole-Codebase Mode, evaluate systemic patterns across files—such as inconsistent error handling, duplicated logic across modules, circular dependencies, unreferenced dead code across the repo, security boundary gaps, and mismatches between `ARCHITECTURE.md` and the code.

---

## Review Standards & Five-Axis Evaluation

### Review Philosophy & Approval Bar

- **Continuous Code Health Improvement**: Approve changes or modules when they maintain or improve overall codebase health, even if not perfect. Do not Nit-pick purely stylistic preferences when project conventions are followed.
- **Lead with Leverage**: Order findings by impact—correctness and security first, then structural/architectural flaws and missed simplifications, then minor nits last. Never bury a high-conviction structural issue under a long list of cosmetic suggestions.

### The Five Quality Axes

Evaluate systematically across five core engineering dimensions:

1. **Correctness & Verification**:
   - Does the code accurately fulfil requirements and specifications?
   - Are edge cases (`None`/`null`, empty inputs, boundary conditions, network/API timeouts) and error paths handled cleanly?
   - Are there off-by-one errors, race conditions, resource leaks, or state inconsistencies?
   - Do tests validate actual behaviour rather than implementation details?
2. **Readability & Simplicity**:
   - Are variable, function, and type names descriptive and consistent with project conventions?
   - Is control flow straightforward (avoiding nested ternaries, deep nesting, or clever tricks)?
   - **Could this be expressed in significantly fewer lines?**
   - **Are abstractions earning their complexity?** (Do not generalise until the third use case.)
   - **Is a conditional bolted onto an unrelated flow?** Push it into its own helper, state, or policy rather than tangling an existing path.
   - **Do repeated conditionals on the same data shape appear?** Signals a missing model, polymorphism, or dispatcher.
3. **Architecture & System Design**:
   - Does the code maintain clean module boundaries and unidirectional dependencies (no circular imports)?
   - **Does a refactor or abstraction reduce complexity or merely relocate it?** Count the concepts a reader must hold in working memory. Prefer designs that make whole branches, modes, or layers disappear over shifting the same logic around. Prefer deleting an unused abstraction to polishing it.
   - **Is feature-specific logic leaking into a shared utility module?** Keep domain logic in its owning layer and reuse canonical helpers instead of creating bespoke near-duplicates.
   - **Are type boundaries explicit?** Question gratuitous `Any`/`any` casts or silent fallbacks that paper over broken invariants.
4. **Security & Data Hardening**:
   - Is external input (CLI arguments, HTTP payloads, environment/config files, LLM outputs, remote URLs) treated as untrusted and validated/sanitised at system boundaries?
   - Are dynamic file paths protected against path traversal (e.g. `os.path.commonpath`)?
   - Are secrets excluded from source code, logs, command-line flags, and version control?
   - Are database queries parameterised and rendered outputs safely encoded?
5. **Performance & Efficiency**:
   - Are there $O(N^2)$ lookups, N+1 queries, unbounded loops, or unconstrained memory/file reads in hot paths?
   - Are synchronous blocking operations avoided in async event loops?
   - Are external network/API requests configured with explicit timeouts, retries, and pagination?

---

## Structural Remedies & Hygiene

### Named Structural Remedies

When flagging a structural or architectural problem, always propose the concrete restructuring move rather than simply stating that code is "complex":
- **Replace conditional chains** with a typed model, lookup table, or explicit dispatcher.
- **Collapse duplicate branches** into a single clear flow.
- **Separate orchestration from business logic** so each reads and tests independently.
- **Move feature-specific logic** out of shared modules into the owning package.
- **Reuse canonical helpers** instead of creating bespoke near-duplicates across modules.
- **Make type boundaries explicit** at ingress so downstream defensive branching disappears.
- **Delete pass-through wrappers** that add indirection without clarifying the interface.
- **Decompose oversized files** into focused modules with clear single responsibilities.

### Dead Code Hygiene

Actively identify orphaned code (both after refactors in Mode A and across modules in Mode B):
- Flag unreachable functions, unused helpers/imports/constants, no-op variables (`_unused`), obsolete compatibility shims, or commented-out blocks.
- List them explicitly with `file:line` references and ask before deleting: *"Safe to remove these unused elements?"*

### Dependency Discipline & Upgrades

- **Dependency Footprint**: Prefer the standard library and existing project dependencies. Evaluate any external dependency on necessity, footprint, active maintenance, security vulnerabilities, and licence compatibility.
- **Upgrading Dependencies**:
  1. Check changelogs and migration notes rather than relying blindly on semver.
  2. Prefer single-package upgrades over bulk unrelated bumps so regressions are trivial to isolate.
  3. Verify with the test suite and inspect lockfile diffs for unintended transitive shifts.

### Common Rationalisations to Reject

| Rationalisation | Reality |
| :--- | :--- |
| *"It works, that's good enough"* | Working code that is unreadable, insecure, or architecturally wrong creates compounding debt. |
| *"We'll clean it up later"* | Deferred cleanup rarely happens. Address structural debt now unless responding to a live outage. |
| *"The refactor makes it cleaner"* | Relocating complexity is not reducing it. Look for the design where branches or concepts disappear. |
| *"It's only a small addition to this file"* | Small additions still push large files past healthy boundaries and bolt branches onto unrelated flows. |
| *"It's just a version bump"* | Dependency upgrades carry behavioural changes you did not write; verify changelogs and tests. |

---

## Change Sizing & Splitting Heuristics

- **Diff Size (Mode A)**:
  - `~100 lines changed`: Ideal—reviewable with high confidence in one sitting.
  - `~300 lines changed`: Acceptable for a single cohesive logical change.
  - `~1,000+ lines changed`: Too large (unless automated formatting or bulk deletion); recommend splitting.
  - **Separate refactoring from behaviour changes**: Reorganising existing code and adding new behaviour should be separate commits/PRs.
- **File Size (Mode A & Mode B)**:
  - Around `~1,000 total lines` in a single source file is a strong decomposition signal. When a file exceeds or approaches this boundary with multiple responsibilities, recommend extracting focused sub-modules.
- **Splitting Strategies**:
  - **Stack**: Foundational change first, dependent change stacked on top.
  - **Horizontal**: Shared models/interfaces first, consumers second.
  - **Vertical**: Smaller end-to-end slices of functionality.
  - **By File Group**: Separate cross-cutting subsystem changes.

---

## Critical Anti-Hallucination Guardrails

1. **Always Verify Full File Contents on Disk**:
   - Never report duplicate functions, redundant routes, or missing imports based solely on a partial snippet or diff hunk. In Mode A, a function deleted in one place and added in another is **moved**, not duplicated. Always verify the actual file on disk and cite exact 1-based line numbers.
2. **Fact-Based Findings Only**:
   - Only report verifiable bugs, security risks, architectural smells, test gaps, or concrete improvements. Do **not** add filler comments that merely explain what the code does or ask the author to *"check/verify if X works"* without a concrete defect.
3. **No Sweeping or Universal Claims**:
   - Never make universal assertions (e.g. *"all endpoints validate input"* or *"all dependencies are pinned"*) unless every single occurrence across the target scope has been verified. State precisely which files or functions were checked.
4. **No Version or Model Downgrades**:
   - Never suggest downgrading Gemini models (e.g. `gemini-3.8-flash` to `gemini-2.5-flash`), SDK versions, or language targets due to training cut-off dates. Treat newer version identifiers as valid.
5. **No Command Substitution in Suggested Shell Commands**:
   - Avoid `$(...)` or backticks in suggested shell commands to prevent unintended command execution and keep commands prefix-matchable.
6. **Language & Spelling**:
   - Write all review commentary in **English (UK)** unless project rules specify otherwise. Never flag valid US English spelling in code identifiers or third-party APIs as a typo.

---

## Output Format

Format your review in clean GitHub-Flavored Markdown using **relative file links** (never `file:///` URIs):

### 1. Executive Summary & Verdict
- **Mode & Scope Reviewed**: State whether **Mode A (Diff Review)** or **Mode B (Whole-Codebase / Module Audit)** was executed, the files/branches covered, and whether tests were run.
- **Summary**: Concise assessment (3–6 sentences) covering overall code health, architecture, test coverage, and documentation/diagram alignment.
- **Verdict**: `✅ Approve / Healthy`, `⚠️ Approve with Minor Suggestions`, or `🔴 Request Changes / Action Required`.

### 2. Architectural & Holistic Observations
- System-level patterns, cross-module design observations, positive engineering highlights, documentation/diagram sync status, and any **Dead Code Identified** (with `file:line` locations).

### 3. Findings (Ordered by Leverage & Severity)
Prefix every finding with its severity badge so required vs optional actions are unmistakable:
- `🔴 Critical`: Security vulnerability, data loss, crash, or broken core functionality (must fix).
- `🟠 High`: Bug, missing error/edge-case handling, missing test coverage, or significant architectural flaw (should fix).
- `🟡 Medium`: Simplification opportunity, structural smell, module boundary leak, or documentation drift.
- `🟢 Low (Nit)`: Minor readability, naming, or idiomatic polish (optional).

For each finding, provide:
- **Location**: Clickable relative link with exact line numbers, e.g. [`gemini_review/context.py:171-195`](gemini_review/context.py#L171-L195).
- **Issue & Structural Remedy**: Direct, quantified explanation of the problem and the named remedy.
- **Suggested Fix**: Clean drop-in replacement code block (without line-number prefixes).

### 4. Interactive Next Steps
Conclude by asking the user which findings, refactorings, or dead-code removals they would like you to apply directly.

