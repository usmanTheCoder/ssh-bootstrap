"""
Build script to create a debug version of the SSH Configuration Manager
(main.py) with a visible console window, for troubleshooting startup or
packaging issues that the windowed build would hide.
"""

import subprocess
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(PROJECT_ROOT)

APP_NAME = "SSH_Configuration_Manager_Debug"
ENTRY_POINT = "main.py"


def build_debug_executable():
    """Build the debug executable with a console window using PyInstaller"""
    print("\nBuilding DEBUG executable (with console window)...")

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        # No --windowed: keep the console so errors are visible.
        # hook-<module>.py in this directory applies when <module> is used).
        f"--name={APP_NAME}",
        "--additional-hooks-dir=scripts",
        "--collect-all=customtkinter",
        "--clean",
        "--noconfirm",
        ENTRY_POINT,
    ]

    try:
        subprocess.check_call(command)
        exe_path = os.path.join("dist", f"{APP_NAME}.exe")
        print("\nDebug build completed successfully!")
        print("\n" + "=" * 60)
        print(f"DEBUG Executable created at: {exe_path}")
        if os.path.exists(exe_path):
            print("File size: ~", os.path.getsize(exe_path) // 1024 // 1024, "MB")
        print("=" * 60)
        print("\nThis version shows a console window with error messages.")
        print("Use this for debugging if the regular version doesn't work.")
        return True
    except subprocess.CalledProcessError:
        print("\nBuild failed")
        return False
    except Exception as e:
        print(f"\nError: {e}")
        return False


def main():
    print("=" * 60)
    print("SSH Configuration Manager - DEBUG Executable Builder")
    print("=" * 60)
    print()

    try:
        import PyInstaller  # noqa: F401
        print("PyInstaller is already installed")
    except ImportError:
        print("PyInstaller not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("PyInstaller installed successfully")
        except Exception:
            print("\nPlease install PyInstaller manually: pip install pyinstaller")
            return

    if build_debug_executable():
        print(f"\nYou can now run the DEBUG executable from: dist\\{APP_NAME}.exe")
        print("\nThis version will show any error messages in a console window.")
    else:
        print("\nBuild process failed. Please check the error messages above.")


if __name__ == "__main__":
    main()
