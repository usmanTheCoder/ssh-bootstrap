# 🔐 SSH Configuration Manager - Cross-Platform Notes

A complete SSH configuration management application, designed to run on
Windows, Linux, and macOS.

**Developed by M. Usman Sharif & M. Umair Khan**

---

## 🌍 Platform Status

✅ **Windows** (10/11) - fully built, packaged, and tested
🧪 **Linux** (Ubuntu, Debian, Fedora, Arch, etc.) - supported by design, not yet packaged/tested
🧪 **macOS** (10.14+) - supported by design, not yet packaged/tested

The core application (`sshmgr/`) is OS-agnostic: `Path.home() / ".ssh" / "config"`
resolves correctly everywhere, and the SSH config engine, key management, and
Git sync logic don't depend on Windows-specific APIs. Only the Windows build
has actually been produced and run so far - if you package and run this on
Linux or macOS, please report back what you find.

---

## ✨ Features

- 🖥️ **Dashboard** - host/jump-host counts, sync status, quick actions
- 🗂️ **Server/VM Management** - add, edit, duplicate, delete, search/filter
- 🧭 **Jump Host Management** - configure once, cascading updates to dependents
- 🔑 **SSH Key Management** - use existing, generate new, or skip - independent of server config
- 📝 **SSH Configuration Engine** - managed block inside `~/.ssh/config`, validated before every save, never duplicates `Host` entries, never touches unrelated content
- 🔄 **Git Synchronization** - GitHub-backed backup/restore with conflict handling
- 🎨 **Modern UI** - customtkinter-based, light/dark mode, toast notifications

---

## 🚀 Quick Start

### Option 1: Run the Executable (Recommended)

#### Windows:
```
dist\SSH_Configuration_Manager.exe
```

#### Linux/macOS (untested - build it yourself first, see below):
```bash
chmod +x dist/SSH_Configuration_Manager
./dist/SSH_Configuration_Manager
```

### Option 2: Run from Source
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
# or on Linux/macOS
python3 main.py
```

---

## 📋 Requirements

### For the executable:
- **Windows**: OpenSSH client (pre-installed on Windows 10/11)
- **Linux**: openssh-client (usually pre-installed)
- **macOS**: OpenSSH (pre-installed)
- **All platforms**: Git, only if you use Git Synchronization

### For running from source:
- Python 3.10+
- See `requirements.txt` (paramiko, cryptography, customtkinter, GitPython, keyring, requests)
- tkinter (usually included with Python; see platform notes below for Linux/macOS)

---

## 🎯 How to Use

1. **Launch the application**
2. **Dashboard** - see current host/jump-host counts and sync status
3. **Servers → + Add Server/VM** - Host Alias, Hostname/IP, Username, Port, a key (existing/new/skip), and an optional Jump Host
4. **Jump Hosts** (optional) - configure a bastion once, reuse it anywhere
5. **SSH Configuration** - view, import, export, or (advanced) hand-edit the generated config
6. **Git Synchronization** (optional) - connect a GitHub repo via Personal Access Token

Every change is validated and written to `~/.ssh/config` automatically.

---

## 🛠️ Build Instructions

### Build for Your Platform

#### Method 1: Python Script (All Platforms)
```bash
python build_crossplatform.py
# or
python3 build_crossplatform.py
```

#### Method 2: Shell Script (Linux/macOS)
```bash
chmod +x build.sh
./build.sh
```

#### Method 3: Batch File (Windows)
```cmd
build.bat
```

#### Method 4: Manual PyInstaller
```bash
pip install pyinstaller

# All platforms
pyinstaller --onefile --windowed --name=SSH_Configuration_Manager \
  --additional-hooks-dir=. --collect-all=customtkinter --clean main.py

# Linux/macOS: mark it executable afterward
chmod +x dist/SSH_Configuration_Manager
```

`--additional-hooks-dir=.` picks up `hook-paramiko.py`'s hidden imports;
`--collect-all=customtkinter` is required to bundle customtkinter's theme
assets - without it the packaged app won't render correctly.

The executable will be created in the `dist` folder.

---

## 📁 Project Structure

```
ssh-bootstrap/
├── main.py                     # Application entry point
├── sshmgr/                     # Core application package (OS-agnostic)
│   └── ui/                     #   customtkinter screens
├── remote_ssh_gui.py           # Legacy single-purpose tool (superseded)
├── remote_ssh_bootstrap_ssh.py # Legacy CLI version
├── build_crossplatform.py     # Cross-platform build script
├── build_executable.py         # Windows-focused build script
├── build.bat                   # Windows batch build script
├── build.sh                    # Linux/macOS shell build script
├── requirements.txt            # Python dependencies
├── README.md                   # Main documentation
└── dist/
    └── SSH_Configuration_Manager[.exe]  # Standalone executable
```

---

## 🐛 Troubleshooting

### All Platforms

#### "ssh-keygen not found"
Install OpenSSH client for your platform (see Installation Notes below).

#### Git Synchronization: "GitHub authentication failed"
The Personal Access Token needs `repo` scope.

### Windows Specific

```powershell
# Check if OpenSSH is installed
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH*'

# Install if missing
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

### Linux Specific

```bash
# Ubuntu/Debian
sudo apt-get install openssh-client

# Fedora/RHEL
sudo dnf install openssh-clients

# Arch
sudo pacman -S openssh
```

### macOS Specific

- macOS has OpenSSH pre-installed
- Check System Preferences > Security & Privacy if the app is blocked from network access

---

## 📝 Installation Notes

### Linux
You may need `tkinter` (the base library customtkinter builds on) installed separately:

```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

### macOS
Tkinter is included with Python from python.org. If using Homebrew:

```bash
brew install python-tk@3.11
```

---

## 👨‍💻 Developers

**M. Usman Sharif & M. Umair Khan**

---

## 📄 License

This project is provided as-is for personal and educational use.

---

## 🤝 Contributing

Feel free to fork, modify, and enhance this tool! Linux/macOS build reports
and fixes are especially welcome since that side is untested.

---

**Manage your SSH configuration with confidence, on any platform. 🚀**
