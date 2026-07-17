"""Deploy a public key to a remote server over password auth and verify
passwordless login - refactored out of the original remote_ssh_gui.py's
upload_ssh_key()/test_ssh_connection(), which were hardcoded to id_rsa and
tightly coupled to the old single-screen GUI. Used from the Add Server
wizard as an optional step, not a mandatory one.
"""
import platform
import socket
import subprocess
from pathlib import Path
from typing import Callable, Optional

import paramiko
from paramiko.ssh_exception import AuthenticationException

ProgressFn = Callable[[str, str], None]  # (message, level) -> None where level in info/success/warning/error


def _noop(message: str, level: str = "info") -> None:
    pass


def deploy_key(
    hostname: str,
    username: str,
    password: str,
    public_key_path: str,
    port: int = 22,
    timeout: int = 10,
    on_progress: ProgressFn = _noop,
) -> bool:
    """Connect with password auth and append the public key to
    ~/.ssh/authorized_keys on the remote host."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    on_progress(f"Connecting to {hostname}:{port} as {username}...", "info")
    try:
        client.connect(hostname, port=port, username=username, password=password, timeout=timeout)
    except AuthenticationException:
        on_progress("Authentication failed: incorrect username or password.", "error")
        return False
    except socket.timeout as e:
        on_progress(f"Connection timeout: {e}", "error")
        return False
    except Exception as e:
        on_progress(f"Connection error: {e}", "error")
        return False

    on_progress("Connected. Uploading public key...", "info")
    public_key_text = Path(public_key_path).read_text(encoding="utf-8").strip()
    commands = [
        "mkdir -p ~/.ssh && chmod 700 ~/.ssh",
        f"echo '{public_key_text}' >> ~/.ssh/authorized_keys",
        "chmod 600 ~/.ssh/authorized_keys",
    ]
    try:
        for cmd in commands:
            _, _, stderr = client.exec_command(cmd)
            err = stderr.read().decode()
            if err:
                on_progress(f"Error running remote command: {err}", "warning")
                return False
    finally:
        client.close()

    on_progress("Public key deployed successfully.", "success")
    return True


def _find_ssh_client() -> str:
    if platform.system() == "Windows":
        candidates = [r"C:\Windows\System32\OpenSSH\ssh.exe", "ssh"]
    else:
        candidates = ["ssh"]
    for candidate in candidates:
        try:
            subprocess.run(
                [candidate, "-V"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=2
            )
            return candidate
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return "ssh"


def test_passwordless(
    hostname: str,
    username: str,
    port: int = 22,
    identity_file: Optional[str] = None,
    on_progress: ProgressFn = _noop,
) -> bool:
    """Verify that key-based (no password prompt) SSH login works."""
    on_progress("Testing passwordless SSH connection...", "info")
    ssh_cmd = _find_ssh_client()
    cmd = [
        ssh_cmd,
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=5",
        "-p", str(port),
    ]
    if identity_file:
        cmd += ["-i", identity_file]
    cmd += [f"{username}@{hostname}", "echo ok"]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
    except subprocess.TimeoutExpired:
        on_progress("Passwordless SSH test timed out.", "error")
        return False

    if result.returncode == 0:
        on_progress("Passwordless SSH works.", "success")
        return True

    on_progress("Passwordless SSH failed or prompted for a password.", "error")
    return False
