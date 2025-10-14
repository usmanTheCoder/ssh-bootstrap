"""
Build script to create standalone executable for SSH Bootstrap GUI
Developed by M. Usman Sharif & M. Umair Khan
"""

import subprocess
import sys
import os

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    print("Installing PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to install PyInstaller")
        return False

def build_executable():
    """Build the executable using PyInstaller"""
    print("\nBuilding executable...")
    
    # PyInstaller command with options
    command = [
        "pyinstaller",
        "--onefile",                          # Create a single executable file
        "--windowed",                         # No console window (GUI only)
        "--name=SSH_Bootstrap_Tool",          # Name of the executable
        "--icon=NONE",                        # No icon (you can add one later)
        "--add-data=remote_ssh_gui.py;.",    # Include the main script
        "--clean",                            # Clean PyInstaller cache
        "remote_ssh_gui.py"                  # Main script to build
    ]
    
    try:
        subprocess.check_call(command)
        print("\n✓ Build completed successfully!")
        print("\n" + "="*60)
        print("Executable created at: dist\\SSH_Bootstrap_Tool.exe")
        print("="*60)
        return True
    except subprocess.CalledProcessError:
        print("\n✗ Build failed")
        return False

def main():
    print("="*60)
    print("SSH Bootstrap Tool - Executable Builder")
    print("Developed by M. Usman Sharif & M. Umair Khan")
    print("="*60)
    print()
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✓ PyInstaller is already installed")
    except ImportError:
        print("PyInstaller not found. Installing...")
        if not install_pyinstaller():
            print("\nPlease install PyInstaller manually: pip install pyinstaller")
            return
    
    # Build the executable
    if build_executable():
        print("\nYou can now run the executable from: dist\\SSH_Bootstrap_Tool.exe")
        print("\nNote: The executable includes all dependencies and can be")
        print("distributed to other Windows machines without Python installed.")
    else:
        print("\nBuild process failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
