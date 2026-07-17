"""
Automated installer builder for the SSH Configuration Manager
"""

import subprocess
import os
import sys

def check_executables():
    """Check if executables exist"""
    print("Checking for executables...")
    
    if not os.path.exists("dist/SSH_Configuration_Manager.exe"):
        print("✗ SSH_Configuration_Manager.exe not found!")
        print("\nBuilding regular executable...")
        try:
            subprocess.run([sys.executable, "build_executable.py"], check=True)
            print("✓ Regular executable built")
        except subprocess.CalledProcessError:
            print("✗ Failed to build regular executable")
            return False
    else:
        print("✓ SSH_Configuration_Manager.exe found")
    
    if not os.path.exists("dist/SSH_Configuration_Manager_Debug.exe"):
        print("✗ SSH_Configuration_Manager_Debug.exe not found!")
        print("\nBuilding debug executable...")
        try:
            subprocess.run([sys.executable, "build_debug.py"], check=True)
            print("✓ Debug executable built")
        except subprocess.CalledProcessError:
            print("✗ Failed to build debug executable")
            return False
    else:
        print("✓ SSH_Configuration_Manager_Debug.exe found")
    
    return True

def find_inno_setup():
    """Find Inno Setup compiler"""
    print("\nLooking for Inno Setup...")
    
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]
    
    for path in inno_paths:
        if os.path.exists(path):
            print(f"✓ Found Inno Setup: {path}")
            return path
    
    return None

def build_installer():
    """Build the Windows installer using Inno Setup"""
    print("="*70)
    print("SSH Configuration Manager - Installer Builder")
    print("="*70)
    print()
    
    # Step 1: Check executables
    if not check_executables():
        print("\n✗ Cannot proceed without executables")
        return False
    
    # Step 2: Find Inno Setup
    inno_setup = find_inno_setup()
    if not inno_setup:
        print("\n✗ Inno Setup not found!")
        print("\nPlease install Inno Setup:")
        print("1. Download from: https://jrsoftware.org/isdl.php")
        print("2. Install with default settings")
        print("3. Run this script again")
        print("\nDirect download link:")
        print("https://jrsoftware.org/download.php/is.exe")
        return False
    
    # Step 3: Check for script
    if not os.path.exists("installer_script.iss"):
        print("\n✗ installer_script.iss not found!")
        print("Please ensure the Inno Setup script file exists.")
        return False
    
    print("✓ installer_script.iss found")
    print()
    
    # Step 4: Create installer directory
    os.makedirs("installer", exist_ok=True)
    print("✓ Installer directory ready")
    print()
    
    # Step 5: Build installer
    print("Building installer...")
    print("-" * 70)
    try:
        result = subprocess.run(
            [inno_setup, "installer_script.iss"],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        print("-" * 70)
        print("\n✓ Installer built successfully!")
        print()
        print("="*70)
        print("📦 INSTALLER CREATED")
        print("="*70)
        print()
        print("Location: installer\\SSH_Configuration_Manager_Setup_v2.0.0.exe")

        # Check file size
        installer_path = "installer/SSH_Configuration_Manager_Setup_v2.0.0.exe"
        if os.path.exists(installer_path):
            size_mb = os.path.getsize(installer_path) / (1024 * 1024)
            print(f"Size: {size_mb:.1f} MB")
        
        print()
        print("Next Steps:")
        print("1. Test the installer on this machine")
        print("2. Test on a clean Windows machine")
        print("3. Distribute to users")
        print()
        print("="*70)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("-" * 70)
        print(f"\n✗ Build failed!")
        print(f"\nError: {e}")
        if e.stderr:
            print(f"\nDetails:\n{e.stderr}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False

def main():
    success = build_installer()
    
    if not success:
        print("\n" + "="*70)
        print("Build failed. Please check the errors above.")
        print("="*70)
        sys.exit(1)
    
    print("\nPress Enter to exit...")
    input()
    sys.exit(0)

if __name__ == "__main__":
    main()
