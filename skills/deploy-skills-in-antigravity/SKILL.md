---
name: deploy-skills-in-antigravity
description: |
  Downloads, installs, and relocates new agent skills to the global Antigravity shared directory (`~/.gemini/config/skills/`) to make them available across all tools. Use when the user requests to download, install, import, setup, or update new agent skills, or asks to relocate installed skills.
metadata:
  author: Darren "Dazbo" Lester
  repository: https://github.com/derailed-dash/dazbo-agent-skills
  skills:
    - find-skills
  cli:
    - npx
---

# Deploying Skills in Antigravity

This skill provides a structured workflow for downloading, installing, and relocating new agent skills. It first checks for the availability of the `find-skills` skill to handle skill discovery, installation, or upgrades. If `find-skills` is unavailable, it falls back to direct CLI installation commands.

After installation or upgrade, if operating within an Antigravity environment (where `~/.gemini` exists), it prompts the user to confirm whether they want the skills relocated to `~/.gemini/config/skills/` so they become available across all Antigravity tools.

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
- **Access Permissions**: Ensure you have directory write permissions for `~/.agents/skills/` and, if relocating, `~/.gemini/config/skills/`.

## Installation and Relocation Workflow

Copy this checklist and track your progress:

```
Skill Deployment Progress:
- [ ] Step 1: Check for `find-skills` availability
- [ ] Step 2: Install or upgrade skills
- [ ] Step 3: Check for Antigravity environment and prompt user for relocation
- [ ] Step 4: Relocate skills (if confirmed)
- [ ] Step 5: Verify that files are correctly positioned
- [ ] Step 6: Sync & Register with `skills.json`
```

**Step 1: Check for `find-skills` availability**

Before initiating an installation or upgrade:
- Check if the `find-skills` skill is available in your active agent skills context.
- If `find-skills` is present, use it for discovering, installing, or upgrading skills in Step 2.
- If `find-skills` is NOT present, proceed to Step 2 using the direct CLI fallback commands detailed in this skill.

**Step 2: Install or upgrade skills**

Depending on `find-skills` availability:

- **When `find-skills` IS available:**
  - Delegate skill search, selection, installation, or updates to `find-skills`.
  - For new skill installation: execute `npx skills add <package> -g -y` (or specific repository URL/branch flags).
  - For skill upgrades: execute `npx skills update -g -y` (or `npx skills check`).
- **When `find-skills` is NOT available:**
  - Parse the user's request to identify the target repository URL, skill name, or branch.
  - Execute direct CLI commands using `run_command`:
    - Repository installation: `npx skills add https://github.com/username/repo-name -y -g`
    - Specific skill installation: `npx skills add https://github.com/username/repo-name -y -g --skill skill-name`
    - Skill upgrade: `npx skills update -g -y`

**Step 3: Check for Antigravity environment and prompt user for relocation**

> [!IMPORTANT] MANDATORY USER CONFIRMATION GATE
> You MUST STOP and ask the user using `ask_question` or a direct prompt before running any relocation script. Do NOT execute the relocation command until the user explicitly confirms.

Default skill installation via `npx skills` places files into `~/.agents/skills/`.
Before relocating files:
1. **Check if `~/.gemini` exists**: Verify if the target environment is Antigravity by checking for the existence of `~/.gemini` (e.g. `[ -d "$HOME/.gemini" ]` on Linux/macOS or `Test-Path "$HOME\.gemini"` on Windows).
   - If `~/.gemini` does **not** exist, skip relocation. Installed skills will remain in `~/.agents/skills/`.
2. **Prompt the User**: If `~/.gemini` **does** exist, explicitly ask the user whether they want the newly installed/updated skills relocated to `~/.gemini/config/skills/` to make them available across all Antigravity tools.
   - If the user confirms: proceed to Step 4 to perform the relocation.
   - If the user declines: leave the skills in `~/.agents/skills/`.

**Step 4: Relocate skills (if confirmed)**

If the user confirmed relocation and `~/.gemini` exists:
- Use the OS-specific relocation command detailed in the [OS-Specific Relocation Commands](#os-specific-relocation-commands) section to move skills from `~/.agents/skills/` to `~/.gemini/config/skills/`.

**Step 5: Verify that files are correctly positioned**

Perform the checks outlined in the [Verification Loop](#verification-loop) to ensure the skill is functional and correctly placed.

**Step 6: Sync & Register with `skills.json`**

If operating in an Antigravity environment (`~/.gemini` exists) and skills were relocated to `~/.gemini/config/skills/`:
1. Check if `~/.gemini/config/skills.json` exists.
2. Read `skills.json` and check if the newly installed/updated skills are listed in the `exclude` array.
105 | 3. For any newly relocated skill missing from `skills.json`:
106 |     - Prompt the user or evaluate context to decide whether the skill should be enabled by default (`"//skill-name"`) or disabled (`"skill-name"`).
107 |     - Insert the skill into the `exclude` array.
   - Sort the `exclude` array alphabetically and write the updated `skills.json` back to disk.

## OS-Specific Relocation Commands

Depending on the operating system, execute the appropriate shell command or script:

### Linux & macOS (Bash/Zsh)

Run this clean replacement script. It removes any existing versions in `~/.gemini/config/skills/` before moving the newly installed versions:

```bash
mkdir -p "$HOME/.gemini/config/skills/" && [ -d "$HOME/.agents/skills" ] && for d in "$HOME/.agents/skills"/*/; do [ -d "$d" ] && rm -rf "$HOME/.gemini/config/skills/$(basename "$d")" && mv "$d" "$HOME/.gemini/config/skills/"; done
```

### Windows (PowerShell)

If operating on a Windows host environment, run the following PowerShell command:

```powershell
$sourceDir = "$HOME\.agents\skills"
$destDir = "$HOME\.gemini\config\skills"
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
Confirm the skill directory path (either `~/.gemini/config/skills/` if relocated, or `~/.agents/skills/` if not):
- **Linux/macOS:** `ls -la ~/.gemini/config/skills/` (or `ls -la ~/.agents/skills/`)
- **Windows:** `Get-ChildItem "$HOME\.gemini\config\skills"` (or `Get-ChildItem "$HOME\.agents\skills"`)

### 2. Frontmatter & Integrity Check
Verify that the `SKILL.md` file exists in the target directory and has a valid YAML frontmatter block:
- **Command:** Read the first 10 lines of `SKILL.md` and confirm it starts with `---` and contains valid `name` and `description` keys.

### 3. Subdirectory Validation
For complex skills, ensure that nested folders (such as `references/`, `evals/`, or `scripts/`) are present and populated:
- **Command:** Verify that critical folders are present and not empty.

### 4. Global Registry Check
Confirm the Skills CLI successfully registers and lists the skill:
- **Command:** `npx skills ls -g` (or `npx skills ls -g --json`)
- **Success Criteria:** The output must list the skill name alongside its absolute path.

### 5. Permission & Readability Check
Ensure that the skill files are readable by the active shell process to prevent loader failures during execution.
