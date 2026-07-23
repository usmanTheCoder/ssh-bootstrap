#!/bin/bash
# Cross-platform build script for Linux and macOS

echo "============================================================"
echo "SSH Configuration Manager - Build Script"
echo "Platform: $(uname -s)"
echo "============================================================"
echo

# Change to project root
cd "$(dirname "$0")/.."

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
pyinstaller --onefile --windowed --name=SSH_Configuration_Manager --additional-hooks-dir=scripts --collect-all=customtkinter --clean --noconfirm main.py

echo
echo "============================================================"
if [ -f "dist/SSH_Configuration_Manager" ]; then
    echo "BUILD SUCCESSFUL!"
    echo "Executable location: dist/SSH_Configuration_Manager"
    echo
    echo "Making executable..."
    chmod +x dist/SSH_Configuration_Manager
    echo "Done!"
else
    echo "BUILD FAILED!"
fi
echo "============================================================"
echo
