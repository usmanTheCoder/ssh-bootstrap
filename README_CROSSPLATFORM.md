# 🔐 SSH Key Bootstrap Tool

A beautiful, cross-platform GUI application to set up passwordless SSH authentication on remote servers.

**Developed by M. Usman Sharif & M. Umair Khan**

---

## 🌍 Cross-Platform Support

✅ **Windows** (10/11)  
✅ **Linux** (Ubuntu, Debian, Fedora, Arch, etc.)  
✅ **macOS** (10.14+)

---

## ✨ Features

- 🎨 **Modern, Beautiful UI** - Clean and professional interface
- 🌍 **Cross-Platform** - Works on Windows, Linux, and macOS
- 🔒 **IP Validation** - Only accepts valid IP address formats
- 👁️ **Password Toggle** - Show/hide password visibility
- 📊 **Progress Tracking** - Real-time progress bar and color-coded logs
- ⚡ **Multi-threaded** - Non-blocking UI during operations
- 🔄 **Retry Mechanism** - Configurable retry attempts for connections
- ✅ **Automatic Testing** - Verifies passwordless SSH after setup
- 🎨 **Platform-Adaptive UI** - Uses native fonts for each OS

---

## 🚀 Quick Start

### Option 1: Run the Executable (Recommended)

#### Windows:
```
dist\SSH_Bootstrap_Tool.exe
```

#### Linux/macOS:
```bash
chmod +x dist/SSH_Bootstrap_Tool
./dist/SSH_Bootstrap_Tool
```

### Option 2: Run from Source
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python remote_ssh_gui.py
# or on Linux/macOS
python3 remote_ssh_gui.py
```

---

## 📋 Requirements

### For Executable:
- **Windows**: OpenSSH client (pre-installed on Windows 10/11)
- **Linux**: openssh-client (usually pre-installed)
- **macOS**: OpenSSH (pre-installed)

### For Running from Source:
- Python 3.7+
- paramiko >= 3.0.0
- cryptography >= 41.0.0
- tkinter (usually included with Python)

---

## 🎯 How to Use

1. **Launch the application**

2. **Enter server details:**
   - Remote Server IP (validated format)
   - Username
   - Password (with visibility toggle)
   - Max Retries (default: 3)

3. **Click "🚀 Start Bootstrap"**

4. **Monitor progress:**
   - 🟢 Green = Success
   - 🔴 Red = Error
   - 🟡 Yellow = Warning
   - 🔵 Blue = Info

5. **Done!** Connect without password:
   ```bash
   ssh username@ip_address
   ```

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
# Install PyInstaller
pip install pyinstaller

# Windows
pyinstaller --onefile --windowed --name=SSH_Bootstrap_Tool --clean remote_ssh_gui.py

# Linux/macOS
pyinstaller --onefile --windowed --name=SSH_Bootstrap_Tool --clean remote_ssh_gui.py
chmod +x dist/SSH_Bootstrap_Tool
```

The executable will be created in the `dist` folder.

---

## 📁 Project Structure

```
remote_ssh/
├── remote_ssh_gui.py          # Main GUI application (cross-platform)
├── remote_ssh_bootstrap_ssh.py # Original CLI version
├── build_crossplatform.py     # Cross-platform build script
├── build_executable.py         # Python build script (legacy)
├── build.bat                   # Windows batch build script
├── build.sh                    # Linux/macOS shell build script
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── dist/
│   └── SSH_Bootstrap_Tool[.exe] # Standalone executable
└── build/                      # Build artifacts (can be deleted)
```

---

## 🎨 Platform-Specific Features

### Windows
- Uses **Segoe UI** font
- Uses **Consolas** for monospace
- Detects OpenSSH in System32

### Linux
- Uses **Ubuntu** font (or system default)
- Uses **Monospace** for terminal
- Standard SSH paths

### macOS
- Uses **SF Pro Display** font
- Uses **Monaco** for monospace
- Native macOS look and feel

---

## 🔧 Technical Details

### What It Does:
1. **Generates SSH Key Pair** (if not exists)
   - Creates `~/.ssh/id_rsa` and `~/.ssh/id_rsa.pub`
   - 2048-bit RSA key
   - Proper permissions on Unix systems (600/644)

2. **Uploads Public Key**
   - Connects to remote server via SSH
   - Creates `.ssh` directory on remote
   - Adds public key to `authorized_keys`
   - Sets correct permissions (700 for .ssh, 600 for authorized_keys)

3. **Tests Connection**
   - Verifies passwordless SSH works
   - Provides connection command

### Dependencies:
- **Paramiko**: SSH protocol implementation (Python)
- **Cryptography**: Cryptographic operations
- **Tkinter**: GUI framework (built-in with Python)
- **Platform**: OS detection and compatibility

---

## 🐛 Troubleshooting

### All Platforms

#### "Authentication failed"
- Verify username and password are correct
- Check if SSH is enabled on remote server
- Increase max retries

#### "Connection timeout"
- Verify IP address is correct
- Check network connectivity
- Ensure port 22 is accessible

### Windows Specific

#### "ssh-keygen not found"
```powershell
# Check if OpenSSH is installed
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH*'

# Install if missing
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

### Linux Specific

#### "ssh-keygen not found"
```bash
# Ubuntu/Debian
sudo apt-get install openssh-client

# Fedora/RHEL
sudo dnf install openssh-clients

# Arch
sudo pacman -S openssh
```

### macOS Specific

#### "Permission denied"
- macOS has OpenSSH pre-installed
- Check System Preferences > Security & Privacy
- Allow terminal/app to access network

---

## 📝 Installation Notes

### Linux
After building, you may need to install additional dependencies:

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

## 🌟 Changelog

### Version 1.1 - Cross-Platform
- ✅ Cross-platform support (Windows, Linux, macOS)
- ✅ Platform-adaptive fonts
- ✅ Smart SSH tool detection
- ✅ Proper file permissions on Unix systems
- ✅ Cross-platform build scripts

### Version 1.0
- Initial release (Windows only)
- Modern GUI with validation
- IP address format validation
- Password visibility toggle
- Multi-threaded operations
- Color-coded logging
- Progress tracking

---

## 👨‍💻 Developers

**M. Usman Sharif & M. Umair Khan**

---

## 📄 License

This project is provided as-is for personal and educational use.

---

## 🤝 Contributing

Feel free to fork, modify, and enhance this tool!

---

**Enjoy secure, passwordless SSH connections on any platform! 🚀**
