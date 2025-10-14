#!/bin/bash
# Cross-platform build script for Linux and macOS
# Developed by M. Usman Sharif & M. Umair Khan

echo "============================================================"
echo "SSH Bootstrap Tool - Build Script"
echo "Developed by M. Usman Sharif & M. Umair Khan"
echo "Platform: $(uname -s)"
echo "============================================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller

# Build the executable
echo
echo "Building executable..."
pyinstaller --onefile --windowed --name=SSH_Bootstrap_Tool --clean remote_ssh_gui.py

echo
echo "============================================================"
if [ -f "dist/SSH_Bootstrap_Tool" ]; then
    echo "BUILD SUCCESSFUL!"
    echo "Executable location: dist/SSH_Bootstrap_Tool"
    echo
    echo "Making executable..."
    chmod +x dist/SSH_Bootstrap_Tool
    echo "✓ Done!"
else
    echo "BUILD FAILED!"
fi
echo "============================================================"
echo
