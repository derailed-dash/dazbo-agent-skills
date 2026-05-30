#!/usr/bin/env bash
# git-crypt-helper.sh
# Automation utility for managing repository secrets with git-crypt.
# Built for Dazbo's Agentic Skills.

set -euo pipefail

# Ensure we are in a git repository
is_git_repo() {
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "Error: Not inside a git repository." >&2
        return 1
    fi
}

# Print usage instructions
usage() {
    cat <<EOF
Usage: $0 <command> [arguments]

Commands:
  install             Check and attempt to install git-crypt via apt-get.
  init <key_path>     Initialize git-crypt, setup .gitattributes, and export the key.
  unlock <key_path>   Unlock the repository using the provided key.
  sync-to-enc [file]  Sync unencrypted file(s) to their .enc versions (ignores node_modules/etc.).
  sync-from-enc [file] Sync/restore .enc file(s) to their unencrypted versions.
  status              Check git-crypt installation, initialization, and file synchronization state.

Examples:
  $0 init ~/secure-keys/my-project.key
  $0 unlock ~/secure-keys/my-project.key
  $0 sync-to-enc .env
  $0 sync-to-enc
  $0 sync-from-enc
EOF
}

# Ensure unencrypted file is in .gitignore
ensure_ignored() {
    local file="$1"
    if [ ! -f "$file" ]; then
        return
    fi
    local root_dir
    root_dir=$(git rev-parse --show-toplevel)
    local rel_path
    rel_path=$(realpath --relative-to="$root_dir" "$file")
    
    # Create .gitignore if missing
    if [ ! -f "$root_dir/.gitignore" ]; then
        touch "$root_dir/.gitignore"
    fi

    # Check if already ignored
    if ! grep -Fxq "$rel_path" "$root_dir/.gitignore" 2>/dev/null && \
       ! grep -Fxq "/$rel_path" "$root_dir/.gitignore" 2>/dev/null; then
        echo "/$rel_path" >> "$root_dir/.gitignore"
        echo "Added /$rel_path to .gitignore"
    fi
}

# Check and install git-crypt
cmd_install() {
    if command -v git-crypt >/dev/null 2>&1; then
        echo "git-crypt is already installed: $(git-crypt --version | head -n 1)"
        return 0
    fi

    echo "git-crypt is not installed. Attempting installation via apt..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y git-crypt
        echo "git-crypt installed successfully!"
    else
        echo "Error: apt-get not found. Please install git-crypt manually for your OS." >&2
        return 1
    fi
}

# Initialize git-crypt and export key
cmd_init() {
    is_git_repo
    local key_path="${1:-}"
    if [ -z "$key_path" ]; then
        echo "Error: Key path argument is required for init." >&2
        echo "Usage: $0 init <key_path>" >&2
        return 1
    fi

    # Check if git-crypt is installed
    if ! command -v git-crypt >/dev/null 2>&1; then
        echo "git-crypt is not installed. Running install first..."
        cmd_install
    fi

    # Initialize if not already done
    local root_dir
    root_dir=$(git rev-parse --show-toplevel)
    if [ -d "$root_dir/.git-crypt" ] || git-crypt status >/dev/null 2>&1; then
        echo "git-crypt appears already initialized."
    else
        echo "Initializing git-crypt..."
        git-crypt init
    fi

    # Configure .gitattributes if not already done
    local gitattr="$root_dir/.gitattributes"
    local attr_line="*.enc filter=git-crypt diff=git-crypt"
    if [ ! -f "$gitattr" ]; then
        echo "$attr_line" > "$gitattr"
        echo "Created .gitattributes with git-crypt filter configuration."
    else
        if ! grep -Fq "filter=git-crypt" "$gitattr"; then
            echo "$attr_line" >> "$gitattr"
            echo "Added git-crypt filter configuration to .gitattributes."
        else
            echo ".gitattributes already configured for git-crypt."
        fi
    fi

    # Export key
    mkdir -p "$(dirname "$key_path")"
    echo "Exporting secure key to: $key_path"
    git-crypt export-key "$key_path"
    echo "Key exported successfully! Keep this key safe and NEVER check it into the repository."
}

# Unlock repository
cmd_unlock() {
    is_git_repo
    local key_path="${1:-}"
    if [ -z "$key_path" ]; then
        echo "Error: Key path argument is required for unlock." >&2
        echo "Usage: $0 unlock <key_path>" >&2
        return 1
    fi

    if [ ! -f "$key_path" ]; then
        echo "Error: Key file not found at '$key_path'" >&2
        return 1
    fi

    echo "Unlocking repository with key: $key_path"
    git-crypt unlock "$key_path"
    echo "Repository unlocked successfully!"
}

# Sync unencrypted files to their parallel .enc counterparts
cmd_sync_to_enc() {
    is_git_repo
    local target_file="${1:-}"
    local root_dir
    root_dir=$(git rev-parse --show-toplevel)

    if [ -n "$target_file" ]; then
        # Explicit file mode
        if [ ! -f "$target_file" ]; then
            echo "Error: File '$target_file' not found." >&2
            return 1
        fi
        local enc_file="${target_file}.enc"
        echo "Syncing '$target_file' -> '$enc_file'..."
        cp "$target_file" "$enc_file"
        ensure_ignored "$target_file"
    else
        # Suffix-based automatic detection mode
        echo "Scanning repository for active .enc files..."
        local found=0
        # Find all .enc files excluding .git and node_modules
        while IFS= read -r -d '' enc_file; do
            local plain_file="${enc_file%.enc}"
            if [ -f "$plain_file" ]; then
                found=1
                # Sync if plain is newer or if they are different
                if [ "$plain_file" -nt "$enc_file" ] || ! cmp -s "$plain_file" "$enc_file"; then
                    echo "Syncing: $plain_file -> $enc_file"
                    cp "$plain_file" "$enc_file"
                else
                    echo "Up-to-date: $plain_file"
                fi
                ensure_ignored "$plain_file"
            fi
        done < <(find "$root_dir" -name "*.enc" -not -path "*/.git/*" -not -path "*/node_modules/*" -print0)
        
        if [ "$found" -eq 0 ]; then
            echo "No parallel .enc files found to sync. Run '$0 sync-to-enc <file>' to set one up."
        fi
    fi
}

# Sync/restore .enc files to their unencrypted counterparts
cmd_sync_from_enc() {
    is_git_repo
    local target_file="${1:-}"
    local root_dir
    root_dir=$(git rev-parse --show-toplevel)

    if [ -n "$target_file" ]; then
        # Explicit file mode
        local enc_file
        if [[ "$target_file" == *.enc ]]; then
            enc_file="$target_file"
            target_file="${enc_file%.enc}"
        else
            enc_file="${target_file}.enc"
        fi

        if [ ! -f "$enc_file" ]; then
            echo "Error: Encrypted file '$enc_file' not found." >&2
            return 1
        fi
        echo "Restoring '$enc_file' -> '$target_file'..."
        cp "$enc_file" "$target_file"
        ensure_ignored "$target_file"
    else
        # Suffix-based automatic detection mode
        echo "Scanning repository for .enc files to restore..."
        local found=0
        while IFS= read -r -d '' enc_file; do
            local plain_file="${enc_file%.enc}"
            found=1
            # Copy only if plain is missing or different
            if [ ! -f "$plain_file" ] || ! cmp -s "$enc_file" "$plain_file"; then
                echo "Restoring: $enc_file -> $plain_file"
                cp "$enc_file" "$plain_file"
            else
                echo "Already matches: $plain_file"
            fi
            ensure_ignored "$plain_file"
        done < <(find "$root_dir" -name "*.enc" -not -path "*/.git/*" -not -path "*/node_modules/*" -print0)

        if [ "$found" -eq 0 ]; then
            echo "No .enc files found in the repository."
        fi
    fi
}

# Display state and status check
cmd_status() {
    echo "=== git-crypt Environment Status ==="
    
    # 1. Check CLI Installation
    if command -v git-crypt >/dev/null 2>&1; then
        echo "[OK] git-crypt is installed: $(git-crypt --version | head -n 1)"
    else
        echo "[WARNING] git-crypt is NOT installed. Run '$0 install' to install."
    fi

    # 2. Check Git Repo
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "[ERROR] Not inside a git repository."
        return 0
    fi
    local root_dir
    root_dir=$(git rev-parse --show-toplevel)
    echo "[OK] Inside git repository at: $root_dir"

    # 3. Check initialization
    if [ -d "$root_dir/.git-crypt" ]; then
        echo "[OK] git-crypt has been initialized (.git-crypt folder exists)."
    else
        echo "[INFO] git-crypt is not initialized in this repository."
    fi

    # 4. Check .gitattributes
    local gitattr="$root_dir/.gitattributes"
    if [ -f "$gitattr" ] && grep -Fq "filter=git-crypt" "$gitattr"; then
        echo "[OK] .gitattributes contains git-crypt filter configuration."
    else
        echo "[WARNING] .gitattributes does not configure git-crypt filter."
    fi

    # 5. Check Parallel Secret files status
    echo ""
    echo "=== Secret Files Sync Status ==="
    local found=0
    while IFS= read -r -d '' enc_file; do
        found=1
        local plain_file="${enc_file%.enc}"
        local plain_base
        plain_base=$(basename "$plain_file")
        
        # Check .gitignore
        local ignored="NO"
        if [ -f "$plain_file" ]; then
            local rel_plain
            rel_plain=$(realpath --relative-to="$root_dir" "$plain_file")
            if grep -Fxq "$rel_plain" "$root_dir/.gitignore" 2>/dev/null || \
               grep -Fxq "/$rel_plain" "$root_dir/.gitignore" 2>/dev/null; then
                ignored="YES"
            fi
        fi

        # Check sync and diff
        if [ ! -f "$plain_file" ]; then
            echo "[-] $plain_base.enc -> (Plaintext file missing! Run '$0 sync-from-enc')"
        elif ! cmp -s "$plain_file" "$enc_file"; then
            echo "[!] $plain_base <-> $plain_base.enc DO NOT MATCH! (Plaintext is modified, run '$0 sync-to-enc')"
        else
            echo "[OK] $plain_base matches $plain_base.enc (Ignored in git: $ignored)"
        fi
    done < <(find "$root_dir" -name "*.enc" -not -path "*/.git/*" -not -path "*/node_modules/*" -print0)

    if [ "$found" -eq 0 ]; then
        echo "No secrets files tracked using .enc suffix found."
    fi
}

# Main Command Dispatcher
main() {
    if [ $# -lt 1 ]; then
        usage
        exit 1
    fi

    local command="$1"
    shift

    case "$command" in
        install)
            cmd_install "$@"
            ;;
        init)
            cmd_init "$@"
            ;;
        unlock)
            cmd_unlock "$@"
            ;;
        sync-to-enc)
            cmd_sync_to_enc "$@"
            ;;
        sync-from-enc)
            cmd_sync_from_enc "$@"
            ;;
        status)
            cmd_status "$@"
            ;;
        help|-h|--help)
            usage
            ;;
        *)
            echo "Unknown command: $command" >&2
            usage
            exit 1
            ;;
    esac
}

main "$@"
