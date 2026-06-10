#!/usr/bin/env bash
# Bootstrap Python and optional system dependencies for meta-toolkit.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# --- MODIFIED SECTION ---
# Instead of putting the venv in the shared folder, we put it in a local hidden folder in home.
PROJECT_NAME=$(basename "$ROOT")
VENV_DIR="${HOME}/.venv_${PROJECT_NAME}"
# ------------------------
INSTALL_SYSTEM=false
INSTALL_DEV=false

usage() {
    cat <<'EOF'
Usage: ./install-deps.sh [OPTIONS]

Install meta-toolkit dependencies.

Options:
  --system    Install optional OS packages via apt (Debian/Ubuntu; requires sudo)
  --dev       Install pytest and dev requirements from requirements-dev.txt
  -h, --help  Show this help message

Without --system, only the Python virtual environment and pip packages are installed.
EOF
}

for arg in "$@"; do
    case "$arg" in
        --system) INSTALL_SYSTEM=true ;;
        --dev) INSTALL_DEV=true ;;
        -h|--help) usage; exit 0 ;;
        *) echo "error: unknown option: $arg" >&2; usage; exit 1 ;;
    esac
done

if ! command -v python3 >/dev/null 2>&1; then
    echo "error: python3 not found on PATH" >&2
    exit 1
fi

if $INSTALL_SYSTEM; then
    if command -v apt-get >/dev/null 2>&1; then
        echo "==> Installing system packages (apt)..."
        sudo apt-get update
        sudo apt-get install -y \
            libimage-exiftool-perl \
            mediainfo \
            binwalk \
            binutils
    else
        echo "warning: apt-get not found; skipping system package install" >&2
        echo "          Install exiftool, mediainfo, binwalk, and strings manually." >&2
    fi
fi

echo "==> Creating virtual environment at ${VENV_DIR}"
# Ensure the directory exists locally
if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "==> Upgrading pip"
python -m pip install --upgrade pip

echo "==> Installing Python requirements"
if $INSTALL_DEV; then
    pip install -r "${ROOT}/requirements-dev.txt"
else
    pip install -r "${ROOT}/requirements.txt"
fi

chmod +x "${ROOT}/meta_extract"

echo ""
echo "Done. Activate the environment and run:"
echo "  source ${VENV_DIR}/bin/activate"
echo "  cd ${ROOT}"
echo "  ./meta_extract -f /path/to/file --json"
if $INSTALL_DEV; then
    echo "  pytest"
fi
