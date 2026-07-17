# Quick Start Guide - SSH Configuration Manager

**Developed by M. Usman Sharif & M. Umair Khan**

---

## 🚀 For End Users

### Option 1: Use the Regular Version (Recommended)

1. **Download:** `SSH_Configuration_Manager.exe`
2. **Run:** Double-click the file
3. **If Windows asks:** Click "More info" → "Run anyway"

### Option 2: Use the Debug Version (If Regular Doesn't Work)

1. **Download:** `SSH_Configuration_Manager_Debug.exe`
2. **Run:** Double-click the file
3. **View:** Console window shows any errors

---

## 📋 Prerequisites

### What You Need:
- ✅ Windows 10 or Windows 11
- ✅ OpenSSH client (pre-installed on Win10/11)
- ✅ Network access to any remote servers you add

### Optional but Recommended:
- 📦 [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- 🔗 Git, if you plan to use Git Synchronization

---

## 🎯 How to Use

### Step 1: Launch the Application
- Double-click `SSH_Configuration_Manager.exe`

### Step 2: Look at the Dashboard
- Configured host count, jump host count, and sync status at a glance
- Quick actions: Add Server/VM, Import Configuration, Synchronize, Open SSH Config

### Step 3: Add a Server
- Go to **Servers → + Add Server/VM**
- Fill in Host Alias, Hostname/IP, Username, Port
- Choose a key: **use an existing key**, **generate a new one**, or **skip** (if auth is handled another way)
- Optionally assign a **Jump Host**
- Optionally check **"Deploy key to this server now"** to push the key over password auth right away

### Step 4: (Optional) Set Up a Jump Host First
- Go to **Jump Hosts → + Add Jump Host** before adding servers that need one
- Any server can then select it from a dropdown - editing or deleting the jump host later updates every server that uses it automatically

### Step 5: Check the Generated Config
- Go to **SSH Configuration** to see exactly what was written to `~/.ssh/config`
- Import an existing config, export a copy, or (advanced) enable manual editing

### Step 6: (Optional) Connect Git Synchronization
- Go to **Git Synchronization**, paste a GitHub Personal Access Token, and connect/initialize a repository
- From then on, you'll be asked to push each change - or pull to restore your configuration on a new machine

### Step 7: Connect
```bash
ssh <alias-you-chose>
```

---

## 💡 Tips

- 🔍 Use the **search box** on the Servers screen to filter by alias or hostname
- 🌓 Toggle **dark/light mode** from the sidebar - it's remembered next launch
- 📋 **Duplicate** a server to quickly create a similar one with a new alias
- 🧭 A **Jump Host** only needs to be created once; reuse it across any number of servers

---

## ⚠️ Troubleshooting

### "Windows protected your PC"
1. Click **"More info"**
2. Click **"Run anyway"**

### "App doesn't start"
1. Try the **debug version:** `SSH_Configuration_Manager_Debug.exe` and read the console output
2. Install [VC++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
3. Check antivirus settings

### "Deploy key to server" fails
1. Verify the hostname/IP, username, and password are correct
2. Ensure the remote server has an SSH server running and accepts password auth
3. Check firewall settings and that the port is correct

### Git Synchronization issues
1. "Authentication failed" - your Personal Access Token needs `repo` scope
2. "Push rejected" - pull first (someone/something else changed the remote), resolve any conflict, then push again

---

## 🔒 Security

- Private keys are generated locally and never leave your computer
- The GitHub token is stored in your OS credential store (via `keyring`), never in plain text
- Manual "Deploy key" only sends the password over the encrypted SSH connection itself, and only for that one operation

---

## 📁 Files & Data

On **your computer:**
```
C:\Users\YourName\.ssh\
├── config                       (generated/managed SSH config)
├── config.bak                   (backup of the previous config)
├── <your-key-name>              (private key)
└── <your-key-name>.pub          (public key)

C:\Users\YourName\.ssh-bootstrap-manager\
├── data.json                    (the app's own server/jump-host/settings data)
└── git-repo\                    (local clone, if Git Synchronization is connected)
```

---

## ❓ FAQ

**Q: Do I need Python installed?**
A: No! The executable includes everything.

**Q: Is SSH key generation mandatory?**
A: No - when adding a server you can use an existing key, generate a new one, or skip it entirely.

**Q: Will this overwrite my existing SSH config?**
A: No - the app only manages a clearly marked block inside `~/.ssh/config`; anything else in that file is left alone.

**Q: Can I manage multiple servers and jump hosts?**
A: Yes - that's the whole point. Add as many as you need from the Servers and Jump Hosts screens.

**Q: Is my GitHub token saved anywhere readable?**
A: No - it's stored in your OS's secure credential store, not in a plain file.

---

## 📞 Need Help?

**Found a bug?** Report it:
- https://github.com/usmanTheCoder/ssh-bootstrap/issues

**Questions?** Check:
- `README.md` - Full documentation
- `INSTALLATION.md` - Installation guide

**Developers:**
- M. Usman Sharif
- M. Umair Khan

---

**Manage your SSH configuration with confidence. 🎉**

For detailed documentation, see: `README.md`
