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

| Skill | Purpose | Key Features |
| :--- | :--- | :--- |
| **Project Documentation** | Specialist framework for technical docs. | Creation and management of software project documentation, including: README, TODO, DESIGN, Architecture, Testing, and Deployment. |
| **Deploying Skills in Antigravity** | Skill installer and relocator for Antigravity. | Automates installation of new skills via `npx` and moves them to the shared global location (`~/.gemini/skills/`). |
| **Convert to Dev.to** | Standardises Markdown for Dev.to publication. | Automates YAML frontmatter insertion, liquid tags conversion, variable formatting, and heading hierarchy standardisation. |

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
│   └── convert-to-devto/                  # Dev.to publisher formatter
│       └── SKILL.md                       # Main instruction file
└── README.md                              # This storefront
```