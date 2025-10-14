# Quick Start Guide - SSH Bootstrap Tool

**Developed by M. Usman Sharif & M. Umair Khan**

---

## 🚀 For End Users

### Option 1: Use the Regular Version (Recommended)

1. **Download:** `SSH_Bootstrap_Tool.exe`
2. **Run:** Double-click the file
3. **If Windows asks:** Click "More info" → "Run anyway"

### Option 2: Use the Debug Version (If Regular Doesn't Work)

1. **Download:** `SSH_Bootstrap_Tool_Debug.exe`
2. **Run:** Double-click the file
3. **View:** Console window shows any errors

---

## 📋 Prerequisites

### What You Need:
- ✅ Windows 10 or Windows 11
- ✅ OpenSSH client (pre-installed on Win10/11)
- ✅ Network access to remote server
- ✅ Valid SSH server credentials

### Optional but Recommended:
- 📦 [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

---

## 🎯 How to Use

### Step 1: Launch the Application
- Double-click `SSH_Bootstrap_Tool.exe`

### Step 2: Enter Server Details
- **Server IP:** e.g., `192.168.1.100` or `10.0.0.50`
- **Username:** Your SSH username
- **Password:** Your SSH password (will be hidden)

### Step 3: Start Bootstrap
- Click "🚀 Start Bootstrap" button
- OR press **Enter** on keyboard

### Step 4: Wait for Completion
- Progress bar shows current stage
- Terminal shows colored output:
  - 🟢 Green = Success
  - 🔴 Red = Error
  - 🟡 Yellow = Warning
  - 🔵 Blue = Info

### Step 5: Test Connection
Once complete, connect without password:
```bash
ssh username@server-ip
```

---

## 💡 Tips

### Quick Tips:
- ✨ **Press Enter** in any field to start
- 👁️ **Click eye icon** to show/hide password
- 🔄 **IP validation** shows real-time feedback
- ⌨️ **Tab key** moves between fields

### What It Does:
1. **Generates SSH Key** (RSA 2048-bit)
2. **Connects to Server** (via SSH)
3. **Uploads Public Key** (to `~/.ssh/authorized_keys`)
4. **Tests Connection** (passwordless SSH)

### Result:
✅ You can now login without password!

---

## ⚠️ Troubleshooting

### "Windows protected your PC"
1. Click **"More info"**
2. Click **"Run anyway"**

### "App doesn't start"
1. Try **debug version:** `SSH_Bootstrap_Tool_Debug.exe`
2. Install [VC++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
3. Check antivirus settings

### "Connection failed"
1. Verify server IP is correct
2. Check username and password
3. Ensure SSH server is running
4. Check firewall settings

### "Permission denied"
1. Verify password is correct
2. Check server allows password authentication
3. Ensure SSH service is running

---

## 🔒 Security

### What's Safe:
- ✅ Password only sent over encrypted SSH
- ✅ Keys stored in `~/.ssh/` (standard location)
- ✅ Private key never leaves your computer
- ✅ Uses industry-standard RSA encryption

### What's Stored:
- 📁 Private Key: `~/.ssh/id_rsa` (on your computer)
- 📄 Public Key: `~/.ssh/id_rsa.pub` (on your computer)
- 🔑 Public Key: `~/.ssh/authorized_keys` (on remote server)

---

## 📁 Files Created

On **your computer:**
```
C:\Users\YourName\.ssh\
├── id_rsa          (Private key - keep secure!)
└── id_rsa.pub      (Public key - safe to share)
```

On **remote server:**
```
/home/username/.ssh/
└── authorized_keys (Contains your public key)
```

---

## 🎓 Example Usage

### Example 1: Home Server
```
IP:       192.168.1.100
Username: pi
Password: raspberry
```

### Example 2: Cloud Server
```
IP:       203.0.113.45
Username: ubuntu
Password: MySecurePass123
```

### Example 3: Local Network
```
IP:       10.0.0.50
Username: admin
Password: AdminPass456
```

---

## ❓ FAQ

**Q: Do I need Python installed?**  
A: No! The executable includes everything.

**Q: Will this work on Mac/Linux?**  
A: No, this executable is Windows only. Use the Python script for Mac/Linux.

**Q: Can I use custom SSH port?**  
A: Not in v1.0. Use standard port 22 for now.

**Q: What if I already have SSH keys?**  
A: Existing keys will be backed up automatically.

**Q: Is my password saved anywhere?**  
A: No! Password is only used during setup and never stored.

**Q: Can I use this for multiple servers?**  
A: Yes! Run the tool for each server.

---

## 📞 Need Help?

**Found a bug?** Report it:
- https://github.com/usmanTheCoder/ssh-bootstrap/issues

**Questions?** Check:
- `README.md` - Full documentation
- `TROUBLESHOOTING.md` - Common issues
- `INSTALLATION.md` - Installation guide

**Developers:**
- M. Usman Sharif
- M. Umair Khan

---

## ✅ After Setup

Once bootstrap is complete:

### Connect Without Password:
```bash
ssh username@server-ip
```

### Copy Files:
```bash
scp file.txt username@server-ip:/path/
```

### Run Remote Commands:
```bash
ssh username@server-ip "ls -la"
```

### Mount Remote Folder (Windows):
```bash
# Use SSHFS-Win or WinFsp
```

---

**Enjoy passwordless SSH! 🎉**

For detailed documentation, see: `README.md`
