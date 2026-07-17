#!/usr/bin/env python3
"""
Cross-platform build script for the SSH Configuration Manager.
Works on Windows, Linux, and macOS.
"""

import subprocess
import sys
import os
import platform

APP_NAME = "SSH_Configuration_Manager"
ENTRY_POINT = "main.py"


def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    print("Installing PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("Failed to install PyInstaller")
        return False


def build_executable():
    """Build the executable using PyInstaller"""
    print("\nBuilding executable...")

    system = platform.system()

    command = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        f"--name={APP_NAME}",
        # Picks up hook-paramiko.py automatically (PyInstaller convention:
        # hook-<module>.py in this directory applies when <module> is used).
        "--additional-hooks-dir=.",
        # customtkinter ships its own theme/asset JSON files that PyInstaller
        # won't find otherwise - collect data+binaries+hiddenimports for it.
        "--collect-all=customtkinter",
        "--clean",
        "--noconfirm",
        ENTRY_POINT,
    ]

    try:
        subprocess.check_call(command)
        print("\nBuild completed successfully!")
        print("\n" + "=" * 60)

        if system == "Windows":
            print(f"Executable created at: dist\\{APP_NAME}.exe")
        else:
            print(f"Executable created at: dist/{APP_NAME}")

        print("=" * 60)
        return True
    except subprocess.CalledProcessError:
        print("\nBuild failed")
        return False


def main():
    system = platform.system()

    print("=" * 60)
    print("SSH Configuration Manager - Cross-Platform Executable Builder")
    print(f"Platform: {system}")
    print("=" * 60)
    print()

    try:
        import PyInstaller  # noqa: F401
        print("PyInstaller is already installed")
    except ImportError:
        print("PyInstaller not found. Installing...")
        if not install_pyinstaller():
            print("\nPlease install PyInstaller manually: pip install pyinstaller")
            return

    if build_executable():
        if system == "Windows":
            print(f"\nYou can now run the executable from: dist\\{APP_NAME}.exe")
        else:
            print(f"\nYou can now run the executable from: dist/{APP_NAME}")
            print("\nTo make it executable on Unix systems, run:")
            print(f"  chmod +x dist/{APP_NAME}")

        print("\nNote: The executable includes all dependencies and can be")
        print(f"distributed to other {system} machines without Python installed.")
    else:
        print("\nBuild process failed. Please check the error messages above.")


if __name__ == "__main__":
    main()
