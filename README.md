# 🔐 SSH Configuration Manager

A complete SSH configuration management application: manage servers, jump hosts,
and SSH keys through a modern GUI, with `~/.ssh/config` generated and validated
automatically, and optional Git-based backup/sync.

**Developed by M. Usman Sharif & M. Umair Khan**

---

## ✨ Features

- 🖥️ **Dashboard** - host/jump-host counts, sync status, one-click quick actions
- 🗂️ **Server/VM Management** - add, edit, duplicate, delete, search/filter, all reflected in `~/.ssh/config` instantly
- 🧭 **Jump Host (Bastion) Management** - configure once, reference from any server; edits/deletes cascade to every dependent server automatically
- 🔑 **SSH Key Management** - use an existing key, generate a new one, or skip key management entirely (key generation is optional, not mandatory)
- 📝 **SSH Configuration Engine** - owns a managed block inside `~/.ssh/config`, never touches your existing unmanaged entries, validates before every save, never creates duplicate `Host` entries
- 📥📤 **Import/Export** - import an existing SSH config (jump hosts inferred automatically from `ProxyJump`), export a portable copy
- ✍️ **Advanced Manual Editing** - optional raw-text edit mode with validation before save, for anything the structured UI doesn't cover
- 🔄 **Git Synchronization** - back up and restore your SSH configuration via a GitHub repository (PAT-authenticated), with conflict detection and resolution
- 🎨 **Modern UI** - light/dark mode, sidebar navigation, toast notifications

---

## 🚀 Quick Start

### Option 1: Run the Executable (Recommended)
```
dist\SSH_Configuration_Manager.exe
```
**No Python installation required!** Just download and run.

**Platform:** Windows 64-bit (Linux/macOS support planned)

### Option 2: Run from Source
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

---

## 📋 Requirements

### For the executable:
- Windows 10/11
- OpenSSH client (usually pre-installed)
- Git (only needed if you use the Git Synchronization feature)

### For running from source:
- Python 3.10+
- See `requirements.txt` (paramiko, customtkinter, GitPython, keyring, requests, cryptography)

---

## 🎯 How to Use

1. **Launch the application** - `python main.py` or the packaged `.exe`
2. **Dashboard** - see your current host/jump-host counts and sync status
3. **Add a Server/VM** - Host Alias, Hostname/IP, Username, Port, an existing/new/skip SSH key, and an optional Jump Host
4. **Add a Jump Host** (optional) - servers can reference it; editing or deleting it updates every dependent server's `ProxyJump` automatically
5. **SSH Configuration tab** - view the generated config, import an existing one, export a copy, or (advanced) edit the raw file directly with pre-save validation
6. **Git Synchronization tab** (optional) - connect a GitHub repo with a Personal Access Token, then push/pull your configuration as a backup

Every add/edit/delete you make regenerates and validates `~/.ssh/config` immediately - you should never need to hand-edit it for normal use.

---

## 🛠️ Build Instructions

### Build the Executable Yourself

#### Method 1: Using Python Script
```bash
python build_executable.py
```

#### Method 2: Using Batch File (Windows)
```bash
build.bat
```

#### Method 3: Manual PyInstaller
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name=SSH_Configuration_Manager --additional-hooks-dir=. --collect-all=customtkinter --clean main.py
```
`--additional-hooks-dir=.` picks up `hook-paramiko.py`; `--collect-all=customtkinter` bundles customtkinter's theme/asset files, which PyInstaller won't find otherwise.

The executable will be created in the `dist` folder.

---

## 📁 Project Structure

```
ssh-bootstrap/
├── main.py                     # Application entry point
├── sshmgr/                     # Core application package
│   ├── models.py                #   Server / JumpHost / SSHKey / Settings data models
│   ├── store.py                 #   JSON-backed app state + CRUD/validation
│   ├── ssh_config.py            #   ~/.ssh/config generation, validation, import/export
│   ├── keys.py                  #   SSH key generation/discovery
│   ├── deploy.py                #   Deploy a key to a server over password auth
│   ├── git_sync.py               #   GitHub-backed backup/sync
│   └── ui/                      #   CustomTkinter screens (Dashboard, Servers, Jump Hosts, ...)
├── tests/                      # pytest suite for the core engine
├── remote_ssh_gui.py           # Legacy single-purpose bootstrap tool (superseded by main.py)
├── remote_ssh_bootstrap_ssh.py # Legacy CLI version
├── build_executable.py         # Python build script
├── build.bat / build.sh        # Platform build scripts
├── requirements.txt            # Python dependencies
└── dist/                       # Standalone executable (after building)
```

---

## 🔧 Technical Details

### Single source of truth
`sshmgr/ssh_config.py` owns a marked "managed block" inside `~/.ssh/config`. Only
that block is ever regenerated; anything else already in your config file - or
added outside the markers by another tool - is left untouched. Every save is
validated (structurally and via a real SSH-config parse) before anything
touches disk, with an automatic `.bak` backup of whatever was there before.

### Git Synchronization
Authentication is a GitHub Personal Access Token, stored via your OS credential
store (`keyring`) - never written to disk in plain text. The repo holds one
portable config file; pushing writes/commits/pushes your current state, pulling
treats the repo as the source of truth (added/updated/removed hosts are
reconciled into the local app state), and conflicts are detected and can be
resolved by keeping either the local or remote version.

### Dependencies
- **paramiko** / **cryptography** - SSH protocol + key generation
- **customtkinter** - modern themed GUI (built on Tkinter)
- **GitPython** - Git operations for synchronization
- **keyring** - secure OS-level credential storage
- **requests** - GitHub API calls (token validation)

---

## 🐛 Troubleshooting

### "PyInstaller not found"
```bash
pip install pyinstaller
```

### App builds but the packaged .exe won't launch / looks broken
Make sure the build included `--collect-all=customtkinter` - without it, the
executable is missing customtkinter's theme JSON files.

### "ssh-keygen not found" / "Deploy key" fails
Ensure OpenSSH client is installed and on `PATH` (Windows: usually pre-installed
under `C:\Windows\System32\OpenSSH\`).

### Git Synchronization errors
- "GitHub authentication failed" - check the Personal Access Token has `repo` scope.
- "Push rejected" - someone else (or another machine) pushed since your last
  sync; use Pull first, resolve any conflict, then push again.

---

## 📝 Notes

- SSH keys are stored in `C:\Users\<YourUsername>\.ssh\`; existing keys are
  reused, never overwritten.
- The app's own data (server/jump-host list, settings) lives in
  `C:\Users\<YourUsername>\.ssh-bootstrap-manager\data.json` - separate from
  the actual SSH config file it generates.

---

## 👨‍💻 Developers

**M. Usman Sharif & M. Umair Khan**

---

## 📄 License

This project is provided as-is for personal and educational use.

---

**Manage your SSH configuration with confidence. 🚀**
