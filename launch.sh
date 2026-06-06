#!/usr/bin/env bash
# NoirPlayer – Linux / macOS launcher
set -e

cd "$(dirname "$0")"

# ── Dependency check ────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.10+ first."
    exit 1
fi

# Check for libmpv (system must provide it on Linux/macOS)
if python3 -c "import ctypes; ctypes.CDLL('libmpv.so.2')" 2>/dev/null; then
    : # Linux libmpv found
elif python3 -c "import ctypes; ctypes.CDLL('libmpv.2.dylib')" 2>/dev/null; then
    : # macOS libmpv found
elif python3 -c "import ctypes; ctypes.CDLL('libmpv.dylib')" 2>/dev/null; then
    : # macOS libmpv (alt name) found
else
    echo ""
    echo "  libmpv not found on your system."
    echo ""
    echo "  Linux:  sudo apt install libmpv-dev    (Debian/Ubuntu)"
    echo "          sudo dnf install mpv-libs       (Fedora)"
    echo "          sudo pacman -S mpv              (Arch)"
    echo ""
    echo "  macOS:  brew install mpv"
    echo ""
    echo "  Then run this script again."
    echo ""
    exit 1
fi

# ── Virtual environment ─────────────────────────────────────────────────────
if [ ! -f "venv/bin/activate" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Checking dependencies..."
pip install --quiet --upgrade PyQt6 python-mpv

echo "Launching NoirPlayer..."
echo ""
python3 player.py
