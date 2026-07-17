# SSH Configuration Manager - Installation Guide

**Developed by M. Usman Sharif & M. Umair Khan**

## 📦 Standalone Executable (Recommended)

### For End Users

The easiest way to use the SSH Configuration Manager is with the standalone executable:

1. **Download** `SSH_Configuration_Manager.exe` from the `dist` folder
2. **Run** the executable by double-clicking it
3. No Python installation required!

**File Location:** `dist\SSH_Configuration_Manager.exe`
**Platform:** Windows 64-bit

### Features
- ✅ No dependencies to install
- ✅ Single executable file
- ✅ Ready to use immediately
- ✅ Can be distributed to any Windows machine

---

## 🔧 Building from Source

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git (only needed for the Git Synchronization feature)

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/usmanTheCoder/ssh-bootstrap.git
   cd ssh-bootstrap
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

### Building Your Own Executable

To create a standalone executable:

```bash
python build_executable.py
```

This bundles `main.py` with PyInstaller, including customtkinter's theme
assets (`--collect-all=customtkinter`) and paramiko's hidden imports (via
`hook-paramiko.py`, picked up with `--additional-hooks-dir=.`). The
executable will be created in the `dist` folder.

---

## 🚀 Usage

1. **Launch** the application
2. **Dashboard** - see host/jump-host counts and sync status
3. **Servers → + Add Server/VM** - Host Alias, Hostname/IP, Username, Port,
   an existing/new/skipped SSH key, and an optional Jump Host
4. **Jump Hosts** (optional) - configure a bastion once, reuse it across servers
5. **SSH Configuration** - view/import/export the generated config, or
   hand-edit it in advanced mode
6. **Git Synchronization** (optional) - connect a GitHub repo with a
   Personal Access Token to back up/restore your configuration
7. **Connect:** `ssh <alias-you-chose>`

Every change made through the app is validated and written to
`~/.ssh/config` automatically - manual editing is optional, not required.

---

## 📋 Requirements (for running from source)

See `requirements.txt`: paramiko, cryptography, customtkinter, GitPython,
keyring, requests.

---

## 🔒 Security Notes

- SSH keys (RSA or Ed25519) are generated locally; private keys never leave your computer
- Private keys are stored in `~/.ssh/` and are never displayed in the UI
- The optional "Deploy key to server" step sends a password only over the
  encrypted SSH connection itself, and only for that one operation
- A connected GitHub Personal Access Token is stored via your OS credential
  store (`keyring`), never in plain text on disk

---

## 🐛 Troubleshooting

### Common Issues

**"ssh-keygen not found"**
- Install OpenSSH client on your system

**"Connection refused" (when deploying a key)**
- Check if SSH server is running on the remote machine
- Verify firewall settings

**"Permission denied" (when deploying a key)**
- Verify username and password
- Check if the remote server allows password authentication

**Git Synchronization: "GitHub authentication failed"**
- The Personal Access Token needs `repo` scope

---

## 📞 Support

For issues or questions, please open an issue on GitHub:
https://github.com/usmanTheCoder/ssh-bootstrap

---

## 📄 License

This project is open source and available under the MIT License.

---

**Manage your SSH configuration with confidence. 🎉**
