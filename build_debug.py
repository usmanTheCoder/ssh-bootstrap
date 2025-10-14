"""
Build script to create debug version of SSH Bootstrap GUI with console output
Developed by M. Usman Sharif & M. Umair Khan
"""

import subprocess
import sys
import os

def build_debug_executable():
    """Build the debug executable with console window using PyInstaller"""
    print("\nBuilding DEBUG executable (with console window)...")
    
    # PyInstaller command with custom spec file
    command = [
        "pyinstaller",
        "--clean",                            # Clean PyInstaller cache
        "--noconfirm",                        # Replace output directory without asking
        "ssh_bootstrap_debug.spec"            # Use custom debug spec file
    ]
    
    try:
        subprocess.check_call(command)
        print("\n✓ Debug build completed successfully!")
        print("\n" + "="*60)
        print("DEBUG Executable created at: dist\\SSH_Bootstrap_Tool_Debug.exe")
        if os.path.exists("dist\\SSH_Bootstrap_Tool_Debug.exe"):
            print("File size: ~", os.path.getsize("dist\\SSH_Bootstrap_Tool_Debug.exe") // 1024 // 1024, "MB")
        print("="*60)
        print("\nThis version shows a console window with error messages.")
        print("Use this for debugging if the regular version doesn't work.")
        return True
    except subprocess.CalledProcessError:
        print("\n✗ Build failed")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

def main():
    print("="*60)
    print("SSH Bootstrap Tool - DEBUG Executable Builder")
    print("Developed by M. Usman Sharif & M. Umair Khan")
    print("="*60)
    print()
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✓ PyInstaller is already installed")
    except ImportError:
        print("PyInstaller not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✓ PyInstaller installed successfully")
        except:
            print("\nPlease install PyInstaller manually: pip install pyinstaller")
            return
    
    # Build the debug executable
    if build_debug_executable():
        print("\nYou can now run the DEBUG executable from:")
        print("dist\\SSH_Bootstrap_Tool_Debug.exe")
        print("\nThis version will show any error messages in a console window.")
    else:
        print("\nBuild process failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
