#!/bin/bash
################################################################################
# meta-toolkit wrapper script — auto-activates venv and invokes meta_extract
#
# Usage:
#   ./run.sh -f /path/to/file [--json] [--ai]
#   ./run.sh -d /path/to/directory [--json] [--workers N]
#
# The wrapper automatically sets up and activates a virtual environment on
# first run, so users never need to manually configure dependencies.
################################################################################

set -e

# Determine the directory where this script lives (handles symlinks properly)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
VENV_CONFIG_FILE="$SCRIPT_DIR/.venv_location"
DEFAULT_VENV_DIR="/root/.venv_xfiltrator"

# Determine venv location (check config file first, then fallback to defaults)
if [[ -f "$VENV_CONFIG_FILE" ]]; then
    CANDIDATE_VENV_DIR="$(cat "$VENV_CONFIG_FILE")"
    if [[ -x "$CANDIDATE_VENV_DIR/bin/python" ]]; then
        VENV_DIR="$CANDIDATE_VENV_DIR"
    fi
elif [[ -x "$DEFAULT_VENV_DIR/bin/python" ]]; then
    VENV_DIR="$DEFAULT_VENV_DIR"
elif [[ -x "/root/.venv_meta_toolkit/bin/python" ]]; then
    VENV_DIR="/root/.venv_meta_toolkit"
elif [[ -x "$SCRIPT_DIR/.venv/bin/python" ]]; then
    VENV_DIR="$SCRIPT_DIR/.venv"
else
    VENV_DIR="$DEFAULT_VENV_DIR"  # Default for first-time setup
fi

# Check if virtual environment exists; create it if missing
if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "Virtual environment not found. Setting up dependencies..."
    echo "This will only happen once on first run."
    "$SCRIPT_DIR/install-deps.sh"
    
    # Re-read venv location after install-deps.sh runs (may have been redirected)
    if [[ -f "$VENV_CONFIG_FILE" ]]; then
        CANDIDATE_VENV_DIR="$(cat "$VENV_CONFIG_FILE")"
        if [[ -x "$CANDIDATE_VENV_DIR/bin/python" ]]; then
            VENV_DIR="$CANDIDATE_VENV_DIR"
        fi
    elif [[ -x "$DEFAULT_VENV_DIR/bin/python" ]]; then
        VENV_DIR="$DEFAULT_VENV_DIR"
    fi
else
    # Venv exists—ensure dependencies are installed (idempotent, skips if already installed)
    PYTHON_BIN="$VENV_DIR/bin/python"
    "$PYTHON_BIN" -m pip install -q -r "$SCRIPT_DIR/requirements.txt"
fi

# Use the venv's Python interpreter directly (more reliable than sourcing activate)
PYTHON_BIN="$VENV_DIR/bin/python"

# Invoke meta_extract with all arguments passed through
"$PYTHON_BIN" "$SCRIPT_DIR/meta_extract" "$@"
