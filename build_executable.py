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
    
    # PyInstaller command with custom spec file
    command = [
        "pyinstaller",
        "--clean",                            # Clean PyInstaller cache
        "--noconfirm",                        # Replace output directory without asking
        "ssh_bootstrap.spec"                  # Use custom spec file
    ]
    
    try:
        subprocess.check_call(command)
        print("\n✓ Build completed successfully!")
        print("\n" + "="*60)
        print("Executable created at: dist\\SSH_Bootstrap_Tool.exe")
        print("File size: ~", os.path.getsize("dist\\SSH_Bootstrap_Tool.exe") // 1024 // 1024, "MB" if os.path.exists("dist\\SSH_Bootstrap_Tool.exe") else "")
        print("="*60)
        return True
    except subprocess.CalledProcessError:
        print("\n✗ Build failed")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
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
