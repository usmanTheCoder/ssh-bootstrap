# 🔐 SSH Key Bootstrap Tool

A beautiful, user-friendly GUI application to set up passwordless SSH authentication on remote servers.

**Developed by M. Usman Sharif & M. Umair Khan**

---

## ✨ Features

- 🎨 **Modern, Beautiful UI** - Clean and professional interface
- 🔒 **IP Validation** - Only accepts valid IP address formats
- 👁️ **Password Toggle** - Show/hide password visibility
- 📊 **Progress Tracking** - Real-time progress bar and color-coded logs
- ⚡ **Multi-threaded** - Non-blocking UI during operations
- 🔄 **Retry Mechanism** - Configurable retry attempts for connections
- ✅ **Automatic Testing** - Verifies passwordless SSH after setup

---

## 🚀 Quick Start

### Option 1: Run the Executable (Recommended)
Download the standalone executable from the [Releases](https://github.com/usmanTheCoder/ssh-bootstrap/releases) page or use the one in the `dist` folder:
```
dist\SSH_Bootstrap_Tool.exe
```
**No Python installation required!** Just download and run.

**File Size:** ~9 MB  
**Platform:** Windows 64-bit

### Option 2: Run from Source
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python remote_ssh_gui.py
```

---

## 📋 Requirements

### For Executable:
- Windows OS
- OpenSSH client (usually pre-installed on Windows 10/11)

### For Running from Source:
- Python 3.7+
- paramiko >= 3.0.0
- cryptography >= 41.0.0

---

## 🎯 How to Use

1. **Launch the application**
   - Run `SSH_Bootstrap_Tool.exe` or `python remote_ssh_gui.py`

2. **Enter server details:**
   - Remote Server IP (validated format)
   - Username
   - Password (with visibility toggle)
   - Max Retries (default: 3)

3. **Click "🚀 Start Bootstrap"**

4. **Monitor progress:**
   - Green = Success
   - Red = Error
   - Yellow = Warning
   - Blue = Info

5. **Done!** Connect without password:
   ```bash
   ssh username@ip_address
   ```

---

## 🛠️ Build Instructions

### Build the Executable Yourself

#### Method 1: Using Python Script
```bash
python build_executable.py
```

#### Method 2: Using Batch File
```bash
build.bat
```

#### Method 3: Manual PyInstaller
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name=SSH_Bootstrap_Tool --clean remote_ssh_gui.py
```

The executable will be created in the `dist` folder.

---

## 📁 Project Structure

```
remote_ssh/
├── remote_ssh_gui.py          # Main GUI application
├── remote_ssh_bootstrap_ssh.py # Original CLI version
├── build_executable.py         # Python build script
├── build.bat                   # Windows batch build script
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── dist/
│   └── SSH_Bootstrap_Tool.exe # Standalone executable
└── build/                      # Build artifacts (can be deleted)
```

---

## 🎨 UI Features

### Input Validation
- **IP Address**: Only accepts valid IP format (0-255 per octet)
- **Required Fields**: All fields must be filled

### Visual Feedback
- **Progress Bar**: Animated during operations
- **Color-coded Logs**:
  - 🟢 Success messages
  - 🔴 Error messages
  - 🟡 Warning messages
  - 🔵 Information messages

### User Controls
- 👁️ **Password Toggle**: Click eye icon to show/hide password
- 🚀 **Start Bootstrap**: Begin the SSH setup process
- 🗑️ **Clear Log**: Clear the output log

---

## 🔧 Technical Details

### What It Does:
1. **Generates SSH Key Pair** (if not exists)
   - Creates `~/.ssh/id_rsa` and `~/.ssh/id_rsa.pub`
   - 2048-bit RSA key

2. **Uploads Public Key**
   - Connects to remote server via SSH
   - Creates `.ssh` directory on remote
   - Adds public key to `authorized_keys`
   - Sets correct permissions (700 for .ssh, 600 for authorized_keys)

3. **Tests Connection**
   - Verifies passwordless SSH works
   - Provides connection command

### Dependencies:
- **Paramiko**: SSH protocol implementation
- **Cryptography**: Cryptographic operations
- **Tkinter**: GUI framework (built-in with Python)

---

## 🐛 Troubleshooting

### "PyInstaller not found"
```bash
pip install pyinstaller
```

### "Authentication failed"
- Verify username and password are correct
- Check if SSH is enabled on remote server
- Increase max retries

### "Connection timeout"
- Verify IP address is correct
- Check network connectivity
- Ensure port 22 is accessible

### "SSH key generation failed"
- Check if `ssh-keygen` is in system PATH
- Run as administrator if permission issues occur

---

## 📝 Notes

- The executable is **portable** - can be copied to any Windows machine
- SSH keys are stored in `C:\Users\<YourUsername>\.ssh\`
- Existing SSH keys are reused (not overwritten)
- The application requires OpenSSH client installed on Windows

---

## 🌟 Changelog

### Version 1.0
- Initial release
- Modern GUI with validation
- IP address format validation
- Password visibility toggle
- Multi-threaded operations
- Color-coded logging
- Progress tracking
- Standalone executable build

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

**Enjoy secure, passwordless SSH connections! 🚀**
