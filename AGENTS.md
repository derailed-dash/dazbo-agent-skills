# Repository Guidelines (`dazbo-agent-skills`)

Public collection of portable, self-contained AI agent skills authored by Dazbo (`derailed-dash`) and distributed via [Skills.sh](https://skills.sh/derailed-dash/dazbo-agent-skills) (`npx skills add https://github.com/derailed-dash/dazbo-agent-skills`).

## Key References

- **Storefront & Catalogue**: [README.md](README.md) (`Available Skills` table, `npx` install commands, project tree, and companion articles)
- **Skill Entrypoints**: `skills/<skill-name>/SKILL.md` (with optional `scripts/` and `references/` subdirectories)
- **Test & Lint Harness**: [Makefile](Makefile), [pyproject.toml](pyproject.toml), and `tests/unit/`
- **CI & Automated Review**: [.github/workflows/pr-checks.yml](.github/workflows/pr-checks.yml), [.github/workflows/gemini-review.yml](.github/workflows/gemini-review.yml), and [.github/workflows/gemini-triage.yml](.github/workflows/gemini-triage.yml)
- **Upstream Format**: [Agent Skills Open Specification (`agentskills.io`)](https://agentskills.io)

## Skill Authoring Principles

- **Naming & Frontmatter**: Use clear kebab-case folder names (preferring `verb(ing)-noun` or explicit action-noun phrasing). Every `SKILL.md` must begin with YAML frontmatter where `name` matches the folder name, `description` is written in the **3rd person** with explicit `"Use when..."` activation triggers (and `"Don't use..."` boundaries when helpful), and `metadata` sets `author: Dazbo (GitHub: derailed-dash)` and `repository: https://github.com/derailed-dash/dazbo-agent-skills` (plus optional `cli` dependencies).
- **Plain-English Opening**: Start every `SKILL.md` with `# Heading 1` followed immediately by 1–2 plain-English paragraphs explaining *what* the skill does and *how* it works conceptually before introducing dense tables, flags, or rubrics.
- **Progressive Disclosure**: Keep `SKILL.md` under **500 lines**. Move templates, samples, and deep reference tables into `references/` (linked via Unix-style relative paths for on-demand reading), and place reusable deterministic utilities into `scripts/` (documenting expected arguments, prerequisites, and output format). Add a `## Table of Contents` whenever `SKILL.md` or a reference Markdown file exceeds **100 lines**.
- **High-Signal Guidance**: Assume a capable frontier model — omit generic explanations the model already knows. Prefer numbered workflows with explicit intermediate validation steps, deterministic commands for low-freedom tasks, and a single recommended path rather than competing options.
- **Portable Script & Tool References**: Reference bundled scripts via installed skill paths (`~/.gemini/config/skills/<skill-name>/scripts/...` and `.agents/skills/<skill-name>/scripts/...`) rather than assuming execution from a clone of this repository. When referencing MCP tools, identify both the MCP server and tool name clearly rather than bare tool names.

## Repository Invariants (`B1`–`B8`)

- **B1** `[det]`: Every `skills/<skill-name>/SKILL.md` stays strictly under `500` lines, has YAML `name` matching `<skill-name>` and a 3rd-person `"Use when..."` `description`, and includes `## Table of Contents` whenever over `100` lines.
- **B2** `[det]`: Every Markdown heading (`#`–`####`) is followed immediately by a blank line, fenced code blocks close cleanly (use `~~~~` outer fences when nesting triple-backtick examples), and internal `#anchor` links resolve to valid GitHub-flavoured slugs.
- **B3** `[det]`: All prose, documentation, and comments use **English (UK)** spelling (e.g. `synchronise`, `organise`, `artefacts`, `initialisation`, `summarise`) and pass `uv run codespell -s`.
- **B4** `[det]`: Markdown files use relative links only (never `file:///` URIs) and wrap literal dollar amounts in inline backticks (e.g. `` `$0` ``) rather than backslash-escaping `\$0`.
- **B5** `[det]`: Zero `mermaid` blocks or ASCII/Unicode box-drawing diagrams appear in any file (generate PNG/SVG image assets when architecture or workflow diagrams are needed).
- **B6** `[det]`: Python utilities under `skills/*/scripts/` use Python `>= 3.12` modern type hints (`list[str]`, `str | None`), include a top-of-module docstring, are registered in `[tool.ruff]` and `[tool.pyright]` in [pyproject.toml](pyproject.toml) with unit tests under `tests/unit/`, and pass `make check`.
- **B7**: Adding, renaming, or materially changing a skill updates [README.md](README.md) (`Available Skills` table, `npx skills add` list, and `Project Structure` tree) in the same change.
- **B8**: Public-repository hygiene — never commit credentials, API keys, personal cloud project IDs, or machine-private local paths.

## Verification

Run the offline static and unit-test gate from the repository root before committing:

```bash
make check    # codespell, ruff check, ruff format --check, pyright, and pytest
make fix      # auto-apply codespell and ruff fixes
```
