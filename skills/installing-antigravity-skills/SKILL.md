---
name: installing-antigravity-skills
description: Downloads, installs, and relocates new agent skills to the global Antigravity shared directory (`~/.gemini/skills/`) to make them available across all tools. Use when the user requests to download, install, import, or update new agent skills.
---

# Installing Antigravity Skills

This skill provides a structured workflow for downloading, installing, and relocating new agent skills. It automates the installation process via `npx` and ensures that all downloaded skills are cleanly migrated to the global/shared location so they are instantly accessible to all Google Antigravity tools.

## Table of Contents

- [Triggers](#triggers)
- [Prerequisites](#prerequisites)
- [Installation and Relocation Workflow](#installation-and-relocation-workflow)
- [OS-Specific Relocation Commands](#os-specific-relocation-commands)
- [Verification Loop](#verification-loop)

## Triggers

This skill MUST trigger whenever:

- The user asks to download, install, import, or update a new agent skill.
- The user mentions adding a skill from a repository or a specific branch.

## Prerequisites

- **Node.js**: The system must have `npx` available to run the `skills` tool.
- **Access Permissions**: Ensure you have directory write permissions for `~/.agents/skills/` and `~/.gemini/skills/`.

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

Check the contents of `~/.gemini/skills/` to ensure the new skill directory has been relocated successfully and is not empty.

## OS-Specific Relocation Commands

Depending on the operating system, execute the appropriate shell command or script:

### Linux & macOS (Bash/Zsh)

Run this clean replacement script. It removes any existing versions in `~/.gemini/skills/` before moving the newly installed versions:

```bash
mkdir -p "$HOME/.gemini/skills/" && for d in "$HOME"/.agents/skills/*/; do [ -d "$d" ] && rm -rf "$HOME/.gemini/skills/$(basename "$d")"; done && mv "$HOME"/.agents/skills/* "$HOME/.gemini/skills/"
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

1. Run a check to verify that the skills have been successfully moved:
   - On Linux/macOS: `ls -la ~/.gemini/skills/`
   - On Windows: `Get-ChildItem "$HOME\.gemini\skills"`
2. If the files are not present in the target directory, trace back through the migration logs to find permission or pathway errors. Do not complete the task until the skill is verified to exist in `~/.gemini/skills/`.
