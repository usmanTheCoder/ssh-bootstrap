# Distribution Guide - SSH Configuration Manager

## 📦 Distributing the Application

### What to Share

The standalone executable is located at:
```
dist\SSH_Configuration_Manager.exe
```

**File Details:**
- **Size:** ~20-25 MB (customtkinter's bundled assets make this larger than the old single-purpose tool)
- **Platform:** Windows 64-bit
- **Type:** Standalone executable
- **Dependencies:** None (all included)

---

## 🚀 Distribution Methods

### 1. Direct File Sharing
Simply share the `SSH_Configuration_Manager.exe` file via:
- Email attachment
- USB drive
- Network share
- Cloud storage (Google Drive, Dropbox, OneDrive)

### 2. GitHub Releases (Recommended)
1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Tag version: `v2.0.0`
4. Upload `SSH_Configuration_Manager.exe` as a release asset
5. Add release notes from `RELEASE_NOTES.md`

### 3. Internal Network Distribution
- Place on shared network drive
- Add to company software repository
- Include in IT deployment packages

---

## 📋 User Instructions

When sharing the executable, include these simple instructions:

```
SSH Configuration Manager
==========================

Quick Start:
1. Download SSH_Configuration_Manager.exe
2. Double-click to run (no installation needed)
3. From the Dashboard, add a Server/VM or import an existing SSH config
4. Optionally set up a Jump Host, generate/select an SSH key, and connect
   Git Synchronization for backup
5. Every change is written to ~/.ssh/config automatically
6. Connect: ssh <alias-you-chose>

Requirements:
- Windows 10 or 11
- OpenSSH client (pre-installed on Windows 10/11)
- Git, only if using Git Synchronization

Developed by M. Usman Sharif & M. Umair Khan
```

---

## ⚠️ Important Notes

### Antivirus Warnings
Some antivirus software may flag PyInstaller executables as suspicious. This is a false positive. To resolve:

1. **For Users:**
   - Add exception in antivirus software
   - Right-click → Properties → Unblock

2. **For Developers:**
   - Sign the executable with a code signing certificate
   - Submit to antivirus vendors for whitelisting

### Windows SmartScreen
First-time users may see "Windows protected your PC" message:
1. Click "More info"
2. Click "Run anyway"

**To avoid this:** Sign the executable with a trusted certificate.

---

## 🔧 Rebuilding the Executable

If you need to rebuild with changes:

```bash
# 1. Make your changes under sshmgr/ (or main.py)
# 2. Run the build script
python build_executable.py

# 3. New executable will be in dist\SSH_Configuration_Manager.exe
```

### Build Options

`build_executable.py` invokes PyInstaller with:

```bash
pyinstaller --onefile --windowed --name=SSH_Configuration_Manager \
  --additional-hooks-dir=. --collect-all=customtkinter --clean main.py
```

- `--additional-hooks-dir=.` picks up `hook-paramiko.py`'s hidden imports automatically
- `--collect-all=customtkinter` is required - without it, the packaged app is
  missing customtkinter's theme/asset JSON files and will fail to render correctly
- Add `--icon=myicon.ico` for a custom icon
- Use `--onedir` instead of `--onefile` to produce a folder instead of a single file

---

## 📊 File Size Optimization

The executable is larger than a typical Tkinter app because it includes:
- Python interpreter
- customtkinter (+ its theme assets) and standard tkinter
- paramiko / cryptography (SSH + crypto)
- GitPython, keyring, requests (Git Synchronization)

**To reduce size:**
1. Use `--onedir` instead of `--onefile` (creates folder with DLLs, faster startup)
2. Use UPX compression: `--upx-dir=path/to/upx`
3. Exclude unused modules: `--exclude-module=module_name`

---

## 🌐 Cross-Platform Distribution

The application's core logic (`sshmgr/`) is OS-agnostic - `Path.home() / ".ssh" / "config"`
resolves correctly on Windows, Linux, and macOS. Only Windows packaging has
been verified so far; Linux/macOS builds should work but haven't been tested.

### macOS
```bash
pyinstaller --onefile --windowed --name=SSH_Configuration_Manager \
  --additional-hooks-dir=. --collect-all=customtkinter main.py
# Output: .app bundle in dist/
```

### Linux
```bash
pyinstaller --onefile --name=ssh-configuration-manager \
  --additional-hooks-dir=. --collect-all=customtkinter main.py
# Output: Linux binary in dist/
```

---

## 📦 Creating an Installer (Optional)

For professional distribution on Windows, use the included `installer_script.iss`
with Inno Setup - see `INSTALLER_GUIDE.md` for the full walkthrough.

---

## ✅ Pre-Distribution Checklist

Before distributing:
- [ ] Test executable on a clean Windows machine
- [ ] Verify no Python installation is needed
- [ ] Check antivirus detection
- [ ] Test on Windows 10 and 11
- [ ] Verify SSH key generation and key deployment work
- [ ] Test adding a server, a jump host, and Git Synchronization end-to-end
- [ ] Include README or user guide
- [ ] Add version number in filename
- [ ] Create release notes
- [ ] Update GitHub repository

---

## 📞 Support

For distribution issues:
- GitHub: https://github.com/usmanTheCoder/ssh-bootstrap

---

**Ready to distribute! 🎉**
