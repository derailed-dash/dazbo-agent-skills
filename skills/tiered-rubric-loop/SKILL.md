---
name: tiered-rubric-loop
description: |
  Drops a combined deterministic and semantic rubric verification loop into any
  project, acting as the loop component of an agentic harness. Automatically
  leverages existing Spec-Driven Development (SDD) and Test-Driven Development
  (TDD) artefacts - or creates lightweight ones inline - routing each check across
  fast Tier 1 deterministic gates, Tier 1.5 calibrated scoring via the Gemini
  Decisions API (fast and 0 output tokens), and a Tier 2 stateless semantic 
  critique only for 1.5 escalations or complex `[arch]` invariants. 
  Use when running iterative implementation/refinement loops, gating
  PRs or complex slices against `B1`–`Bn` assertions (`SPEC.md` / `LOOPS.md`),
  or scoring diffs and multimodal diagrams.
metadata:
  author: Darren "Dazbo" Lester
  repository: https://github.com/derailed-dash/dazbo-agent-skills
  cli:
    - uv
---

# Tiered Rubric Loop (`tiered-rubric-loop`)

A fast, loosely coupled way to drop a combined **deterministic + semantic verification loop** into any repository as the verification engine of an agentic harness.

It automatically reuses any **Spec-Driven Development (SDD)** (`docs/SPEC.md` or `SPEC.md`) and **Test-Driven Development (TDD)** artefacts already in the repo, or bootstraps a lightweight `B1–Bn` binary rubric checklist inline if none exist.

Instead of waking an expensive reasoning subagent on every single pass, or trusting a zero-thinking classifier blindly on deep security and concurrency invariants, each assertion flows through three escalating stages:

1. **Tier 1 — Deterministic Checks (fast)**: Runs local linters, typecheckers, and unit tests (`make check`, `codespell`, `ruff`, `pyright`, `pytest`) first. Any failure stops the pass immediately so you never waste API calls on broken code.
2. **Tier 1.5 — Fast Semantic Scoring (fast model, no output tokens)**: Evaluates open binary (`yes`/`no`) rubric criteria (`B1–Bn`) in a single prefill pass using the **Gemini Decisions API** (`gemini-decision-1` via [`scripts/eval_rubric.py`](scripts/eval_rubric.py)). Straightforward editorial and doc-sync checks pass immediately, while obvious omissions fail fast without waking a subagent.
3. **Tier 2 — Stateless Semantic Critique**: Spawns a fresh, read-only reviewer subagent *only* when Tier 1.5 is uncertain ("grey zone"), or for complex architectural and security invariants (`[arch]`) that need deeper multi-file reasoning.

## Table of Contents

- [How the 3-Stage Funnel Works](#how-the-3-stage-funnel-works)
- [Plain-Markdown `B1`–`Bn` Contract & Tagging](#plain-markdown-b1bn-contract--tagging)
- [Loose Coupling & Companion Skills Matrix](#loose-coupling--companion-skills-matrix)
- [Bounded Loop Workflow](#bounded-loop-workflow)
- [Running Tier 1.5 (`eval_rubric.py`)](#running-tier-15-eval_rubricpy)
- [Threshold Routing & Stateless Tier 2 Critic](#threshold-routing--stateless-tier-2-critic)
- [Circuit Breaker Trio & Continuous Ratchet](#circuit-breaker-trio--continuous-ratchet)
- [Loop Receipt Format](#loop-receipt-format)

---

## How the 3-Stage Funnel Works

| Tier | Mechanism | Latency & Cost | What It Owns |
| :--- | :--- | :--- | :--- |
| **Tier 1 (Deterministic)** | Local linters, typecheckers, unit tests (`make check`, `codespell`, `ruff`, `pyright`, `pytest`) | Seconds, **`$0`** | Syntax, static types, formatting, and deterministic test execution. Any failure **short-circuits immediately** before Tier 1.5 or Tier 2 runs. |
| **Tier 1.5 (Calibrated Probabilistic)** | `gemini-decision-1` via `client.decisions.create` (`v1beta`) in [`scripts/eval_rubric.py`](scripts/eval_rubric.py) | **~150–250 ms**, **`$0.10` / 1M input tokens**, **0 output / thinking tokens** | Evaluates up to 1,000 closed-ended `noul` (yes/no) assertions over a single shared diff/spec/media payload. Terminates clear mechanical passes (`PASS`), rejects obvious omissions immediately (`FAIL_FAST`), and flags uncertain items for L2. |
| **Tier 2 (Stateless Semantic Critic)** | Fresh read-only subagent (`Model: "flash"` for mechanical grey-zones; `Model: "inherit"` — or `Model: "pro"` for frontier escalation — on `[arch]` items) with zero prior coding chain-of-thought | 10–40 s, standard model tokens | Diagnoses grey-zone escalations and performs **one final L2 sign-off** on `[arch]` items after Tier 1.5 is green. |

**Key safety rule**: Because `gemini-decision-1` runs in a single prefill forward pass with **zero thinking tokens** and **zero file-reading tools**, it can produce false positives on subtle logic, race conditions, or auth flaws. Therefore, Tier 1.5 is **terminal** for mechanical/editorial checks, **fail-fast** on clear omissions, and **provisional** for `[arch]` assertions.

---

## Plain-Markdown `B1–Bn` Contract & Tagging

The sole shared contract is a Markdown table or bullet list of numbered binary assertions (`B1–Bn`) in `docs/SPEC.md`, `SPEC.md`, or `LOOPS.md` (with optional `--spec <path>` override):

```markdown
| ID | Falsifiable Condition | Verification Target |
| :--- | :--- | :--- |
| `B1 [det]` | Static gates (`codespell`, `ruff`, `pyright`) and offline tests exit `0` | `make check` |
| `B2` | `.env.template` and `README.md` document every newly added variable and flag | Doc review |
| `B3 [arch]` | Auth middleware rejects expired tokens and never retries `4xx` responses | `tests/unit/test_auth.py` |
```

Other supported rubric formats and tags:

- **Bullet assertions**: `- **B4**: CLI help panel renders in English (UK)`
- **Atomic sub-IDs**: `B4a`, `B11b`
- **Numbered items**: ``1. `B5 [docs]`: ...``
- **Task checkboxes**: `- [ ] **B6 [concurrency]**: ...` or `- [x] **B6**: ...`
- **Extended tags**: `[mech]`, `[docs]`, `[ui]`, `[visual]`, `[perf]`, `[concurrency]` (unrecognised tags warn on `stderr` and default safely to `[mech]` instead of silently dropping the assertion)

| Tag | Meaning | Tier 1.5 Handling |
| :--- | :--- | :--- |
| `[det]` (or deterministic Verification Target such as `make check`, `pytest tests/...`, `codespell -s`, `ruff check .`) | Already proven by Tier 1 shell exit codes | **Skipped by Tier 1.5** by default (`--include-det` overrides) so the model never guesses whether `pytest` passed from a text diff. |
| *(untagged, `[mech]`, `[docs]`, `[ui]`, `[visual]`, `[multimodal]`)* | Mechanical, editorial, doc-sync, schema, or UI convention check | **Terminal `PASS`** when `P(yes) >= 0.90`, `confidence >= 0.80`, and **no evidence was truncated**; `FAIL_FAST` when `<= 0.20`; otherwise `ESCALATE_L2_FLASH`. |
| `[arch]` (also `[security]`, `[logic]`, `[concurrency]`, `[perf]`) | Concurrency, security, state invariant, performance, or test-realism check | **Provisional pass (`PROVISIONAL_ARCH_PASS`)** when confident (`Model: "inherit"` / `"pro"` final Tier 2 review); `FAIL_FAST` when `<= 0.20`; otherwise `ESCALATE_L2_ARCH` (`Model: "inherit"` / `"pro"`). |

Repo-relative file paths and local images named in `Verification Target` or inline backticks are **automatically resolved and attached** (blocking `.env`, secret env files, `*.enc`, and paths outside `--repo-root`; pass `--no-auto-target-files` to disable).

### Writing High-Signal `B1–Bn` Assertions

- **Keep assertions atomic**: Test **one falsifiable invariant per `Bi`** rather than bundling three functions or eight files into one question—single-invariant assertions give sharp `P(yes)` separation and trigger `FAIL_FAST` accurately on regressions.
- **Name concrete paths in `Verification Target`**: Prefer `src/auth.py, tests/unit/test_auth.py` over generic `Doc review` / `Code review` so `eval_rubric.py` auto-attaches untouched context files even in narrow working-tree diffs.
- **Separate canonical registries from summary copy**: Don't assert identical title formatting across both machine registries (`navigation.yaml`) and summarised overview pages (`README.md`, spotlight cards) unless exact parity is truly required.

---

## Loose Coupling & Companion Skills Matrix

`tiered-rubric-loop` requires **zero hard dependencies** on other skills and degrades cleanly when optional companions or API keys are absent:

| Companion Skill / Dependency | When Present | Standalone Fallback (When Absent) |
| :--- | :--- | :--- |
| `maintaining-core-documentation` / `spec-driven-development` | Reads `B1`–`Bn` directly from `docs/SPEC.md` or `SPEC.md`. | Reads any local `SPEC.md` / `LOOPS.md`, or asks you to agree a compact `B1`–`Bn` list inline before coding. |
| `test-driven-development` | Delegates the **Act** step to full Red-Green-Refactor execution. | Enforces the core TDD rule inline: write/update a failing test first, change one semantic behaviour per pass, never weaken assertions. |
| `loopy` | Supplies the outer `Observe -> Choose -> Act -> Verify -> Record -> Stop` governance, saved reusable loops in `LOOPS.md`, and conversation run receipts. | Runs the identical bounded loop directly with the receipt format below. |
| `local-code-review` | Stateless Tier 2 read-only subagent runs `local-code-review` on escalated/`[arch]` items. | Uses the built-in **Stateless Tier 2 Critic Prompt** below. |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Enables ~200 ms Tier 1.5 screening via `eval_rubric.py`. | When `eval_rubric.py` exits `3` (missing/invalid key or `429` quota/spend-cap block), skips Tier 1.5 cleanly and executes `Tier 1 -> Tier 2` directly while noting how to enable Tier 1.5. |

---

## Bounded Loop Workflow

Track every pass around **`Observe -> Choose -> Act -> Verify -> Record -> Stop`**:

1. **Observe**: Read the specification (`docs/SPEC.md`, `SPEC.md`, or `LOOPS.md`), `git status --short`, and current failing tests/checks. Confirm `B1`–`Bn` exist (draft and confirm them first if missing).
2. **Choose**: Pick **one** highest-value unverified semantic behaviour or failing assertion for this pass (mechanical lint/spelling fixes may be batched).
3. **Act (TDD)**: Write or update the failing test first (**Red**), confirm it fails, then implement the minimal clean change (**Green**) and refactor without weakening tests.
4. **Verify (3-Stage Funnel)**:
   - **Tier 1**: Run deterministic checks (`make check` or repo lint + test commands). If Tier 1 fails, **stop verification immediately** and return to **Choose/Act**—do not spend tokens on Tier 1.5 or Tier 2.
   - **Tier 1.5**: Run `eval_rubric.py --json` over the spec, diff, and touched files (plus `--image` / `--pdf` for diagram/UI specs).
   - **Tier 2**: Escalate only grey-zone items immediately, or run a single final `[arch]` critic pass once Tier 1.5 reports zero `FAIL_FAST` and zero grey-zone items.
5. **Record**: Track pass outcome, `ratchet_score` (mean `P(yes)`), and remaining failures in the conversation receipt (do not create or append to `LOOPS.md` by default; persist to disk only when requested or required by an established project convention).
6. **Repeat or Stop**: Enforce the **Circuit Breaker Trio** before starting another pass.

---

## Running Tier 1.5 (`eval_rubric.py`)

Resolve `scripts/eval_rubric.py` relative to where `tiered-rubric-loop` is installed:
- Global Antigravity path: `~/.gemini/config/skills/tiered-rubric-loop/scripts/eval_rubric.py`
- Project-local path: `.agents/skills/tiered-rubric-loop/scripts/eval_rubric.py`

In sandboxed agent runtimes that block outbound HTTPS by default, invoke `uv run` with unsandboxed network permission (`BypassSandbox: true` in Antigravity) for live API calls, or pass `--offline` for sandboxed `--dry-run` checks.

```bash
# 1. Working-tree loop: auto-discover SPEC.md / docs/SPEC.md / LOOPS.md
uv run ~/.gemini/config/skills/tiered-rubric-loop/scripts/eval_rubric.py --json

# 2. Branch or merged PR gating: evaluate committed changes against base ref / range
uv run ~/.gemini/config/skills/tiered-rubric-loop/scripts/eval_rubric.py --base main --json
uv run ~/.gemini/config/skills/tiered-rubric-loop/scripts/eval_rubric.py \
  --git-range origin/main...HEAD \
  --only B3,B4 \
  --json

# 3. Explicit spec, scoped files, and multimodal diagram/UI screenshot check
uv run ~/.gemini/config/skills/tiered-rubric-loop/scripts/eval_rubric.py \
  --spec docs/SPEC.md \
  --file src/auth.py \
  --image docs/images/architecture.png \
  --json

# 4. Offline dry-run inside sandbox (verifies rubric, targets, and truncation zero-API)
uv run --offline ~/.gemini/config/skills/tiered-rubric-loop/scripts/eval_rubric.py --dry-run --json
```

Default caps (`--max-file-chars 48000`, `--max-evidence-chars 500000`) fit most multi-file reviews in a single batched pass within `gemini-decision-1`'s `262k`-token window. Target files referenced by the evaluated assertions are attached ahead of general working-tree diffs, and `--targets-only` or `--only B3,B4` keeps huge PRs uncluttered. If any source relevant to a mechanical assertion is truncated, `eval_rubric.py` populates `truncated_sources` and **downgrades mechanical `PASS` to `ESCALATE_L2_FLASH`** unless `--allow-truncated-pass` is explicitly set.

### Exit Codes

| Code | Meaning | Loop Action |
| :--- | :--- | :--- |
| `0` | Tier 1.5 clear (all evaluated items are `PASS` or `PROVISIONAL_ARCH_PASS`) | If `final_l2_arch_ids` is non-empty, run **one** Tier 2 (`Model: "inherit"`, or `Model: "pro"` for frontier escalation) critic pass on those IDs; otherwise exit loop as **`Success`**. |
| `1` | One or more `FAIL_FAST`, `ESCALATE_L2_FLASH`, or `ESCALATE_L2_ARCH` items (or API call error) | Address `FAIL_FAST` items directly; escalate grey-zone items (`ESCALATE_L2_FLASH` / `ESCALATE_L2_ARCH`) only when root cause is non-obvious. |
| `2` | Usage error, missing spec, or no `B1`–`Bn` assertions parsed | Fix spec path or rubric formatting before continuing. |
| `3` | Missing/invalid `GEMINI_API_KEY` / `GOOGLE_API_KEY` or `429` quota/spending-cap block | Degrade gracefully to **`Tier 1 -> Tier 2`** and inform the user once. |

---

## Threshold Routing & Stateless Tier 2 Critic

Default calibrated thresholds (overridable via `--pass-threshold`, `--fail-threshold`, `--min-confidence`):
- **`PASS`** (`P(yes) >= 0.90`, `confidence >= 0.80`, mechanical): **Terminal pass.** No L2 model runs.
- **`PROVISIONAL_ARCH_PASS`** (`P(yes) >= 0.90`, `confidence >= 0.80`, `[arch]`): Held until all other assertions pass, then verified once by a Tier 2 (`Model: "inherit"`, or `Model: "pro"` for frontier escalation) critic.
- **`FAIL_FAST`** (`P(yes) <= 0.20`, `confidence >= 0.80`): Returned directly to the coding agent—do **not** burn an L2 turn repeating an obvious omission.
- **`ESCALATE_L2_FLASH`** (`0.20 < P(yes) < 0.90` or `confidence < 0.80`, mechanical) & **`ESCALATE_L2_ARCH`** (`[arch]`): Escalate **only those specific `Bi` IDs** to a fresh read-only subagent (`Model: "flash"` for `ESCALATE_L2_FLASH`; `Model: "inherit"` — or `Model: "pro"` — for `ESCALATE_L2_ARCH`).

### Subagent Routing Across Coding Agents

Always spawn Tier 2 as a **fresh, stateless, read-only subagent** that never sees the coding agent's prior chain-of-thought or failed attempts. In **Antigravity**, call `invoke_subagent` with `TypeName: "research"` and `Model: "flash"` for mechanical grey-zone escalations, or `Model: "inherit"` (or `Model: "pro"` to escalate to frontier judgement from a faster orchestrator like Neon) for `[arch]` escalations and final `[arch]` sign-off.

### Built-In Stateless Tier 2 Critic Prompt

Pass this exact prompt (filling in only the target `Bi` IDs, spec path, and changed files):

```text
You are a stateless, read-only Tier 2 semantic critic. You have NOT seen the
coding session and must judge solely from the specification and actual files on disk.

Evaluate ONLY these rubric assertions: [INSERT B_i IDs AND CONDITIONS].
Read: [SPEC.md / docs/SPEC.md] and inspect the changed/untracked files + git diff.

Rules:
1. Cite exact file paths, line numbers, and observed code/test behaviour.
2. Check whether tests verify real behaviour rather than mocking away logic.
3. For each assertion ID, return PASS or FAIL with a concise root-cause note.
4. Do not invent fixes or assume uninspected files pass.
```

---

## Circuit Breaker Trio & Continuous Ratchet

Stop the loop whenever **any** of these three conditions triggers:

1. **100% Pass**: Tier 1 passes, Tier 1.5 reports `exit_code == 0`, and any `final_l2_arch_ids` clear their final Tier 2 (`Model: "inherit"` / `"pro"`) review (**`Success`**).
2. **Pass Budget Exhausted**: Maximum **4–5 passes** per slice reached (**`Exhausted`**—escalate remaining blockers to the user).
3. **2 Consecutive Non-Improving Passes**: Neither failing assertion count decreases **nor** `ratchet_score` (mean `P(yes)` across evaluated `B1`–`Bn` items) improves across two consecutive passes (**`No progress`**—escalate to the user rather than spinning).

Tracking the continuous `ratchet_score` avoids premature stalls when a pass genuinely moves an assertion from e.g. `P(yes) = 0.25` to `0.82` while still short of `0.90`, and catches silent regressions immediately.

---

## Loop Receipt Format

Return completed run receipts concisely in the conversation (persist to disk only when explicitly requested or when an established project convention uses a receipt file — keep `LOOPS.md` for saved reusable loop definitions and `B1`–`Bn` rubrics):

```markdown
## Tiered Rubric Loop Receipt

- **Target**: [Slice / Feature / PR]
- **Spec**: [docs/SPEC.md] (`B1`–`Bn`)
- **Passes**: [N / 5] | **Outcome**: `Success` | `Exhausted` | `No progress` | `Blocked`
- **Tier 1**: `make check` -> PASS
- **Tier 1.5 Ratchet (`gemini-decision-1`)**: `0.58 -> 0.94 -> 0.98` (skipped `[det]`: `B1`)
- **Tier 2 (`Model: "inherit"`)**: Verified `[arch]` IDs `B3` -> PASS
- **Remaining / Escalation**: None (or exact failing `Bi` + file:line)
```
