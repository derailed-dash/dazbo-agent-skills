---
name: deploy-skills-in-antigravity
description: Downloads, installs, and relocates new agent skills to the global Antigravity shared directory (`~/.gemini/skills/`) to make them available across all tools. Use when the user requests to download, install, import, or update new agent skills.
metadata:
  author: Darren "Dazbo" Lester
---

# Deploying Skills in Antigravity

This skill provides a structured workflow for downloading, installing, and relocating new agent skills. It automates the installation process via `npx` and ensures that all downloaded skills are cleanly migrated to the global/shared location so they are instantly accessible to all Google Antigravity tools.

## Table of Contents

- [Triggers](#triggers)
- [Prerequisites](#prerequisites)
- [Installation and Relocation Workflow](#installation-and-relocation-workflow)
- [OS-Specific Relocation Commands](#os-specific-relocation-commands)
- [Verification Loop](#verification-loop)

## Triggers

This skill MUST trigger whenever:

- The user asks to download, install, import, setup, or update a new agent skill.
- The user mentions adding a skill from a repository or a specific branch/commit.
- The user or agent refers to CLI commands such as `npx skills add`, `skills add`, `skills install`, or `npx skills`.
- The user provides a repository URL (e.g. `https://github.com/...`) and asks to "add" or "integrate" its skills.

## Prerequisites

- **Node.js**: The system must have `npx` available to run the `skills` tool.
- **Access Permissions**: Ensure you have directory write permissions for `~/.agents/skills/` and the global (Agy) shared directory `~/.gemini/skills/`.

## Installation and Relocation Workflow

Copy this checklist and track your progress:

```
Skill Deployment Progress:
- [ ] Step 1: Parse the user's installation request
- [ ] Step 2: Run the installation command
- [ ] Step 3: Relocate the skills to the shared global directory
- [ ] Step 4: Verify that files are correctly positioned
```

**Step 1: Parse the user's installation request**

Identify the target repository URL and optional flags such as `--skill` or specific branch/commit references.
Common patterns:
- Repository installation: `npx skills add https://github.com/username/repo-name -y -g`
- Specific skill installation: `npx skills add https://github.com/username/repo-name -y -g --skill skill-name`

**Step 2: Run the installation command**

Propose and execute the installation command using the `run_command` tool.
If the command fails due to permission errors, request appropriate permissions before retrying.

**Step 3: Relocate the skills to the shared global directory**

Once installed, the skills reside in `~/.agents/skills/`. To make them available to all Google Antigravity tools, relocate them to `~/.gemini/skills/`.
Use the appropriate OS-specific relocation command based on the host operating system.

**Step 4: Verify that files are correctly positioned**

Perform the comprehensive checks outlined in the [Verification Loop](#verification-loop) to ensure the skill is fully functional and registered.

## OS-Specific Relocation Commands

Depending on the operating system, execute the appropriate shell command or script:

### Linux & macOS (Bash/Zsh)

Run this clean replacement script. It removes any existing versions in `~/.gemini/skills/` before moving the newly installed versions:

```bash
mkdir -p "$HOME/.gemini/skills/" && [ -d "$HOME/.agents/skills" ] && for d in "$HOME/.agents/skills"/*/; do [ -d "$d" ] && rm -rf "$HOME/.gemini/skills/$(basename "$d")" && mv "$d" "$HOME/.gemini/skills/"; done
```

### Windows (PowerShell)

If operating on a Windows host environment, run the following PowerShell command:

```powershell
$sourceDir = "$HOME\.agents\skills"
$destDir = "$HOME\.gemini\skills"
if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force }
Get-ChildItem -Path $sourceDir -Directory | ForEach-Object {
    $target = Join-Path $destDir $_.Name
    if (Test-Path $target) { Remove-Item -Path $target -Recurse -Force -ErrorAction SilentlyContinue }
    Move-Item -Path $_.FullName -Destination $destDir -Force
}
```

## Verification Loop

Before completing the task, the agent MUST run the following verification sequence:

### 1. Folder Existence and Relocation Verification
Confirm the skill directory has been successfully moved to the global shared path:
- **Linux/macOS:** `ls -la ~/.gemini/skills/`
- **Windows:** `Get-ChildItem "$HOME\.gemini\skills"`

### 2. Frontmatter & Integrity Check
Verify that the `SKILL.md` file exists in the target directory and has a valid YAML frontmatter block:
- **Command:** Read the first 10 lines of the relocated `SKILL.md` and confirm it starts with `---` and contains valid `name` and `description` keys.

### 3. Subdirectory Validation
For complex skills, ensure that nested folders (such as `references/`, `evals/`, or `scripts/`) are present and populated:
- **Command:** Verify that critical folders are present and not empty.

### 4. Global Registry Check
Confirm the Skills CLI successfully registers and lists the newly relocated skill:
- **Command:** `npx skills ls -g` (or `npx skills ls -g --json`)
- **Success Criteria:** The output must list the relocated skill name alongside its absolute global path.

### 5. Permission & Readability Check
Ensure that the relocated skill files are readable by the active shell process to prevent loader failures during execution.
