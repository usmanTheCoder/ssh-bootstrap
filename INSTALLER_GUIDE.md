# Creating an Installer - Complete Guide

**Developed by M. Usman Sharif & M. Umair Khan**

This guide explains how to create a professional Windows installer for SSH Bootstrap Tool.

---

## 📦 Method 1: Using Inno Setup (Recommended)

Inno Setup is a free, professional installer creator for Windows.

### Step 1: Install Inno Setup

1. **Download Inno Setup:**
   - Visit: https://jrsoftware.org/isdl.php
   - Download: `innosetup-6.x.x.exe` (latest version)
   - **Alternative Direct Download:** https://jrsoftware.org/download.php/is.exe

2. **Install Inno Setup:**
   - Run the downloaded installer
   - Follow the installation wizard
   - Default settings are fine

### Step 2: Prepare Files

Ensure you have these files ready:

```
remote_ssh/
├── dist/
│   ├── SSH_Bootstrap_Tool.exe          ✓ Required
│   └── SSH_Bootstrap_Tool_Debug.exe    ✓ Required
├── README.md                            ✓ Required
├── QUICKSTART.md                        ✓ Required
├── TROUBLESHOOTING.md                   ✓ Required
├── LICENSE                              ✓ Required
└── installer_script.iss                 ✓ Required (created)
```

### Step 3: Build Executables First

Before creating installer, build the executables:

```bash
# Build regular version
python build_executable.py

# Build debug version
python build_debug.py
```

### Step 4: Compile the Installer

**Option A: Using Inno Setup GUI**
1. Open Inno Setup Compiler
2. Click `File` → `Open`
3. Select `installer_script.iss`
4. Click `Build` → `Compile`
5. Wait for compilation to complete
6. Installer will be in `installer/` folder

**Option B: Using Command Line**
```bash
# Run from Inno Setup installation directory
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_script.iss
```

**Option C: Using PowerShell Script (Automated)**
```powershell
# Create and run this script
$innoSetup = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
$scriptPath = "installer_script.iss"

if (Test-Path $innoSetup) {
    Write-Host "Building installer..."
    & $innoSetup $scriptPath
    Write-Host "Done! Installer is in the 'installer' folder."
} else {
    Write-Host "Inno Setup not found. Please install from: https://jrsoftware.org/isdl.php"
}
```

### Step 5: Test the Installer

1. Navigate to `installer/` folder
2. Run `SSH_Bootstrap_Tool_Setup_v1.0.0.exe`
3. Follow installation wizard
4. Test the installed application
5. Test uninstallation

---

## 🎯 What the Installer Includes

### Installation Features:
- ✅ **Application files** - Both regular and debug executables
- ✅ **Documentation** - README, Quick Start, Troubleshooting
- ✅ **Start Menu shortcuts** - Easy access to the app
- ✅ **Desktop shortcut** - Optional during installation
- ✅ **Uninstaller** - Clean removal from system
- ✅ **Prerequisites check** - Warns about VC++ requirement
- ✅ **Post-install info** - Shows quick start instructions

### Installation Options:
- **Installation directory** - User can choose location
- **Desktop icon** - Optional checkbox
- **Launch after install** - Optional checkbox
- **Multiple languages** - Easy to add more languages

---

## 🛠️ Customizing the Installer

### Change Version Number

Edit `installer_script.iss`:
```iss
#define MyAppVersion "1.0.0"  ; Change this
```

### Add Custom Icon

1. Create or download an `.ico` file
2. Place it in the project folder
3. Edit `installer_script.iss`:
```iss
SetupIconFile=myicon.ico
```

### Add More Files

Edit the `[Files]` section:
```iss
Source: "path\to\file.txt"; DestDir: "{app}"; Flags: ignoreversion
```

### Change Default Installation Directory

Edit the `[Setup]` section:
```iss
DefaultDirName={autopf}\{#MyAppName}  ; Program Files
; or
DefaultDirName={userpf}\{#MyAppName}  ; User Program Files
```

### Add Custom Messages

Edit the `[Code]` section to customize dialogs and messages.

---

## 📋 Alternative Method: NSIS (Advanced)

If you prefer NSIS (Nullsoft Scriptable Install System):

### Install NSIS
```
Download: https://nsis.sourceforge.io/Download
```

### Create NSIS Script
We've included `installer_script.iss` which can be adapted for NSIS.

---

## 🚀 Quick Build Script

Create `build_installer.py`:

```python
"""
Automated installer builder
Developed by M. Usman Sharif & M. Umair Khan
"""

import subprocess
import os
import sys

def build_installer():
    """Build the Windows installer using Inno Setup"""
    print("="*60)
    print("SSH Bootstrap Tool - Installer Builder")
    print("="*60)
    print()
    
    # Check if Inno Setup is installed
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    
    inno_setup = None
    for path in inno_paths:
        if os.path.exists(path):
            inno_setup = path
            break
    
    if not inno_setup:
        print("✗ Inno Setup not found!")
        print("\nPlease install Inno Setup from:")
        print("https://jrsoftware.org/isdl.php")
        print("\nOr specify the path manually.")
        return False
    
    print(f"✓ Found Inno Setup: {inno_setup}")
    print()
    
    # Check if executables exist
    if not os.path.exists("dist/SSH_Bootstrap_Tool.exe"):
        print("✗ Executable not found!")
        print("Please build the executable first:")
        print("  python build_executable.py")
        return False
    
    print("✓ Executable found")
    print()
    
    # Build installer
    print("Building installer...")
    try:
        result = subprocess.run(
            [inno_setup, "installer_script.iss"],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print("\n✓ Installer built successfully!")
        print("\nInstaller location: installer/SSH_Bootstrap_Tool_Setup_v1.0.0.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        print(e.stderr)
        return False

if __name__ == "__main__":
    success = build_installer()
    if success:
        print("\n" + "="*60)
        print("You can now distribute:")
        print("  installer/SSH_Bootstrap_Tool_Setup_v1.0.0.exe")
        print("="*60)
    sys.exit(0 if success else 1)
```

Save this and run:
```bash
python build_installer.py
```

---

## 📦 Complete Build Process

### Full Build Workflow:

```bash
# 1. Build regular executable
python build_executable.py

# 2. Build debug executable
python build_debug.py

# 3. Build installer
python build_installer.py

# 4. Test installer
.\installer\SSH_Bootstrap_Tool_Setup_v1.0.0.exe
```

---

## ✅ Distribution Checklist

Before distributing the installer:

- [ ] Build latest executables
- [ ] Test executables work
- [ ] Update version number in installer script
- [ ] Update README and documentation
- [ ] Build installer
- [ ] Test installer on clean machine
- [ ] Test installation process
- [ ] Test installed application
- [ ] Test uninstallation
- [ ] Scan with antivirus
- [ ] Sign installer (optional but recommended)

---

## 🔐 Code Signing (Optional)

To avoid "Unknown Publisher" warnings:

### Get a Code Signing Certificate
- **Cost:** $100-400/year
- **Providers:** DigiCert, Sectigo, GlobalSign

### Sign the Installer
```bash
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com SSH_Bootstrap_Tool_Setup_v1.0.0.exe
```

---

## 📊 Installer Size

Expected installer size: **~10-12 MB**

Includes:
- SSH_Bootstrap_Tool.exe (~9 MB)
- SSH_Bootstrap_Tool_Debug.exe (~9 MB)
- Documentation files (~100 KB)
- Compressed with LZMA (~50% compression)

---

## 🌐 Publishing the Installer

### Upload to GitHub Releases:
1. Go to repository on GitHub
2. Click "Releases" → "Create a new release"
3. Tag: `v1.0.0`
4. Upload `SSH_Bootstrap_Tool_Setup_v1.0.0.exe`
5. Add release notes

### Alternative Hosting:
- Google Drive
- Dropbox
- OneDrive
- Your own website
- SourceForge
- Software download sites

---

## 📞 Support

For issues with installer creation:
- **Inno Setup Documentation:** https://jrsoftware.org/ishelp/
- **Inno Setup Forums:** https://groups.google.com/g/innosetup
- **GitHub Issues:** https://github.com/usmanTheCoder/ssh-bootstrap/issues

---

## 🎉 Done!

Your professional Windows installer is ready to distribute!

**Installer Features:**
- ✅ Professional appearance
- ✅ Easy installation
- ✅ Clean uninstallation
- ✅ Start Menu integration
- ✅ Optional desktop shortcut
- ✅ Documentation included
- ✅ Prerequisites check
- ✅ Post-install instructions

**Share your installer with confidence! 🚀**
