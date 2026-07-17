"""
Build script to create a standalone executable for the SSH Configuration
Manager (main.py). Invokes PyInstaller directly with explicit flags rather
than relying on a hand-edited .spec file, so a fresh clone can build
without any prior manual step.
"""

import subprocess
import sys
import os

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
        exe_path = os.path.join("dist", f"{APP_NAME}.exe")
        print("\nBuild completed successfully!")
        print("\n" + "=" * 60)
        print(f"Executable created at: {exe_path}")
        if os.path.exists(exe_path):
            print("File size: ~", os.path.getsize(exe_path) // 1024 // 1024, "MB")
        print("=" * 60)
        return True
    except subprocess.CalledProcessError:
        print("\nBuild failed")
        return False
    except Exception as e:
        print(f"\nError: {e}")
        return False


def main():
    print("=" * 60)
    print("SSH Configuration Manager - Executable Builder")
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
        print(f"\nYou can now run the executable from: dist\\{APP_NAME}.exe")
        print("\nNote: The executable includes all dependencies and can be")
        print("distributed to other Windows machines without Python installed.")
    else:
        print("\nBuild process failed. Please check the error messages above.")


if __name__ == "__main__":
    main()
