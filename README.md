# Dazbo's Agentic Skills

This repository serves as a public collection of agentic skills developed for AI agents and assistants. These skills extend the capabilities of AI agents by providing specialised instructions, workflows, and templates for various tasks such as documentation maintenance, content creation, diagrams, and more.

## Repo Metadata

- Author: Dazbo (GitHub: derailed-dash)
- Repository: https://github.com/derailed-dash/dazbo-agent-skills

## Install Count

According to [Skills.sh](https://skills.sh/), these skills have been installed:

[![skills.sh](https://skills.sh/b/derailed-dash/dazbo-agent-skills)](https://skills.sh/derailed-dash/dazbo-agent-skills)

## Table of Contents

- [What is a Skill?](#what-is-a-skill)
- [Available Skills](#available-skills)
  - [Installation Instructions](#installation-instructions)
  - [Skills Documentation](#skills-documentation)
- [Project Structure](#project-structure)
- [Blogs](#blogs)

## What is a Skill?

Think of it as on-demand knowledge or capability, loaded by your agent as needed, to do a thing. A great analogy is how our heroes in The Matrix can instantly install knowledge... _"I know Kung-Fu!"_

## Available Skills

| Skill | Purpose & Value | When to Use & Triggers |
| :--- | :--- | :--- |
| **Project Documentation** | End-to-end framework for managing, structuring, and synchronising repository docs using progressive disclosure, strict single-source-of-truth boundaries, and OKF v0.2 frontmatter. Prevents documentation rot and context bloat. | **Use when** modifying features, system architecture, tests, or deployment. Guides the creation and targeted synchronisation of `README`, `TODO`, `PRD`, `SPEC`, `ARCHITECTURE`, `DESIGN`, `TESTING`, `GUIDE`, and `Deployment`. |
| **Deploying Skills** | Automated installer, relocator, and manager for Antigravity/Gemini agent skills. Saves time by managing local and global paths, and auto-registering newly deployed skills into `skills.json`. | **Use when** downloading, importing, or updating new agent skills. Automates the installation process via `npx`, safely moves skills to the shared global path (`~/.gemini/config/skills/`), and registers new skills into `skills.json`. |
| **Convert to Dev.to** | Formatter that prepares standard Markdown files for publishing on Dev.to. Ensures metadata and syntax compatibility without manual formatting. | **Use when** preparing technical articles for Dev.to. Automates insertion of YAML frontmatter, liquid syntax conversion, variable formatting, and heading structures. |
| **Secrets with Git-Crypt** | Production-grade secrets management workflow. Keeps plaintext files safely gitignored while tracking encrypted versions (`.enc`) in Git. | **Use when** managing `.env`, `*.tfvars`, or sensitive keys. Employs a helper sync script to maintain parallel encrypted copies, avoiding accidental leak of credentials. |
| **Create MD from BrowserMCP Snapshot** | High-fidelity parser to convert raw webpage accessibility trees to structured Markdown. Makes parsed web pages easy for agents to read and search. | **Use when** a webpage has been captured with the BrowserMCP `browser` (`snapshot`) tool. Runs a Python parser to reconstruct structured representations of headings, tables, lists, and links. |
| **Fix WSL Browser Agent** | Diagnostic and remediation workflow for Antigravity's native `browser` subagent and Chrome DevTools MCP in WSL2 environments. Bridges Windows Chrome `DevToolsActivePort` into WSL2 while avoiding sandbox symlink (`ELOOP`) traps. | **Use when** the native `browser` subagent or `chrome-devtools` MCP fails to connect to Chrome in WSL2 (e.g. `Could not find DevToolsActivePort`, `ELOOP` symlink errors, or port `9222` unreachable). |
| **Install [Gemini Code Review Action](https://github.com/derailed-dash/gemini-review-action)** | Automated setup for Dazbo's Gemini-based PR Code Review & Issue Triage action. Streamlines setup and configures secure API credentials.  <br><br>Great for any new projects where you want automated code reviews in your CI/CD pipeline. | **Use when** setting up automated Gemini-based pull request code reviews or issue triaging workflows in a GitHub repository. Offers interactive credential setup using the GitHub CLI (`gh`). |
| **Local Code Review** | Multi-axis local code, documentation, and architecture review across any repository (GitHub, Bitbucket, GitLab, or local working tree). Supports both Diff Review Mode and Whole-Codebase Audit Mode. | **Use when** reviewing uncommitted changes, staged diffs, branches, commit ranges, or auditing an entire repository/module locally using Dazbo's Five-Axis rubric and anti-hallucination guardrails. |
| **Organise Agent Skills** | Standardised workflow for auditing, pruning, and organising standalone and plugin-bundled agent skills in Antigravity/Gemini environments. Performs filesystem auto-discovery across standalone skills and plugins, plugin supersession and `skills.all/` parking checks, orphan pruning, and manages `skills.json` as a full inventory control panel for standalone skills to keep context token overhead lean (~30–50 active skills). | **Use when** auditing, cleaning, and de-duplicating installed standalone or plugin skills, managing bulky plugins (`config/config.json` / `skills.all/`), auto-syncing `skills.json` against disk, pruning token bloat, disabling sub-skills managed by meta-skills, or writing on-demand activation rules in `config/rules/on-demand-skills.md`, `GEMINI.md`, or `AGENTS.md`. |
| **Tiered Rubric Loop** | A mechanism to quickly and easily drop a combined deterministic & semantic rubric-based testing & evaluation loop into your project. It provides the loop component of an agentic harness. It will automatically leverage any Spec-Driven Development (SDD) and Test-Driven Development artefacts it finds, or otherwise implement its own. <br><br>It works by first performing deterministic checks (e.g. linting and unit tests, `$0`). Next, it performs fast, low-cost Tier 1.5 calibrated semantic scoring via the Gemini Decisions API (`gemini-decision-1`, ~200 ms, 0 output tokens). Finally, it performs a full Tier 2 stateless semantic critique only for Tier 1.5 escalations, or for rubrics deemed too complex for Tier 1.5. | **Use when** running iterative implementation/refinement loops, gating PRs or complex slices against `B1`–`Bn` assertions (`SPEC.md` / `LOOPS.md`), or scoring diffs and multimodal diagrams. |

### Installation Instructions

You can install these skills using `npx` directly from the repository, or by manually cloning the repository.

#### Using NPX (Recommended)

To install all available skills from this repository, run:

```bash
npx skills add https://github.com/derailed-dash/dazbo-agent-skills
```

To install only selected skills, you can use the `--skill` option:

```bash
npx skills add https://github.com/derailed-dash/dazbo-agent-skills --skill maintaining-core-documentation
npx skills add https://github.com/derailed-dash/dazbo-agent-skills --skill deploy-skills-in-antigravity
npx skills add https://github.com/derailed-dash/dazbo-agent-skills --skill convert-to-devto
npx skills add https://github.com/derailed-dash/dazbo-agent-skills --skill secrets-with-git-crypt
npx skills add https://github.com/derailed-dash/dazbo-agent-skills --skill create-md-from-browsermcp-snapshot
npx skills add https://github.com/derailed-dash/dazbo-agent-skills --skill fix-wsl-browser-agent
npx skills add https://github.com/derailed-dash/dazbo-agent-skills --skill install-gemini-code-review-action
npx skills add https://github.com/derailed-dash/dazbo-agent-skills --skill local-code-review
npx skills add https://github.com/derailed-dash/dazbo-agent-skills --skill organise-agent-skills
npx skills add https://github.com/derailed-dash/dazbo-agent-skills --skill tiered-rubric-loop
```

### Skills Documentation

For specific guidelines on using particular skills, refer to the `SKILL.md` file located within each skill's respective directory.

## Project Structure

This repo is structured to allow for easy discovery and management of skills. Skills are self-contained and can be deployed individually or as a collection.

```text
dazbo-agent-skills/
├── skills/                                # Core agent skills
│   ├── maintaining-core-documentation/    # Documentation specialist
│   │   ├── SKILL.md                       # Main instruction file
│   │   └── references/                    # Templates and samples
│   ├── deploy-skills-in-antigravity/      # Skill installer and relocator
│   │   └── SKILL.md                       # Main instruction file
│   ├── convert-to-devto/                  # Dev.to publisher formatter
│   │   └── SKILL.md                       # Main instruction file
│   ├── secrets-with-git-crypt/            # Secrets management with git-crypt
│   │   ├── SKILL.md                       # Main instruction file
│   │   └── scripts/                       # Automation helper scripts
│   │       └── git-crypt-helper.sh
│   ├── create-md-from-browsermcp-snapshot/# Converts accessibility trees to MD
│   │   ├── SKILL.md                       # Main instruction file
│   │   └── scripts/                       # Reusable Python parsing script
│   │       └── parse_snapshot.py
│   ├── fix-wsl-browser-agent/             # WSL2 Browser Agent & CDP connection fixer
│   │   ├── SKILL.md                       # Main instruction file
│   │   └── scripts/                       # Diagnostic and DevToolsActivePort sync script
│   │       └── sync_devtools_port.sh
│   ├── install-gemini-code-review-action/ # Installs PR code review & issue triage action
│   │   └── SKILL.md                       # Main instruction file
│   ├── local-code-review/                 # Multi-axis local code & architecture review
│   │   └── SKILL.md                       # Main instruction file
│   ├── organise-agent-skills/             # Audits, prunes, and manages skill token overhead
│   │   └── SKILL.md                       # Main instruction file
│   └── tiered-rubric-loop/                # 3-tier SDD + TDD + Decisions API rubric loop
│       ├── SKILL.md                       # Main instruction file
│       └── scripts/                       # Calibrated Tier 1.5 evaluator
│           └── eval_rubric.py
├── tests/                                 # Offline unit tests for skill scripts
├── AGENTS.md                              # Repository & skill authoring guidelines
├── Makefile                               # Static checks and unit test targets (make check)
├── pyproject.toml                         # uv dev environment and linter config
└── README.md                              # This storefront
```

## Blogs

Check out my related articles on agent skills, harnesses, and workflows:

### Agent Skills & Antigravity Setup

- [Skills Sprawl: When Too Much of a Good Thing Confuses Your AI Agent](https://medium.com/google-cloud/skills-sprawl-when-too-much-of-a-good-thing-bloats-your-ai-agent-167f907e9dc2) — Why overloading context degrades reasoning, and how to prune and partition skills *(pairs with `organise-agent-skills`)*.
- [Dialling Our Agents to 11: Agent Skills You Need to Be Using!](https://medium.com/google-cloud/dialling-our-agents-to-11-agent-skills-you-need-to-be-using-ccffa51e91df) — A curated tour of high-leverage skills for TDD, code review, and cloud automation.
- [Configuring MCP Servers and Skills for Antigravity CLI and IDE](https://medium.com/google-cloud/configuring-mcp-servers-and-skills-for-antigravity-cli-and-ide-a938c7eebb78) — Structuring global and workspace configurations cleanly across tools.

### Spec-Driven Development, Harnesses & Verification Loops

- [Documentation as Context: A Skill to Automate Your Blueprints for the Agentic Era](https://medium.com/google-cloud/documentation-as-context-a-skill-to-automate-your-blueprints-for-the-agentic-era-2bec0cf041a3) — Keeping `README`, `DESIGN`, and architecture blueprints synchronised *(pairs with `maintaining-core-documentation`)*.
- [Loop Engineering in the Harness: Autonomous, Self-Correcting Systems](https://medium.com/google-cloud/loop-engineering-in-the-harness-autonomous-self-correcting-systems-95d3ac8f64cf) — Designing `Observe -> Choose -> Act -> Verify` loops with deterministic gates and stateless critics *(pairs with `tiered-rubric-loop`)*.
- [From Vibing Chaos to Reliable Agents: The What, Why, and How of Harness Engineering](https://medium.com/google-cloud/from-vibing-chaos-to-reliable-agents-the-what-why-and-how-of-harness-engineering-6e7e0443a4fc) — Wrapping coding agents in architectural guardrails, linters, and verification harnesses.
- [Spec-Driven Development For-the-Win: Disposable Code, Living Blueprints, and Building Like a Boss](https://medium.com/google-cloud/spec-driven-development-for-the-win-disposable-code-living-blueprints-and-building-like-a-boss-7fe52e7d2d49) — Decomposing requirements into living blueprints (`PRD.md` / `SPEC.md`) before writing code.

### Tool & Workflow Deep Dives

- [Automated GitHub Code Reviews Using Google Gemini Update: Enterprise-Ready, Multimodal, and Smart](https://medium.com/google-cloud/automated-github-code-reviews-using-google-gemini-update-enterprise-ready-multimodal-and-e3459f621aea) — Automated PR reviews and issue triage *(pairs with `install-gemini-code-review-action`)*.
- [Resolving WSL Friction with Google Antigravity: the Agy 2.0 and Agy IDE Edition](https://medium.com/google-cloud/resolving-wsl-friction-with-google-antigravity-the-agy-2-0-and-agy-ide-edition-41cee17773c8) — Fixing WSL2 networking and Chrome `DevToolsActivePort` attachment *(pairs with `fix-wsl-browser-agent`)*.
- [Creating an Automated UI Test of Your Web App in Seconds, with Antigravity and BrowserMCP](https://medium.com/google-cloud/creating-an-automated-ui-test-of-your-web-app-in-seconds-with-gemini-cli-and-browsermcp-09cf4afb8940) — Driving live browser sessions via BrowserMCP *(pairs with `create-md-from-browsermcp-snapshot`)*.

### Full Article Index

- [Dazbo’s Technical Writing & Engineering Catalogue](https://medium.com/@dazbo/dazbos-technical-writing-engineering-catalogue-agentic-ai-google-cloud-architecture-and-cd21558dde32) — Complete directory across Agentic AI, Google ADK, Cloud Architecture, and Python.
