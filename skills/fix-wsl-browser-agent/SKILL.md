---
name: fix-wsl-browser-agent
description: |
  Diagnoses and resolves Antigravity browser subagent and Chrome DevTools MCP
  connection failures in WSL2 environments (such as `Could not find DevToolsActivePort`,
  `ELOOP` symlink errors, or unreachable port 9222). Use whenever the native
  browser agent or chrome-devtools MCP fails to connect to Chrome on WSL.
metadata:
  author: Darren "Dazbo" Lester
  repository: https://github.com/derailed-dash/dazbo-agent-skills
---

# Fix WSL Browser Agent & Chrome DevTools Connection

This skill diagnoses and resolves connection failures between Antigravity's Linux-based `browser` subagent (or `chrome-devtools` MCP server) running inside **Windows Subsystem for Linux (WSL2)** and **Google Chrome** running on the Windows host.

## When to Use

Activate this skill whenever:
- The `browser` subagent or `chrome-devtools` MCP fails with:
  `Could not connect to Chrome (Could not find DevToolsActivePort for chrome at /home/<user>/.config/google-chrome/DevToolsActivePort)`
- A symlink at `~/.config/google-chrome/DevToolsActivePort` fails with:
  `Cause: ELOOP: too many symbolic links encountered`
- Port `9222` is unreachable from inside WSL2 even though Chrome is running on Windows.

---

## 1. Check If Fixed Upstream First (Future-Proofing)

Google may update Antigravity or `chrome-devtools-mcp` in a future release to natively detect and bridge to Windows Chrome from WSL2 (for example, by automatically scanning `/mnt/c/Users/*/AppData/Local/Google/Chrome/User Data/DevToolsActivePort` or establishing a built-in host channel).

Before applying any workarounds:
1. **Verify Environment**: Confirm the session is actually running inside WSL2 (`grep -qi microsoft /proc/version`). If not on WSL2, follow standard Linux/macOS Chrome DevTools troubleshooting instead.
2. **Check Upstream Behaviour**:
   - If the `browser` subagent or `chrome-devtools` MCP (`list_pages`) succeeds **without** `~/.config/google-chrome/DevToolsActivePort` being manually synced, **stop immediately** — Google has resolved the WSL discovery gap upstream.
   - If the user previously added a custom `DevToolsActivePort` sync snippet to their shell configuration and upstream now handles discovery natively, inform the user and offer to remove the obsolete workaround.

---

## 2. Root Cause Architecture: The Three WSL2 Boundaries

When the problem is present, it is caused by three distinct boundaries between WSL2 and Windows Chrome:

### Boundary 1: Network Isolation (`NAT` vs `mirrored`)
By default, WSL2 uses NAT networking on a separate virtual subnet, preventing Linux processes inside WSL2 from reaching Windows `127.0.0.1:9222`. Enabling `networkingMode=mirrored` in `%USERPROFILE%\.wslconfig` shares `localhost` directly between Windows and WSL2.

### Boundary 2: Chrome 144+ `--autoConnect` & `DevToolsActivePort` Path Mismatch
Modern Chrome (144+) and `chrome-devtools-mcp --autoConnect` do not blindly probe `http://127.0.0.1:9222/json/version`. Instead, when remote debugging is enabled (`chrome://inspect/#remote-debugging`), Chrome writes a two-line file named `DevToolsActivePort` containing the active port and a session-specific WebSocket UUID path:
```text
9222
/devtools/browser/d7936b9a-4469-4faf-97ae-f700b05e5b77
```
- **Windows Chrome writes to**: `/mnt/c/Users/<win-user>/AppData/Local/Google/Chrome/User Data/DevToolsActivePort`
- **WSL2 `browser` agent reads from**: `~/.config/google-chrome/DevToolsActivePort`

### Boundary 3: The Sandbox Symlink Trap (`ELOOP`)
Do **NOT** create a symbolic link (`ln -s`) from `~/.config/google-chrome/DevToolsActivePort` to `/mnt/c/...`. Because the Antigravity `browser` subagent runs inside a sandboxed Linux container where `/mnt/c` (`drvfs`) is not mounted or cannot be traversed, symlinks fail with `ELOOP: too many symbolic links encountered`. The file **must** be copied as a regular file (`cp -f`).

---

## 3. Diagnostic & Remediation Procedure

### Step 1: Run the Diagnostic & Sync Script

Execute the bundled `sync_devtools_port.sh` helper script **unsandboxed** (`BypassSandbox: true`, as it accesses `/mnt/c/` and `~/.config/google-chrome/`):

```bash
bash ~/.gemini/config/skills/fix-wsl-browser-agent/scripts/sync_devtools_port.sh
```

The script automatically:
1. Verifies WSL2 is active.
2. Locates the active Windows Chrome `DevToolsActivePort` file under `/mnt/c/Users/*/AppData/Local/Google/Chrome/User Data/DevToolsActivePort`.
3. Removes any broken symlink at `~/.config/google-chrome/DevToolsActivePort` and copies the file as a regular file.
4. Verifies that `127.0.0.1:<port>` is reachable from WSL2.

### Step 2: Handle Any Reported Layer Failures

Depending on the script output:

- **If the Windows `DevToolsActivePort` file is missing**:
  Instruct the user to open Google Chrome on Windows, navigate to `chrome://inspect/#remote-debugging`, and tick the checkbox to enable remote debugging. Once enabled, re-run `sync_devtools_port.sh`.
- **If `127.0.0.1:<port>` is unreachable from WSL2**:
  1. First check if Chrome on Windows was recently closed or restarted (if so, ask the user to ensure Chrome is open with `chrome://inspect/#remote-debugging` enabled).
  2. If Chrome is open and listening on Windows but unreachable on `127.0.0.1` in WSL2, guide the user to enable **WSL Mirrored Networking** in `%USERPROFILE%\.wslconfig`:
     ```ini
     [wsl2]
     networkingMode=mirrored
     ```
     Then run `wsl --shutdown` from Windows PowerShell/Command Prompt and restart WSL.

### Step 3: Retry the Browser Subagent

Once `~/.config/google-chrome/DevToolsActivePort` is synced and the port is reachable:
1. Message the existing `browser` subagent (or invoke a new one / call `list_pages`) to retry the operation.
2. Remind the user that Chrome on Windows may display a one-time **"Allow remote debugging?"** confirmation dialog in the browser window — they should click **Allow**.

---

## 4. Optional Shell Startup Persistence (Zero Assumptions About `~/.bashrc`)

Because Windows Chrome generates a new WebSocket UUID in `DevToolsActivePort` every time the browser is restarted, the copied file in `~/.config/google-chrome/DevToolsActivePort` will become stale after a Chrome restart.

If the user wants this synced automatically on shell startup:

> [!IMPORTANT]
> **Make Zero Assumptions About `~/.bashrc`**:
> Never assume the user's `~/.bashrc` follows a specific template, uses `oh-my-bash`, or contains an Antigravity fast-exit guard. `~/.bashrc` configurations vary across machines and change over time.

1. **Always Read `~/.bashrc` First**: Inspect the user's actual `~/.bashrc` before proposing or making any edits.
2. **Determine Placement Dynamically**:
   - Check whether `~/.bashrc` contains any early `return` statements (such as non-interactive guards like `case $- in *i*) ;; *) return;; esac`, `[ -z "$PS1" ] && return`, or agent fast-exit guards).
   - If any early `return` guards exist, place the sync block **above the earliest `return`** so it executes for both interactive shells and non-interactive subshells.
   - If no early `return` guards exist, place it cleanly near the top of `~/.bashrc`.
3. **Use a Self-Contained, Silent Snippet**:
   Either call the helper script or inline this self-contained check (which silently no-ops if Chrome is not installed or if Google later removes `DevToolsActivePort`):

```bash
# Sync Windows Chrome DevToolsActivePort into WSL2 (if present and changed)
for _win_dtp in /mnt/c/Users/*/AppData/Local/Google/Chrome/"User Data"/DevToolsActivePort; do
    if [ -f "$_win_dtp" ]; then
        mkdir -p "$HOME/.config/google-chrome"
        [ -L "$HOME/.config/google-chrome/DevToolsActivePort" ] && rm -f "$HOME/.config/google-chrome/DevToolsActivePort"
        cmp -s "$_win_dtp" "$HOME/.config/google-chrome/DevToolsActivePort" || cp -f "$_win_dtp" "$HOME/.config/google-chrome/DevToolsActivePort" 2>/dev/null
        break
    fi
done
unset _win_dtp
```
