# Dazbo's Agentic Skills

This repository serves as a public collection of agentic skills developed for AI agents and assistants. These skills extend the capabilities of AI agents by providing specialised instructions, workflows, and templates for various tasks such as documentation maintenance, content creation, diagrams, and more.

## Repo Metadata

- Author: Dazbo (GitHub: derailed-dash)
- Repository: https://github.com/derailed-dash/dazbo-agent-skills

## Install Count

According to [Skills.sh](https://skills.sh/), these skills have been installed:

[![skills.sh](https://skills.sh/b/derailed-dash/dazbo-agent-skills)](https://skills.sh/derailed-dash/dazbo-agent-skills)

## Table of Contents

- [Available Skills](#available-skills)
  - [Installation Instructions](#installation-instructions)
  - [Skills Documentation](#skills-documentation)
- [Project Structure](#project-structure)

## Available Skills

| Skill | Purpose | About & Triggers |
| :--- | :--- | :--- |
| **Project Documentation** | Specialist framework for repository docs. | **Use when** modifying features, system architecture, or tests. Guides the creation and precise synchronisation of `README`, `TODO`, `DESIGN`, `Architecture`, `Testing`, and `Deployment` files. |
| **Deploying Skills** | Global skill installer and relocator. | **Use when** downloading, importing, or updating new agent skills. Automates the installation process via `npx` and safely moves skills to the shared global path (`~/.gemini/skills/`). |
| **Convert to Dev.to** | Standardises Markdown for publication. | **Use when** preparing technical articles for Dev.to. Automates insertion of YAML frontmatter, liquid syntax conversion, variable formatting, and heading structures. |
| **Secrets with Git-Crypt** | Git-Crypt secrets protection workflow. | **Use when** managing `.env`, `*.tfvars`, or sensitive keys. Employs a helper sync script to maintain parallel encrypted copies (`.enc`) while keeping unencrypted versions safely gitignored. |
| **Create MD from BrowserMCP Snapshot** | Converts BrowserMCP accessibility tree snapshots to Markdown. | **Use when** a webpage's has been captured with the BrowserMCP `browser_snapshot` tool. Runs a Python parser to reconstruct structured, high-fidelity Markdown representations of the page content (headings, tables, lists, blockquotes). |
| **Install Gemini Code Review Action** | Installs Dazbo's PR code review & issue triage action. | **Use when** setting up automated Gemini-based pull request code reviews or issue triaging workflows in a GitHub repository. |

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
npx skills add https://github.com/derailed-dash/dazbo-agent-skills --skill install-gemini-code-review-action
```

Check my blog [Confused About Where to Put Your Agent Skills?](https://medium.com/google-cloud/confused-about-where-to-put-your-agent-skills-ea778f3c64f3) for more information on where you can put these skills.

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
│   └── install-gemini-code-review-action/ # Installs PR code review & issue triage action
│       └── SKILL.md                       # Main instruction file
└── README.md                              # This storefront
```