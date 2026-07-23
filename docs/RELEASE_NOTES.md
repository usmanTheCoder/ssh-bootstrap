# Release Notes - SSH Configuration Manager

## Version 2.0.0 (July 17, 2026)

### 🔁 Complete Rewrite: SSH Bootstrap Tool → SSH Configuration Manager

The application evolved from a single-purpose "upload my key to one server"
tool into a full SSH configuration management app. New entry point: `main.py`
(the old `remote_ssh_gui.py` / `remote_ssh_bootstrap_ssh.py` remain in the
repo, superseded).

**New capabilities:**
- Dashboard with host/jump-host counts, sync status, and quick actions
- Full Server/VM CRUD (add, edit, duplicate, delete, search/filter)
- Jump Host (bastion) management with automatic `ProxyJump` generation and
  cascading updates to every dependent server
- SSH key generation is now optional - use an existing key, generate a new
  one, or skip it entirely per server
- `~/.ssh/config` is now a generated, validated artifact: a managed block is
  regenerated on every change, duplicate `Host` entries are impossible, and
  anything outside that block (or the whole file, if unmanaged) is preserved
- Import an existing SSH config (jump hosts inferred from `ProxyJump`),
  export a portable copy, or hand-edit the raw file in an advanced mode
  (validated before saving)
- Git-based backup/sync: connect a GitHub repo via Personal Access Token,
  push/pull your configuration, with conflict detection and resolution
- Modern CustomTkinter UI with light/dark mode and toast notifications

---

## Version 1.0.0 (October 14, 2025)

**Developed by M. Usman Sharif & M. Umair Khan**

### 🎉 Initial Release

This is the first official release of the SSH Bootstrap Tool, a beautiful GUI application that simplifies SSH key-based authentication setup.

---

### ✨ Features

#### User Interface
- **Modern Design** - Clean, professional interface with blue gradient theme
- **Real-time IP Validation** - Visual feedback with color-coded borders (red/yellow/green)
- **Password Visibility Toggle** - Eye icon button to show/hide password
- **Developer Credits** - Footer showing project developers
- **Centered Window** - Application always appears in the center of the screen
- **Responsive Layout** - Automatically expands to show progress and terminal

#### Functionality
- **Automatic SSH Key Generation** - Creates RSA 2048-bit key pairs
- **Secure Key Upload** - Uploads public key to remote server via SSH
- **Passwordless Testing** - Verifies SSH connection works without password
- **Progress Tracking** - 8-stage progress bar with status updates:
  - 0-25%: SSH key generation
  - 25-50%: Server connection
  - 50-75%: Key upload
  - 75-100%: Connection testing
- **Real-time Logging** - Color-coded terminal output (success/error/warning/info)
- **Cross-platform** - Works on Windows, Linux, and macOS

#### User Experience
- **Enter Key Support** - Press Enter in any field to start bootstrap
- **Input Validation** - Prevents invalid IP addresses and empty fields
- **Error Handling** - Clear error messages and validation dialogs
- **Non-blocking UI** - Multi-threaded operation keeps interface responsive

---

### 📦 What's Included

#### Standalone Executable
- **File:** `SSH_Bootstrap_Tool.exe`
- **Size:** ~9 MB
- **Platform:** Windows 64-bit
- **Dependencies:** All bundled (no Python installation needed)

#### Source Code
- **Main Application:** `remote_ssh_gui.py`
- **CLI Version:** `remote_ssh_bootstrap_ssh.py`
- **Build Script:** `build_executable.py`
- **Requirements:** `requirements.txt`

---

### 🔧 Technical Details

#### Dependencies
- Python 3.7+
- paramiko >= 3.0.0 (SSH protocol)
- cryptography >= 41.0.0 (Cryptographic operations)
- tkinter (GUI framework)

#### SSH Key Details
- **Algorithm:** RSA
- **Key Size:** 2048 bits
- **Storage Location:** `~/.ssh/`
- **Private Key:** `~/.ssh/id_rsa`
- **Public Key:** `~/.ssh/id_rsa.pub`

---

### 🎯 Usage

1. Launch `SSH_Bootstrap_Tool.exe`
2. Enter remote server IP (e.g., 192.168.1.100)
3. Enter username
4. Enter password
5. Click "Start Bootstrap" or press Enter
6. Wait for completion
7. Connect without password: `ssh username@ip`

---

### 🐛 Known Issues

None reported in this release.

---

### 🔜 Future Enhancements

Potential features for future releases:
- Custom SSH key algorithms (ED25519, ECDSA)
- Support for custom SSH ports
- Batch processing for multiple servers
- Configuration profiles
- Dark mode theme
- Custom icon for executable
- Linux/macOS executables

---

### 📝 Installation

**For End Users:**
- Simply download and run `SSH_Bootstrap_Tool.exe`
- No installation or Python required

**For Developers:**
```bash
git clone https://github.com/usmanTheCoder/ssh-bootstrap.git
cd ssh-bootstrap
pip install -r requirements.txt
python remote_ssh_gui.py
```

**Building Executable:**
```bash
python build_executable.py
```

---

### 🔒 Security

- Password is only transmitted over SSH (encrypted)
- Private keys remain on local machine
- Keys stored with proper Unix permissions (600)
- No password storage or logging
- Uses standard OpenSSH key format

---

### 📄 License

MIT License - See LICENSE file for details

---

### 🙏 Acknowledgments

- Built with Python and tkinter
- SSH functionality powered by Paramiko
- Executable created with PyInstaller

---

### 📞 Support

- **GitHub:** https://github.com/usmanTheCoder/ssh-bootstrap
- **Issues:** https://github.com/usmanTheCoder/ssh-bootstrap/issues
- **Developers:** M. Usman Sharif & M. Umair Khan

---

**Thank you for using SSH Bootstrap Tool! 🚀**
