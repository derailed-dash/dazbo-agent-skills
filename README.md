# Dazbo's Agentic Skills

This repository serves as a public collection of agentic skills developed for AI agents and assistants. These skills extend the capabilities of AI agents by providing specialised instructions, workflows, and templates for various tasks such as documentation maintenance, content creation, diagrams, and more.

## Repo Metadata

- Author: Dazbo (GitHub: derailed-dash)
- Repository: https://github.com/derailed-dash/dazbo-agent-skills

## Table of Contents

- [Available Skills](#available-skills)
  - [Installation Instructions](#installation-instructions)
  - [Skills Documentation](#skills-documentation)
- [Project Structure](#project-structure)

## Available Skills

| Skill | Purpose | Key Features |
| :--- | :--- | :--- |
| **Project Documentation** | Specialist framework for technical docs. | Creation and management of software project documentation, including: README, TODO, DESIGN, Architecture, Testing, and Deployment. |

### Installation Instructions

You can install these skills using `npx` directly from the repository, or by manually cloning the repository.

#### Using NPX (Recommended)

To install all available skills from this repository, run:

```bash
npx skills add https://github.com/derailed-dash/dazbo-agent-skills
```

To install only selected skills, you can use the `--skill` option:

```bash
npx skills add https://github.com/derailed-dash/dazbo-agent-skills --skill project-documentation
```

Check my blog [Confused About Where to Put Your Agent Skills?](https://medium.com/google-cloud/confused-about-where-to-put-your-agent-skills-ea778f3c64f3) for more information on where you can put these skills.

### Skills Documentation

For specific guidelines on using particular skills, refer to the `SKILL.md` file located within each skill's respective directory.

## Project Structure

This repo is structured to allow for easy discovery and management of skills. Skills are self-contained and can be deployed individually or as a collection.

```text
dazbo-agent-skills/
├── skills/                      # Core agent skills
│   └── project-documentation/   # Documentation specialist
│       ├── SKILL.md             # Main instruction file
│       └── references/          # Templates and samples
└── README.md                    # This storefront
```