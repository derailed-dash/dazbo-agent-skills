#!/usr/bin/env bash
# ==============================================================================
# Diagnose and Sync Windows Chrome DevToolsActivePort into WSL2
# ==============================================================================
# Resolves Antigravity browser subagent / Chrome DevTools MCP `--autoConnect`
# failures in WSL2 by copying the active Windows Chrome DevToolsActivePort file
# into ~/.config/google-chrome/DevToolsActivePort as a regular file (avoiding
# sandbox ELOOP symlink errors) and verifying localhost port reachability.
# ==============================================================================

set -euo pipefail

LINUX_CHROME_DIR="${HOME}/.config/google-chrome"
LINUX_PORT_FILE="${LINUX_CHROME_DIR}/DevToolsActivePort"

# 1. Verify WSL2 environment
if ! grep -qi microsoft /proc/version 2>/dev/null; then
    echo "INFO: Not running inside WSL. This script only applies to WSL2 environments."
    exit 0
fi

# 2. Locate Windows Chrome DevToolsActivePort file
WIN_PORT_FILE=""
for candidate in /mnt/c/Users/*/AppData/Local/Google/Chrome/"User Data"/DevToolsActivePort; do
    if [ -f "$candidate" ]; then
        WIN_PORT_FILE="$candidate"
        break
    fi
done

if [ -z "$WIN_PORT_FILE" ]; then
    echo "ERROR: Could not find DevToolsActivePort in any Windows Chrome profile (/mnt/c/Users/*/AppData/Local/Google/Chrome/User Data/DevToolsActivePort)." >&2
    echo "ACTION REQUIRED: Open Google Chrome on Windows, navigate to chrome://inspect/#remote-debugging, and enable remote debugging." >&2
    exit 1
fi

echo "Found Windows DevToolsActivePort: ${WIN_PORT_FILE}"

# 3. Ensure target directory exists and replace any symlink (prevents ELOOP in sandbox)
mkdir -p "$LINUX_CHROME_DIR"
if [ -L "$LINUX_PORT_FILE" ]; then
    echo "Removing symlink at ${LINUX_PORT_FILE} (symlinks across /mnt/c fail with ELOOP inside agent sandboxes)..."
    rm -f "$LINUX_PORT_FILE"
fi

# 4. Copy file if missing or changed
if [ ! -f "$LINUX_PORT_FILE" ] || ! cmp -s "$WIN_PORT_FILE" "$LINUX_PORT_FILE"; then
    cp -f "$WIN_PORT_FILE" "$LINUX_PORT_FILE"
    echo "Synced DevToolsActivePort -> ${LINUX_PORT_FILE}"
else
    echo "DevToolsActivePort at ${LINUX_PORT_FILE} is already up to date."
fi

# 5. Parse port and WebSocket target and verify TCP reachability
PORT="$(sed -n '1p' "$LINUX_PORT_FILE" | tr -d '\r\n')"
WS_PATH="$(sed -n '2p' "$LINUX_PORT_FILE" | tr -d '\r\n')"
echo "Active CDP endpoint: 127.0.0.1:${PORT}${WS_PATH}"

if command -v curl >/dev/null 2>&1; then
    if curl -s --max-time 2 "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
        echo "SUCCESS: Port ${PORT} is reachable on 127.0.0.1 from WSL2."
    else
        echo "WARNING: Port ${PORT} is not responding on 127.0.0.1 inside WSL2." >&2
        echo "  1. Ensure Google Chrome is currently open on Windows with chrome://inspect/#remote-debugging enabled." >&2
        echo "  2. Ensure %USERPROFILE%\\.wslconfig has networkingMode=mirrored under [wsl2]." >&2
        exit 2
    fi
fi
