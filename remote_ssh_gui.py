import os
import sys
import subprocess
import paramiko
import socket
import threading
import platform
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path
from paramiko.ssh_exception import AuthenticationException, SSHException, NoValidConnectionsError
import re
import time


class SSHBootstrapGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SSH Key Bootstrap Tool")
        self.root.geometry("700x450")
        self.root.resizable(True, True)
        self.root.minsize(700, 450)
        
        # Center the window on screen
        self.center_window(700, 450)
        
        # Detect operating system
        self.os_type = platform.system()  # 'Windows', 'Linux', 'Darwin' (macOS)
        
        # Set font based on OS
        if self.os_type == "Darwin":  # macOS
            self.main_font = "SF Pro Display"
            self.mono_font = "Monaco"
        elif self.os_type == "Linux":
            self.main_font = "Ubuntu"
            self.mono_font = "Monospace"
        else:  # Windows
            self.main_font = "Segoe UI"
            self.mono_font = "Consolas"
        
        # Color scheme - More modern gradient colors
        self.bg_color = "#f8fafc"
        self.primary_color = "#3b82f6"
        self.primary_dark = "#2563eb"
        self.success_color = "#10b981"
        self.error_color = "#ef4444"
        self.warning_color = "#f59e0b"
        self.text_color = "#1e293b"
        self.card_bg = "#ffffff"
        self.accent_color = "#8b5cf6"
        
        self.root.configure(bg=self.bg_color)
        
        # Password visibility state
        self.password_visible = False
        
        # Progress tracking
        self.current_step = 0
        self.total_steps = 4
        
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title_frame = tk.Frame(self.root, bg=self.primary_color, height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🔐 SSH Key Bootstrap Tool",
            font=(self.main_font, 20, "bold"),
            bg=self.primary_color,
            fg="white"
        )
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(
            title_frame,
            text="Securely set up passwordless SSH authentication",
            font=(self.main_font, 10),
            bg=self.primary_color,
            fg="#e0e7ff"
        )
        subtitle_label.pack()
        
        # Developer credit footer (place after title, before content)
        footer_frame = tk.Frame(self.root, bg="#1f2937", height=35)
        footer_frame.pack(fill=tk.X)
        footer_frame.pack_propagate(False)
        
        credit_label = tk.Label(
            footer_frame,
            text="Developed by M. Usman Sharif & M. Umair Khan",
            font=(self.main_font, 9),
            bg="#1f2937",
            fg="#9ca3af"
        )
        credit_label.pack(pady=8)
        
        # Main container using pack for better control
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Input section (always visible at top)
        input_frame = tk.Frame(main_container, bg=self.bg_color)
        input_frame.pack(fill=tk.X, side=tk.TOP)
        
        # Server Details Section
        details_label = tk.Label(
            input_frame,
            text="Server Details",
            font=(self.main_font, 12, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        details_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # IP Address
        tk.Label(
            input_frame,
            text="Remote Server IP:",
            font=(self.main_font, 10),
            bg=self.bg_color,
            fg=self.text_color
        ).grid(row=1, column=0, sticky="w", pady=8)
        
        # Create a validation command for IP address
        vcmd_ip = (self.root.register(self.validate_ip_input), '%P')
        
        self.ip_entry = tk.Entry(
            input_frame,
            font=(self.main_font, 10),
            width=35,
            relief=tk.FLAT,
            bg="white",
            fg=self.text_color,
            insertbackground=self.text_color,
            validate='key',
            validatecommand=vcmd_ip
        )
        self.ip_entry.grid(row=1, column=1, sticky="ew", pady=8, padx=(10, 0))
        self.add_entry_border(self.ip_entry)
        self.ip_entry.bind('<KeyRelease>', self.check_ip_format)
        self.ip_entry.bind('<FocusOut>', self.validate_complete_ip)
        self.ip_entry.bind('<Return>', lambda e: self.start_bootstrap())
        
        # IP validation feedback label
        self.ip_validation_label = tk.Label(
            input_frame,
            text="",
            font=(self.main_font, 9),
            bg=self.bg_color,
            fg=self.error_color
        )
        self.ip_validation_label.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=(0, 5))
        
        # Username
        tk.Label(
            input_frame,
            text="Username:",
            font=(self.main_font, 10),
            bg=self.bg_color,
            fg=self.text_color
        ).grid(row=3, column=0, sticky="w", pady=8)
        
        self.username_entry = tk.Entry(
            input_frame,
            font=(self.main_font, 10),
            width=35,
            relief=tk.FLAT,
            bg="white",
            fg=self.text_color,
            insertbackground=self.text_color
        )
        self.username_entry.grid(row=3, column=1, sticky="ew", pady=8, padx=(10, 0))
        self.add_entry_border(self.username_entry)
        self.username_entry.bind('<Return>', lambda e: self.start_bootstrap())
        
        # Password
        tk.Label(
            input_frame,
            text="Password:",
            font=(self.main_font, 10),
            bg=self.bg_color,
            fg=self.text_color
        ).grid(row=4, column=0, sticky="w", pady=8)
        
        # Password frame to hold entry and toggle button
        password_frame = tk.Frame(input_frame, bg=self.bg_color)
        password_frame.grid(row=4, column=1, sticky="ew", pady=8, padx=(10, 0))
        
        self.password_entry = tk.Entry(
            password_frame,
            font=(self.main_font, 10),
            show="●",
            relief=tk.FLAT,
            bg="white",
            fg=self.text_color,
            insertbackground=self.text_color
        )
        self.password_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.add_entry_border(self.password_entry)
        self.password_entry.bind('<Return>', lambda e: self.start_bootstrap())
        
        # Toggle password visibility button
        self.toggle_password_btn = tk.Button(
            password_frame,
            text="👁️",
            font=(self.main_font, 10),
            bg="white",
            fg=self.text_color,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_password_visibility,
            width=3,
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            highlightcolor=self.primary_color
        )
        self.toggle_password_btn.pack(side=tk.LEFT, padx=(5, 0))
        self.add_button_hover(self.toggle_password_btn, "white", "#f1f5f9")
        
        input_frame.columnconfigure(1, weight=1)
        
        # Progress container (hidden initially, will be shown at bottom)
        self.progress_container = tk.Frame(main_container, bg=self.bg_color)
        # Don't pack it yet - will show when needed
        
        # Progress Section (hidden initially)
        self.progress_label = tk.Label(
            self.progress_container,
            text="Progress",
            font=(self.main_font, 12, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        # Don't grid it yet - will show when needed
        
        # Progress status label
        self.progress_status = tk.Label(
            self.progress_container,
            text="Starting...",
            font=(self.main_font, 10),
            bg=self.bg_color,
            fg=self.text_color
        )
        # Don't pack it yet - will show when needed
        
        # Progress bar (determinate mode)
        self.progress = ttk.Progressbar(
            self.progress_container,
            mode='determinate',
            length=600,
            maximum=100
        )
        # Don't pack it yet - will show when needed
        self.progress['value'] = 0
        
        # Log output (hidden initially)
        self.log_frame = tk.Frame(self.progress_container, bg="white", relief=tk.FLAT)
        # Don't pack it yet - will show when needed
        
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            height=12,
            font=(self.mono_font, 9),
            bg="#1e293b",
            fg="#e2e8f0",
            insertbackground="white",
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colored output
        self.log_text.tag_config("success", foreground="#10b981")
        self.log_text.tag_config("error", foreground="#ef4444")
        self.log_text.tag_config("warning", foreground="#f59e0b")
        self.log_text.tag_config("info", foreground="#3b82f6")
        
        # Button section (always visible, between input and progress)
        button_frame = tk.Frame(main_container, bg=self.bg_color)
        button_frame.pack(fill=tk.X, side=tk.TOP, pady=(20, 0))
        
        self.start_button = tk.Button(
            button_frame,
            text="🚀 Start Bootstrap",
            font=(self.main_font, 11, "bold"),
            bg=self.primary_color,
            fg="white",
            relief=tk.FLAT,
            padx=30,
            pady=12,
            cursor="hand2",
            command=self.start_bootstrap
        )
        self.start_button.pack(padx=5)
        self.add_button_hover(self.start_button, self.primary_color, "#1d4ed8")
        
        # Store references
        self.main_container = main_container
        self.input_frame = input_frame
        
        # Flag to track if progress section is shown
        self.progress_shown = False
    
    def center_window(self, width, height):
        """Center the window on the screen"""
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Set window position
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def add_entry_border(self, entry):
        """Add a subtle border effect to entry widgets"""
        entry.config(highlightthickness=1, highlightbackground="#cbd5e1", highlightcolor=self.primary_color)
        
    def add_button_hover(self, button, normal_color, hover_color):
        """Add hover effect to buttons"""
        button.bind("<Enter>", lambda e: button.config(bg=hover_color))
        button.bind("<Leave>", lambda e: button.config(bg=normal_color))
    
    def validate_ip_input(self, value):
        """Validate IP address input - only allow numbers, dots, and valid IP characters"""
        if value == "":
            return True
        
        # Allow only digits and dots
        if not all(c.isdigit() or c == '.' for c in value):
            return False
        
        # Don't allow more than 3 dots
        if value.count('.') > 3:
            return False
        
        # Don't allow consecutive dots
        if '..' in value:
            return False
        
        # Check each segment
        segments = value.split('.')
        for segment in segments:
            if segment == '':
                continue
            # Don't allow segments with more than 3 digits
            if len(segment) > 3:
                return False
            # Don't allow leading zeros (except for '0' itself)
            if len(segment) > 1 and segment[0] == '0':
                return False
            # Don't allow values > 255
            if int(segment) > 255:
                return False
        
        return True
    
    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.password_visible:
            self.password_entry.config(show="●")
            self.toggle_password_btn.config(text="👁️")
            self.password_visible = False
        else:
            self.password_entry.config(show="")
            self.toggle_password_btn.config(text="🙈")
            self.password_visible = True
    
    def check_ip_format(self, event=None):
        """Check IP format as user types and show feedback"""
        ip = self.ip_entry.get().strip()
        
        if not ip:
            self.ip_validation_label.config(text="", fg=self.error_color)
            self.ip_entry.config(highlightbackground="#cbd5e1")
            return
        
        # Check if it looks incomplete
        segments = ip.split('.')
        
        # If we have less than 4 segments, it's incomplete
        if len(segments) < 4:
            self.ip_validation_label.config(
                text="⚠️ IP address incomplete (format: xxx.xxx.xxx.xxx)",
                fg=self.warning_color
            )
            self.ip_entry.config(highlightbackground=self.warning_color)
            return
        
        # Check if all segments are filled
        if any(seg == '' for seg in segments):
            self.ip_validation_label.config(
                text="⚠️ IP address incomplete",
                fg=self.warning_color
            )
            self.ip_entry.config(highlightbackground=self.warning_color)
            return
        
        # If we have 4 segments and all are valid, it's good
        if len(segments) == 4:
            try:
                if all(0 <= int(seg) <= 255 for seg in segments if seg):
                    self.ip_validation_label.config(
                        text="✓ Valid IP format",
                        fg=self.success_color
                    )
                    self.ip_entry.config(highlightbackground=self.success_color)
                    return
            except ValueError:
                pass
        
        # Otherwise show error
        self.ip_validation_label.config(
            text="✗ Invalid IP format",
            fg=self.error_color
        )
        self.ip_entry.config(highlightbackground=self.error_color)
    
    def validate_complete_ip(self, event=None):
        """Validate complete IP address when user leaves the field"""
        ip = self.ip_entry.get().strip()
        
        if not ip:
            return
        
        segments = ip.split('.')
        
        # Must have exactly 4 segments
        if len(segments) != 4:
            self.ip_validation_label.config(
                text="✗ IP must have 4 parts (e.g., 192.168.1.1)",
                fg=self.error_color
            )
            self.ip_entry.config(highlightbackground=self.error_color)
            messagebox.showwarning(
                "Invalid IP Format",
                f"IP address must have 4 parts separated by dots.\n\nExample: 192.168.1.1\n\nYou entered: {ip}"
            )
            return False
        
        # Check if all segments are valid numbers
        try:
            for i, seg in enumerate(segments, 1):
                if not seg:
                    self.ip_validation_label.config(
                        text=f"✗ Part {i} is empty",
                        fg=self.error_color
                    )
                    self.ip_entry.config(highlightbackground=self.error_color)
                    messagebox.showwarning(
                        "Invalid IP Format",
                        f"Part {i} of the IP address is empty.\n\nPlease enter a complete IP address."
                    )
                    return False
                
                num = int(seg)
                if not (0 <= num <= 255):
                    self.ip_validation_label.config(
                        text=f"✗ Part {i} must be 0-255 (you entered: {num})",
                        fg=self.error_color
                    )
                    self.ip_entry.config(highlightbackground=self.error_color)
                    messagebox.showwarning(
                        "Invalid IP Format",
                        f"Part {i} of the IP address must be between 0 and 255.\n\nYou entered: {num}"
                    )
                    return False
        except ValueError:
            self.ip_validation_label.config(
                text="✗ IP address contains invalid characters",
                fg=self.error_color
            )
            self.ip_entry.config(highlightbackground=self.error_color)
            messagebox.showwarning(
                "Invalid IP Format",
                "IP address must only contain numbers and dots."
            )
            return False
        
        # If we got here, it's valid
        self.ip_validation_label.config(
            text="✓ Valid IP address",
            fg=self.success_color
        )
        self.ip_entry.config(highlightbackground=self.success_color)
        return True
    
    def show_progress_section(self):
        """Show the progress section when starting bootstrap"""
        if not self.progress_shown:
            # Pack the progress container at the bottom
            self.progress_container.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM, pady=(20, 0))
            
            # Show progress label
            self.progress_label.pack(anchor="w", pady=(0, 10))
            
            # Show progress status
            self.progress_status.pack(anchor="w", pady=(0, 5))
            
            # Show progress bar
            self.progress.pack(fill=tk.X, pady=(0, 10))
            
            # Show log frame
            self.log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
            
            # Resize and center window to accommodate progress section
            self.center_window(700, 750)
            
            self.progress_shown = True
            self.root.update_idletasks()
        
    def log(self, message, tag="info"):
        """Add a log message with color coding"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def update_progress(self, value, status_text):
        """Update progress bar and status text"""
        self.progress['value'] = value
        self.progress_status.config(text=status_text)
        self.root.update_idletasks()
        
    def clear_log(self):
        """Clear the log output"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def start_bootstrap(self):
        """Start the SSH bootstrap process"""
        ip = self.ip_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not ip or not username or not password:
            messagebox.showerror("Input Error", "Please fill in all fields!")
            return
        
        # Validate IP format before starting
        if not self.validate_complete_ip():
            return
        
        max_retries = 3  # Default value
        
        # Show progress section
        self.show_progress_section()
        
        # Disable the start button and reset progress
        self.start_button.config(state=tk.DISABLED)
        self.clear_log()
        self.update_progress(0, "Starting...")
        
        # Run in a separate thread to avoid blocking the UI
        thread = threading.Thread(
            target=self.run_bootstrap,
            args=(ip, username, password, max_retries),
            daemon=True
        )
        thread.start()
        
    def run_bootstrap(self, ip, username, password, max_retries):
        """Run the SSH bootstrap process"""
        try:
            # Step 1: Generate SSH key (25% progress)
            self.update_progress(10, "Checking SSH keys...")
            public_key_path = self.generate_ssh_key()
            self.update_progress(25, "SSH key ready")
            
            # Step 2: Upload SSH key (25% to 75% progress)
            self.update_progress(30, "Connecting to server...")
            success = self.upload_ssh_key(ip, username, password, public_key_path, max_retries)
            
            # Step 3: Test SSH connection (75% to 100% progress)
            if success:
                self.update_progress(80, "Testing connection...")
                self.test_ssh_connection(ip, username)
            else:
                self.update_progress(100, "Failed")
            
        except Exception as e:
            self.log(f"[✖] Unexpected error: {str(e)}", "error")
            self.update_progress(100, "Error occurred")
        finally:
            self.start_button.config(state=tk.NORMAL)
            
    def generate_ssh_key(self):
        """Generate SSH key pair"""
        ssh_dir = Path.home() / ".ssh"
        private_key = ssh_dir / "id_rsa"
        public_key = ssh_dir / "id_rsa.pub"
        
        if private_key.exists() and public_key.exists():
            self.log("[✔] SSH key already exists.", "success")
            return public_key
        
        self.log("[+] Generating SSH key...", "info")
        ssh_dir.mkdir(mode=0o700, exist_ok=True)
        
        try:
            # Use ssh-keygen command (available on all platforms)
            ssh_keygen_cmd = "ssh-keygen"
            
            # On Windows, check if ssh-keygen is in PATH
            if self.os_type == "Windows":
                # Try to find ssh-keygen in common Windows locations
                ssh_paths = [
                    r"C:\Windows\System32\OpenSSH\ssh-keygen.exe",
                    "ssh-keygen"  # Try PATH
                ]
                
                ssh_keygen_cmd = None
                for path in ssh_paths:
                    try:
                        result = subprocess.run(
                            [path, "--help"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            timeout=2
                        )
                        if result.returncode in [0, 1]:  # ssh-keygen returns 1 for help
                            ssh_keygen_cmd = path
                            break
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        continue
                
                if not ssh_keygen_cmd:
                    self.log("[✖] ssh-keygen not found. Please install OpenSSH.", "error")
                    raise Exception("ssh-keygen not found")
            
            subprocess.run(
                [ssh_keygen_cmd, "-t", "rsa", "-b", "2048", "-f", str(private_key), "-N", ""],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Set proper permissions on Unix-like systems
            if self.os_type in ["Linux", "Darwin"]:
                os.chmod(private_key, 0o600)
                os.chmod(public_key, 0o644)
            
            self.log("[✔] SSH key generated successfully.", "success")
            return public_key
        except subprocess.CalledProcessError as e:
            self.log(f"[✖] Failed to generate SSH key: {e}", "error")
            raise
            
    def upload_ssh_key(self, ip, username, password, public_key_path, max_retries):
        """Upload SSH public key to remote server"""
        ssh_dir = ".ssh"
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        for attempt in range(1, max_retries + 1):
            self.update_progress(30 + (attempt * 5), f"Connecting... (Attempt {attempt}/{max_retries})")
            self.log(f"[+] Connecting to {ip} as {username} (Attempt {attempt}/{max_retries})...", "info")
            
            try:
                client.connect(ip, username=username, password=password, timeout=10)
                self.log("[✔] Connected successfully!", "success")
                self.update_progress(50, "Connected to server")
                break
            except AuthenticationException:
                self.log("[✖] Authentication failed: incorrect username or password.", "error")
                self.update_progress(100, "Authentication failed")
                if attempt >= max_retries:
                    self.log("[✖] Max authentication attempts exceeded.", "error")
                    return False
                return False
            except socket.timeout as e:
                self.log(f"[✖] Connection timeout: {e}", "error")
                self.update_progress(100, "Connection timeout")
                return False
            except Exception as e:
                self.log(f"[✖] Connection error: {e}", "error")
                self.update_progress(100, "Connection error")
                return False
        
        # Upload the public key
        self.update_progress(60, "Uploading public key...")
        self.log("[+] Uploading public key...", "info")
        
        commands = [
            f"mkdir -p ~/{ssh_dir} && chmod 700 ~/{ssh_dir}",
            f"echo '{Path(public_key_path).read_text().strip()}' >> ~/{ssh_dir}/authorized_keys",
            f"chmod 600 ~/{ssh_dir}/authorized_keys"
        ]
        
        for cmd in commands:
            try:
                stdin, stdout, stderr = client.exec_command(cmd)
                err = stderr.read().decode()
                if err:
                    self.log(f"[!] Error running command: {err}", "warning")
                    client.close()
                    return False
            except Exception as e:
                self.log(f"[✖] Command execution failed: {e}", "error")
                client.close()
                return False
        
        self.update_progress(75, "Public key uploaded")
        self.log("[✔] Public key added successfully!", "success")
        client.close()
        return True
        
    def test_ssh_connection(self, ip, username):
        """Test passwordless SSH connection"""
        self.update_progress(85, "Testing passwordless SSH...")
        self.log("[+] Testing passwordless SSH connection...", "info")
        
        try:
            # Find ssh command based on platform
            ssh_cmd = "ssh"
            if self.os_type == "Windows":
                # Try to find ssh in common Windows locations
                ssh_paths = [
                    r"C:\Windows\System32\OpenSSH\ssh.exe",
                    "ssh"  # Try PATH
                ]
                
                for path in ssh_paths:
                    try:
                        result = subprocess.run(
                            [path, "-V"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            timeout=2
                        )
                        ssh_cmd = path
                        break
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        continue
            
            result = subprocess.run(
                [
                    ssh_cmd,
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "BatchMode=yes",
                    "-o", "ConnectTimeout=5",
                    f"{username}@{ip}",
                    "echo 'Connected via SSH without password.'"
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                self.update_progress(100, "✓ Completed successfully!")
                self.log("[✔] Passwordless SSH works perfectly!", "success")
                self.log(f"[✔] You can now connect using: ssh {username}@{ip}", "success")
                messagebox.showinfo("Success", "SSH bootstrap completed successfully!\nYou can now connect without a password.")
            else:
                self.update_progress(100, "Test failed")
                self.log("[✖] Passwordless SSH test failed.", "error")
                
        except subprocess.CalledProcessError as e:
            self.update_progress(100, "Test failed")
            self.log("[✖] Passwordless SSH failed or prompted for password.", "error")
            self.log(f"[!] Error details: {e.stderr if e.stderr else 'Unknown error'}", "warning")


def main():
    root = tk.Tk()
    app = SSHBootstrapGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()
