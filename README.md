# Dazbo's Agentic Skills

This repository serves as a public collection of agentic skills developed for AI agents and assistants. These skills extend the capabilities of AI agents by providing specialised instructions, workflows, and templates for various tasks such as documentation maintenance, content creation, diagrams, and more.

## Repo Metadata

- Author: Dazbo (GitHub: derailed-dash)
- Repository: https://github.com/derailed-dash/dazbo-agent-skills

## Table of Contents

- [Repo Metadata](#repo-metadata)
- [Project Structure](#project-structure)
- [Available Skills](#available-skills)
  - [Project Documentation](#project-documentation)
- [Installation Instructions](#installation-instructions)
- [Documentation](#documentation)

## Project Structure

```text
dazbo-agent-skills/
├── skills/                      # Directory containing all agent skills
│   └── project-documentation/   # The project documentation skill
│       ├── SKILL.md             # The main skill instruction file
│       └── references/          # Templates and reference materials
└── README.md                    # This file
```

## Available Skills

### Project Documentation

**Directory:** `skills/project-documentation`

This skill provides a comprehensive framework for the maintenance of high-quality, professional technical documentation for projects. It helps agents create, maintain, and synchronise core project documentation (README, TODO, DESIGN, architecture-and-walkthrough.md, testing, and deployment). 

**Features:**
- Ensures updates cross-synchronise across all relevant Markdown files.
- Adheres to British English ("UK spelling").
- Automates the formatting of design decisions (ADRs) and architectural blueprints.

## Installation Instructions

You can install these skills using `npx` directly from the repository, or by manually cloning the repository.

### Using NPX (Recommended)

To install all available skills from this repository, run:

```bash
npx skills add https://github.com/derailed-dash/dazbo-agent-skills
```

To install only selected skills, you can use the `--skill` option:

```bash
npx skills add https://github.com/derailed-dash/dazbo-agent-skills --skill project-documentation
```

Check my blog [Confused About Where to Put Your Agent Skills?](https://medium.com/google-cloud/confused-about-where-to-put-your-agent-skills-ea778f3c64f3) for more information on where you can put these skills.

## Documentation

For specific guidelines on using particular skills, refer to the `SKILL.md` file located within each skill's respective directory.
