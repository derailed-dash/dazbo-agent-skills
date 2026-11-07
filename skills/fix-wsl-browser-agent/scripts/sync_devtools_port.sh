#!/usr/bin/env bash
# ==============================================================================
# Diagnose and Sync Windows Chrome DevToolsActivePort into WSL2
# ==============================================================================
# Resolves Antigravity browser subagent / Chrome DevTools MCP `--autoConnect`
# failures in WSL2 by:
#   1. Killing any legacy `socat TCP-LISTEN:9222` forwarders that hijack port 9222
#   2. Copying the active Windows Chrome DevToolsActivePort file into
#      ~/.config/google-chrome/DevToolsActivePort as a regular file (avoiding
#      sandbox ELOOP symlink errors)
#   3. Verifying localhost port reachability and deterministically diagnosing
#      Windows netstat vs WSL2 NAT/mirrored networking state.
# ==============================================================================

set -euo pipefail

LINUX_CHROME_DIR="${HOME}/.config/google-chrome"
LINUX_PORT_FILE="${LINUX_CHROME_DIR}/DevToolsActivePort"

# 1. Verify WSL2 environment
if ! grep -qi microsoft /proc/version 2>/dev/null; then
    echo "INFO: Not running inside WSL. This script only applies to WSL2 environments."
    exit 0
fi

# 2. Detect and terminate legacy socat port-9222 forwarders (Boundary 4)
if pgrep -f "socat TCP-LISTEN:9222" >/dev/null 2>&1; then
    echo "WARNING: Detected legacy 'socat TCP-LISTEN:9222' daemon hijacking port 9222 in WSL2."
    echo "         (Chrome only binds to 127.0.0.1:9222 on Windows, so forwarding to the NAT IP hangs.)"
    pkill -f "socat TCP-LISTEN:9222" || true
    echo "         Terminated legacy socat process(es)."
fi
if [ -f "${HOME}/.bashrc" ] && grep -q "socat TCP-LISTEN:9222" "${HOME}/.bashrc" 2>/dev/null; then
    echo "NOTE: Remove the obsolete 'socat TCP-LISTEN:9222' block from ~/.bashrc."
fi

# 3. Locate Windows Chrome DevToolsActivePort file (Boundary 2)
WIN_PORT_FILE=""
WIN_USER_DIR=""
for candidate in /mnt/c/Users/*/AppData/Local/Google/Chrome/"User Data"/DevToolsActivePort; do
    if [ -f "$candidate" ]; then
        WIN_PORT_FILE="$candidate"
        WIN_USER_DIR="${candidate%/AppData/Local/Google/Chrome/User Data/DevToolsActivePort}"
        break
    fi
done

if [ -z "$WIN_PORT_FILE" ]; then
    echo "ERROR: Could not find DevToolsActivePort in any Windows Chrome profile (/mnt/c/Users/*/AppData/Local/Google/Chrome/User Data/DevToolsActivePort)." >&2
    echo "ACTION REQUIRED: Open Google Chrome on Windows, navigate to chrome://inspect/#remote-debugging, and enable remote debugging." >&2
    exit 1
fi

echo "Found Windows DevToolsActivePort: ${WIN_PORT_FILE}"

# 4. Ensure target directory exists and replace any symlink (Boundary 3: prevents ELOOP in sandbox)
mkdir -p "$LINUX_CHROME_DIR"
if [ -L "$LINUX_PORT_FILE" ]; then
    echo "Removing symlink at ${LINUX_PORT_FILE} (symlinks across /mnt/c fail with ELOOP inside agent sandboxes)..."
    rm -f "$LINUX_PORT_FILE"
fi

# 5. Copy file if missing or changed
if [ ! -f "$LINUX_PORT_FILE" ] || ! cmp -s "$WIN_PORT_FILE" "$LINUX_PORT_FILE"; then
    cp -f "$WIN_PORT_FILE" "$LINUX_PORT_FILE"
    echo "Synced DevToolsActivePort -> ${LINUX_PORT_FILE}"
else
    echo "DevToolsActivePort at ${LINUX_PORT_FILE} is already up to date."
fi

# 6. Parse port and WebSocket target and verify TCP reachability (Boundary 1)
PORT="$(sed -n '1p' "$LINUX_PORT_FILE" | tr -d '\r\n')"
WS_PATH="$(sed -n '2p' "$LINUX_PORT_FILE" | tr -d '\r\n')"
echo "Active CDP endpoint: 127.0.0.1:${PORT}${WS_PATH}"

if command -v curl >/dev/null 2>&1; then
    if curl -s --max-time 2 "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
        echo "SUCCESS: Port ${PORT} is reachable on 127.0.0.1 from WSL2."
        exit 0
    fi

    echo "WARNING: Port ${PORT} is not responding on 127.0.0.1 inside WSL2." >&2

    # Deterministically check if Windows is listening on 127.0.0.1:<PORT>
    WIN_LISTENING=false
    if [ -x "/mnt/c/Windows/System32/netstat.exe" ]; then
        if (/mnt/c/Windows/System32/netstat.exe -ano 2>/dev/null || true) | grep -q ":${PORT}.*LISTENING"; then
            WIN_LISTENING=true
        fi
    fi

    # Check if WSL2 is running in NAT mode
    WSL_NAT_MODE=false
    if command -v ip >/dev/null 2>&1 && ip route show 2>/dev/null | grep -qE "^default via (172\.|192\.168\.|10\.)"; then
        WSL_NAT_MODE=true
    fi

    # Check .wslconfig state
    WSLCONFIG_FILE="${WIN_USER_DIR}/.wslconfig"
    WSLCONFIG_MIRRORED=false
    if [ -n "$WIN_USER_DIR" ] && [ -f "$WSLCONFIG_FILE" ] && grep -qi "networkingMode[[:space:]]*=[[:space:]]*mirrored" "$WSLCONFIG_FILE" 2>/dev/null; then
        WSLCONFIG_MIRRORED=true
    fi

    if [ "$WIN_LISTENING" = true ] && [ "$WSL_NAT_MODE" = true ]; then
        echo "DIAGNOSIS: Windows Chrome IS listening on Windows 127.0.0.1:${PORT}, but WSL2 is currently running in NAT mode." >&2
        if [ "$WSLCONFIG_MIRRORED" = true ]; then
            echo "  - ${WSLCONFIG_FILE} already has 'networkingMode=mirrored' configured." >&2
            echo "  - ACTION REQUIRED: Run 'wsl --shutdown' in Windows PowerShell/Terminal and restart WSL to activate mirrored networking." >&2
        else
            echo "  - ACTION REQUIRED: Add 'networkingMode=mirrored' under [wsl2] in ${WSLCONFIG_FILE}, then run 'wsl --shutdown' in Windows PowerShell." >&2
        fi
    elif [ "$WIN_LISTENING" = false ]; then
        echo "DIAGNOSIS: Windows Chrome is NOT currently listening on 127.0.0.1:${PORT} (DevToolsActivePort may be stale from a closed session)." >&2
        echo "  - ACTION REQUIRED: Ensure Google Chrome is open on Windows with chrome://inspect/#remote-debugging enabled." >&2
    else
        echo "  1. Ensure Google Chrome is currently open on Windows with chrome://inspect/#remote-debugging enabled." >&2
        echo "  2. Ensure %USERPROFILE%\\.wslconfig has networkingMode=mirrored under [wsl2] and restart WSL ('wsl --shutdown')." >&2
    fi
    exit 2
fi
