---
name: secrets-with-git-crypt
description: Use when managing encryption and decryption of secrets (like .env or *.tfvars) using git-crypt. Helps install git-crypt, initialize/unlock repositories, and maintain parallel unencrypted/encrypted file copies securely.
---

# Secrets Management with Git-Crypt

This skill provides a secure, structured workflow for managing repository secrets (e.g. `.env`, `*.tfvars`, `sec.json`) using `git-crypt`. It guides the agent to ensure sensitive credentials are never checked in as plaintext, instead maintaining parallel encrypted `.enc` versions checked into Git.

## Table of Contents

- [Triggers](#triggers)
- [Prerequisites](#prerequisites)
- [Secrets Setup and Sync Workflow](#secrets-setup-and-sync-workflow)
- [Command Reference](#command-reference)
- [Verification Loop](#verification-loop)

## Triggers

This skill MUST trigger whenever:

- The user mentions `git-crypt`, `encryption`, `decryption`, or `secrets management`.
- The user requests to store sensitive files (like `.env`, `.tfvars`, keyfiles) in the repository.
- The user attempts to commit or push files that should be encrypted (e.g. `.env`, `*.tfvars`, `sec.json`) to the repository.
- Cloning an existing repository that contains `.enc` files (e.g. `.env.enc`, `terraform.tfvars.enc`), indicating it was previously protected by git-crypt.
- Initializing a new repository and setting up local/remote secret configurations.
- Changing or adding secrets credentials that need to be committed securely.

## Prerequisites

- **Host Environment**: Unix-like operating system (e.g., Linux, WSL, macOS).
- **Git**: A git repository must be initialized in the current project.
- **git-crypt**: The `git-crypt` command-line utility must be installed.
  - If missing, the helper script can attempt installation via `sudo apt-get install git-crypt` on Debian/Ubuntu systems.
- **Helper Script**: Make sure the helper script at `skills/secrets-with-git-crypt/scripts/git-crypt-helper.sh` is executable (`chmod +x`).

## Secrets Setup and Sync Workflow

Copy this checklist and track your progress:

```
Secrets Management Progress:
- [ ] Step 1: Verify git-crypt installation
- [ ] Step 2: Initialize or unlock the repository
- [ ] Step 3: Configure tracking and gitignore rules
- [ ] Step 4: Perform file synchronization
- [ ] Step 5: Verify environment security
```

**Step 1: Verify git-crypt installation**

Run the status command of the helper script to check if git-crypt is available on the system:
```bash
./skills/secrets-with-git-crypt/scripts/git-crypt-helper.sh status
```
If it is not installed, run the installation helper command:
```bash
./skills/secrets-with-git-crypt/scripts/git-crypt-helper.sh install
```

**Step 2: Initialize or unlock the repository**

- **If this is a new repository (or you are setting up git-crypt for the first time)**:
  Decide where the secure key will be stored *outside* of the repository (e.g., `~/secure-keys/my-project.key`). Proactively run:
  ```bash
  ./skills/secrets-with-git-crypt/scripts/git-crypt-helper.sh init ~/secure-keys/my-project.key
  ```
  *Ensure the key is NEVER committed to git.*

- **If this is a cloned repository containing `.enc` files**:
  Ask the user for the local path to the existing key file, and run:
  ```bash
  ./skills/secrets-with-git-crypt/scripts/git-crypt-helper.sh unlock /path/to/existing.key
  ```

**Step 3: Configure tracking and gitignore rules**

Verify that `.gitattributes` in the root of the project contains the filter declaration:
```text
*.enc filter=git-crypt diff=git-crypt
```
All unencrypted files (e.g., `.env`, `variables.tfvars`) MUST be explicitly added to `.gitignore`. Running the helper script sync commands automatically appends them, but you must double-check that they are not tracked as plaintext in Git.

**Step 4: Perform file synchronization**

- **Sync to encrypted versions (before committing changes)**:
  Copy unencrypted local files to their parallel `.enc` versions:
  - For a specific file:
    ```bash
    ./skills/secrets-with-git-crypt/scripts/git-crypt-helper.sh sync-to-enc .env
    ```
  - For all known `.enc` files in the repository:
    ```bash
    ./skills/secrets-with-git-crypt/scripts/git-crypt-helper.sh sync-to-enc
    ```

- **Sync from encrypted versions (after unlocking a cloned repository)**:
  Restore all unencrypted plaintext files from the unlocked `.enc` versions:
  ```bash
  ./skills/secrets-with-git-crypt/scripts/git-crypt-helper.sh sync-from-enc
  ```

**Step 5: Verify environment security**

Perform the steps in the [Verification Loop](#verification-loop) before concluding your turn to make sure no plaintext secrets have been staged or committed.

---

## Command Reference

The helper script supports the following commands:

| Command | Arguments | Description |
| :--- | :--- | :--- |
| `install` | None | Installs git-crypt on Debian/Ubuntu/WSL platforms. |
| `init` | `<key_path>` | Runs `git-crypt init`, sets up `.gitattributes`, and exports key. |
| `unlock` | `<key_path>` | Unlocks the repository using the specified key file. |
| `sync-to-enc` | `[file]` | Syncs unencrypted file(s) to their `.enc` copies; ensures `.gitignore` inclusion. |
| `sync-from-enc`| `[file]` | Syncs/restores `.enc` copies back to unencrypted files. |
| `status` | None | Evaluates installation, git-crypt initialization, and file sync states. |

---

## Verification Loop

Before concluding the secrets setup or modifications, the agent MUST execute the following verification steps:

### 1. Execute Status Check
Run the helper status command:
```bash
./skills/secrets-with-git-crypt/scripts/git-crypt-helper.sh status
```
Ensure all parallel secret files report `[OK]`. If any say `DO NOT MATCH`, run the appropriate `sync-to-enc` or `sync-from-enc` command.

### 2. Verify gitignore Integrity
Confirm the unencrypted plain files are NOT tracked by Git. Run:
```bash
git ls-files --error-unmatch .env 2>/dev/null
```
- **If the command returns output (file is tracked)**: IMMEDIATELY run `git rm --cached <file>` to remove it from staging while keeping it locally on disk.

### 3. Verify .gitattributes Structure
Verify that `.gitattributes` has:
```text
*.enc filter=git-crypt diff=git-crypt
```
This ensures git-crypt transparently manages all `.enc` files under Git.

### 4. Git Crypt Status Check
Verify that git-crypt matches the filter correctly on staged/committed `.enc` files:
```bash
git-crypt status
```
The output must show that the `.enc` files are `encrypted`.
