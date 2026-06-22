#!/usr/bin/env bash
# Bootstrap Python and optional system dependencies for meta-toolkit.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
VENV_DIR="/root/.venv_xfiltrator"
VENV_CONFIG_FILE="$ROOT/.venv_location"
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
if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    mkdir -p "$VENV_DIR"
    python3 -m venv "$VENV_DIR" || {
        echo "error: failed to create virtual environment at ${VENV_DIR}" >&2
        exit 1
    }
    echo "    Created at: $VENV_DIR"
fi

echo "$VENV_DIR" > "$VENV_CONFIG_FILE"

if [[ ! -f "${VENV_DIR}/bin/python" ]]; then
    echo "error: Python not found at ${VENV_DIR}/bin/python" >&2
    echo "       venv creation may have failed" >&2
    exit 1
fi

echo "==> Upgrading pip"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip

echo "==> Installing Python requirements"
PYTHON_BIN="${VENV_DIR}/bin/python"
if $INSTALL_DEV; then
    "$PYTHON_BIN" -m pip install -r "${ROOT}/requirements-dev.txt"
else
    "$PYTHON_BIN" -m pip install -r "${ROOT}/requirements.txt"
fi

chmod +x "${ROOT}/meta_extract"

echo ""
echo "Done. Now simply run:"
echo "  ./run.sh -f /path/to/file [OPTIONS]"
if $INSTALL_DEV; then
    echo "  pytest"
fi
