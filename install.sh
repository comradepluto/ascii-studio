#!/usr/bin/env bash
# ASCII Studio — dependency installer.
#
# Installs Pillow, colorama and pyfiglet using your distro's package manager
# when possible, and falls back to pip otherwise.  Run with --pip to force pip.
set -e

cd "$(dirname "$0")"

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
    echo "Python 3 is required but was not found on PATH." >&2
    exit 1
fi

distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    else
        echo ""
    fi
}

pip_install() {
    # Prefer the system/user site over a venv-only install.
    if "$PY" -c "import sys; sys.exit(0 if sys.prefix != sys.base_prefix else 1)" 2>/dev/null; then
        "$PY" -m pip install -r requirements.txt
    else
        "$PY" -m pip install --user -r requirements.txt
    fi
}

FORCE_PIP=0
[ "$1" = "--pip" ] && FORCE_PIP=1

if [ "$FORCE_PIP" = 0 ]; then
    ID="$(distro)"
    case "$ID" in
        arch|manjaro|endeavouros|garuda|cachyos)
            CMD="sudo pacman -S --noconfirm python-pillow python-colorama python-pyfiglet" ;;
        debian|ubuntu|linuxmint|pop|elementary|raspbian|kali)
            CMD="sudo apt-get update && sudo apt-get install -y python3-pil python3-colorama python3-pyfiglet" ;;
        fedora|rhel|centos|rocky|almalinux|nobara)
            CMD="sudo dnf install -y python3-pillow python3-colorama python3-pyfiglet" ;;
        opensuse|opensuse-tumbleweed|suse)
            CMD="sudo zypper install -y python3-Pillow python3-colorama python3-pyfiglet" ;;
        *) CMD="" ;;
    esac

    if [ -n "$CMD" ]; then
        echo "Detected distro: $ID"
        echo "Running: $CMD"
        if eval "$CMD"; then
            echo "OK — dependencies installed via the system package manager."
            exit 0
        fi
        echo "System package install failed; falling back to pip..."
    else
        echo "No known distro detected; falling back to pip..."
    fi
else
    echo "Using pip (--pip requested)..."
fi

pip_install
echo
echo "Done! Launch it with:  python3 ascii_studio.py"
