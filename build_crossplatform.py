#!/usr/bin/env python3
"""
Cross-platform build script for SSH Bootstrap Tool
Developed by M. Usman Sharif & M. Umair Khan
Works on Windows, Linux, and macOS
"""

import subprocess
import sys
import os
import platform

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
    
    # Detect platform
    system = platform.system()
    
    # Set executable name based on platform
    if system == "Windows":
        exe_name = "SSH_Bootstrap_Tool"
        separator = ";"
    elif system == "Darwin":  # macOS
        exe_name = "SSH_Bootstrap_Tool"
        separator = ":"
    else:  # Linux
        exe_name = "SSH_Bootstrap_Tool"
        separator = ":"
    
    # PyInstaller command with options
    command = [
        "pyinstaller",
        "--onefile",                              # Create a single executable file
        "--windowed",                             # No console window (GUI only)
        f"--name={exe_name}",                     # Name of the executable
        "--icon=NONE",                            # No icon (you can add one later)
        f"--add-data=remote_ssh_gui.py{separator}.",  # Include the main script
        "--clean",                                # Clean PyInstaller cache
        "remote_ssh_gui.py"                       # Main script to build
    ]
    
    try:
        subprocess.check_call(command)
        print("\n✓ Build completed successfully!")
        print("\n" + "="*60)
        
        if system == "Windows":
            print(f"Executable created at: dist\\{exe_name}.exe")
        else:
            print(f"Executable created at: dist/{exe_name}")
        
        print("="*60)
        return True
    except subprocess.CalledProcessError:
        print("\n✗ Build failed")
        return False

def main():
    system = platform.system()
    
    print("="*60)
    print("SSH Bootstrap Tool - Cross-Platform Executable Builder")
    print("Developed by M. Usman Sharif & M. Umair Khan")
    print(f"Platform: {system}")
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
        if system == "Windows":
            print("\nYou can now run the executable from: dist\\SSH_Bootstrap_Tool.exe")
        else:
            print("\nYou can now run the executable from: dist/SSH_Bootstrap_Tool")
            print("\nTo make it executable on Unix systems, run:")
            print("  chmod +x dist/SSH_Bootstrap_Tool")
        
        print("\nNote: The executable includes all dependencies and can be")
        print(f"distributed to other {system} machines without Python installed.")
    else:
        print("\nBuild process failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
