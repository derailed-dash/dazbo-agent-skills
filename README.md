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

| Skill | Purpose & Value | When to Use & Triggers |
| :--- | :--- | :--- |
| **Project Documentation** | End-to-end framework for managing, structuring, and synchronising repository docs. Helps keep documentation in perfect sync with codebase changes to prevent documentation rot. | **Use when** modifying features, system architecture, or tests. Guides the creation and precise synchronisation of core files like `README`, `TODO`, `DESIGN`, `Architecture`, `Testing`, and `Deployment`. |
| **Deploying Skills** | Automated installer, relocator, and manager for Antigravity/Gemini agent skills. Saves time by automatically managing local and global paths. | **Use when** downloading, importing, or updating new agent skills. Automates the installation process via `npx` and safely moves skills to the shared global path (`~/.gemini/skills/`). |
| **Convert to Dev.to** | Formatter that prepares standard Markdown files for publishing on Dev.to. Ensures metadata and syntax compatibility without manual formatting. | **Use when** preparing technical articles for Dev.to. Automates insertion of YAML frontmatter, liquid syntax conversion, variable formatting, and heading structures. |
| **Secrets with Git-Crypt** | Production-grade secrets management workflow. Keeps plaintext files safely gitignored while tracking encrypted versions (`.enc`) in Git. | **Use when** managing `.env`, `*.tfvars`, or sensitive keys. Employs a helper sync script to maintain parallel encrypted copies, avoiding accidental leak of credentials. |
| **Create MD from BrowserMCP Snapshot** | High-fidelity parser to convert raw webpage accessibility trees to structured Markdown. Makes parsed web pages easy for agents to read and search. | **Use when** a webpage has been captured with the BrowserMCP `browser_snapshot` tool. Runs a Python parser to reconstruct structured representations of headings, tables, lists, and links. |
| **Install Gemini Code Review Action** | Automated setup for Dazbo's Gemini-based PR Code Review & Issue Triage action. Streamlines setup and configures secure API credentials. | **Use when** setting up automated Gemini-based pull request code reviews or issue triaging workflows in a GitHub repository. Offers interactive credential setup using the GitHub CLI (`gh`). |

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