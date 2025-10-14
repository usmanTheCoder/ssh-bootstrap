# 🎯 How to Create the Installer - Quick Guide

## Prerequisites

1. **Install Inno Setup** (free):
   - Download: https://jrsoftware.org/isdl.php
   - Or direct: https://jrsoftware.org/download.php/is.exe
   - Install with default settings

## Option 1: Automated Build (Easiest) ⭐

Just run:
```bash
python build_installer.py
```

This will:
- ✅ Build executables if missing
- ✅ Find Inno Setup automatically
- ✅ Create the installer
- ✅ Place it in `installer/` folder

## Option 2: Manual Build

```bash
# 1. Build executables
python build_executable.py
python build_debug.py

# 2. Open Inno Setup Compiler
# 3. Open installer_script.iss
# 4. Click Build → Compile
```

## What You'll Get

**Installer file:**
```
installer/SSH_Bootstrap_Tool_Setup_v1.0.0.exe
```

**Size:** ~10-12 MB (compressed)

## Features

✅ Professional installation wizard
✅ Start Menu shortcuts
✅ Optional desktop icon
✅ Clean uninstaller
✅ Documentation included
✅ Prerequisites check

## Installation includes:
- SSH Bootstrap Tool (main app)
- SSH Bootstrap Tool Debug (troubleshooting)
- Quick Start Guide
- Troubleshooting Guide
- README

## Testing

```bash
# Run the installer
.\installer\SSH_Bootstrap_Tool_Setup_v1.0.0.exe
```

## Distribution

Share the installer file with anyone!

**They only need:**
- Windows 10 or 11
- That's it! No Python, no dependencies!

---

**Created by M. Usman Sharif & M. Umair Khan** 🚀
