# SSH Bootstrap Tool - Installation Guide

**Developed by M. Usman Sharif & M. Umair Khan**

## 📦 Standalone Executable (Recommended)

### For End Users

The easiest way to use the SSH Bootstrap Tool is with the standalone executable:

1. **Download** `SSH_Bootstrap_Tool.exe` from the `dist` folder
2. **Run** the executable by double-clicking it
3. No Python installation required!

**File Location:** `dist\SSH_Bootstrap_Tool.exe`  
**File Size:** ~9 MB  
**Platform:** Windows 64-bit

### Features
- ✅ No dependencies to install
- ✅ Single executable file
- ✅ Ready to use immediately
- ✅ Can be distributed to any Windows machine

---

## 🔧 Building from Source

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

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

3. **Run the GUI:**
   ```bash
   python remote_ssh_gui.py
   ```

### Building Your Own Executable

To create a standalone executable:

```bash
python build_executable.py
```

The executable will be created in the `dist` folder.

---

## 🚀 Usage

1. **Launch** the application
2. **Enter** the remote server details:
   - Server IP address (e.g., 192.168.1.100)
   - Username
   - Password
3. **Click** "Start Bootstrap" or press **Enter**
4. **Wait** for the process to complete
5. **Connect** without password: `ssh username@ip`

---

## 📋 Requirements (for running from source)

- Python 3.7+
- paramiko >= 3.0.0
- cryptography >= 41.0.0

---

## 🔒 Security Notes

- The tool uses SSH key-based authentication (RSA 2048-bit)
- Private keys are stored in `~/.ssh/` directory
- Password is only used during initial setup
- After setup, passwordless SSH authentication is enabled

---

## 🐛 Troubleshooting

### Common Issues

**"ssh-keygen not found"**
- Install OpenSSH client on your system

**"Connection refused"**
- Check if SSH server is running on remote machine
- Verify firewall settings

**"Permission denied"**
- Verify username and password
- Check if remote server allows password authentication

---

## 📞 Support

For issues or questions, please open an issue on GitHub:
https://github.com/usmanTheCoder/ssh-bootstrap

---

## 📄 License

This project is open source and available under the MIT License.

---

**Enjoy passwordless SSH! 🎉**
