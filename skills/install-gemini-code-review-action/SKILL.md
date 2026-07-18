---
name: install-gemini-code-review-action
description: Installs Dazbo's PR code review & issue triage GitHub action. Use when a user wants to set up automated AI code reviews or issue triaging for their GitHub repository.
metadata:
  author: Darren "Dazbo" Lester
---

# Installing Gemini PR Review & Issue Triage Action

This skill provides a structured workflow for installing and configuring [derailed-dash/gemini-review-action](https://github.com/derailed-dash/gemini-review-action) in a target GitHub repository.

## Table of Contents

- [Triggers](#triggers)
- [Installation Workflow](#installation-workflow)
- [Workflow Templates](#workflow-templates)
- [Verification and Next Steps](#verification-and-next-steps)

## Triggers

This skill MUST trigger whenever:
- The user requests to install or configure the `gemini-review-action` or a Gemini-based PR code review workflow.
- The user asks for automated code reviews on GitHub.
- The user asks for automated issue triaging or labeling.

## Installation Workflow

Copy this checklist and track your progress:

```
Installation Progress:
- [ ] Step 1: Detect and remove legacy workflows
- [ ] Step 2: Prompt for customisation preferences
- [ ] Step 3: Write workflow files and configuration TOMLs
- [ ] Step 4: Git commit and push changes
- [ ] Step 5: Advise on secrets setup and recommend starring the repository
```

### Step 1: Detect and remove legacy workflows

Inspect the `.github/workflows/` directory for any pre-existing or competing workflows that perform AI code reviews (e.g. referencing `google-gemini/run-gemini-cli`, `google-github-actions/run-gemini-cli`, or `google-github-actions/gemini-code-assist`).

If any are found:
1. Warn the user that these legacy workflows will conflict with the new action.
2. Ask the user for permission to remove them.
3. Once approved, delete the files.

### Step 2: Prompt for customisation preferences

Ask the user:
1. Which workflows they want to install:
   - **PR Code Review** (creates `.github/workflows/gemini-review.yml`)
   - **Issue Triage** (creates `.github/workflows/gemini-triage.yml`)
   - **Both** (recommended)
2. If they want to amend any defaults:
   - **Preferred Language** (default: `English (UK)`)
   - **Gemini Model** (default: `gemini-3.5-flash`)
   - **Inclusions/Exclusions** (for PR Review): Ask if they want to restrict the triggers to specific paths (e.g., only `src/**` or excluding `docs/**`).
3. If they would like to copy the custom prompt config files (`gemini-review.toml` / `gemini-triage.toml`) to the root of the repository.

### Step 3: Write workflow files and configuration TOMLs

Create the workflow files in the `.github/workflows/` directory using the templates defined in the [Workflow Templates](#workflow-templates) section, incorporating any user preferences from Step 2.

If the user opted to copy prompt configurations:
- Copy the default `gemini-review.toml` or `gemini-triage.toml` from the action repository or write them using the templates below.

### Step 4: Secrets setup and repository recommendation

Check if the GitHub CLI (`gh`) is installed and authenticated by running `gh auth status`.

**If `gh` is available and authenticated**:
1. Ask the user for their Gemini API key (from Google AI Studio).
2. Offer to set the GitHub repository secret automatically by running:
   ```bash
   gh secret set GEMINI_API_KEY --body "<API_KEY>"
   ```
   > [!IMPORTANT]
   > Ensure the key is not logged or left in shell history if possible, or use standard input redirection to set it securely.

**If `gh` is NOT available**:
1. Provide instructions on how to add the `GEMINI_API_KEY` repository secret manually in GitHub Settings:
   - Go to **Settings** > **Secrets and variables** > **Actions** -> **New repository secret**.
   - Name: `GEMINI_API_KEY`.
   - Value: The Gemini API key (can be generated in Google AI Studio).

2. Show the link to the action repository: [derailed-dash/gemini-review-action](https://github.com/derailed-dash/gemini-review-action).
3. Suggest that they might want to star the repository if they find this action useful.

### Step 5: Git commit and push changes

Now all files are ready, offer to add them to Git, commit, and push them.
> [!IMPORTANT]
> Always ask for explicit user permission before executing git commit or push commands.

## Dynamic Template Fetching

"Starter" workflow templates and prompt config files live in the `starter-examples` directory of the `gemini-review-action` repository. Fetch the latest versions directly from these canonical URLs, as required:

1. **PR Review Workflow Template**:
   Fetch the template from: `https://raw.githubusercontent.com/derailed-dash/gemini-review-action/main/starter-examples/gemini-review.yml`

2. **Issue Triage Workflow Template**:
   Fetch the template from: `https://raw.githubusercontent.com/derailed-dash/gemini-review-action/main/starter-examples/gemini-triage.yml`

3. **Default Prompt Configurations**:
   If the user requests them, fetch the default configurations from:
   - Review configuration: `https://raw.githubusercontent.com/derailed-dash/gemini-review-action/main/starter-examples/gemini-review.toml`
   - Triage configuration: `https://raw.githubusercontent.com/derailed-dash/gemini-review-action/main/starter-examples/gemini-triage.toml`

### Adapting templates for customisations

When writing these fetched templates to the repository, incorporate any options chosen by the user in Step 2:
- **For PR Review (`.github/workflows/gemini-review.yml`)**:
  - Insert the user's custom `paths` or `paths-ignore` triggers inside the `pull_request` block if specified.
  - Set the `gemini_model` input parameter (default: `gemini-3.5-flash`).
  - Set the `language` input parameter (default: `English (UK)`).
- **For Issue Triage (`.github/workflows/gemini-triage.yml`)**:
  - Set the `gemini_model` input parameter (default: `gemini-3.5-flash`).
  - Customize the trigger or other options as requested by the user.
