"""SSH key generation and discovery, independent of any server config.

Refactored out of the original remote_ssh_gui.py's generate_ssh_key(), which
was hardcoded to a single id_rsa keypair - this version supports naming and
listing multiple keys.
"""
import platform
import re
import subprocess
from pathlib import Path
from typing import Optional

from sshmgr.models import SSHKey

SSH_DIR = Path.home() / ".ssh"
VALID_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class KeyError_(Exception):
    """Raised for invalid names or generation failures."""


def _find_ssh_keygen() -> str:
    if platform.system() == "Windows":
        candidates = [r"C:\Windows\System32\OpenSSH\ssh-keygen.exe", "ssh-keygen"]
    else:
        candidates = ["ssh-keygen"]
    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, "--help"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=2,
            )
            if result.returncode in (0, 1):
                return candidate
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    raise KeyError_("ssh-keygen not found. Please install OpenSSH.")


def validate_name(name: str, existing_names: Optional[set] = None) -> None:
    name = name.strip()
    if not name:
        raise KeyError_("Key name is required.")
    if not VALID_NAME_RE.match(name):
        raise KeyError_(
            "Key name may only contain letters, digits, hyphens and underscores."
        )
    if existing_names and name in existing_names:
        raise KeyError_(f"A key named '{name}' already exists.")


def list_keys() -> list[SSHKey]:
    """Scan ~/.ssh for matching private/public key pairs."""
    if not SSH_DIR.exists():
        return []
    keys = []
    for pub_path in sorted(SSH_DIR.glob("*.pub")):
        priv_path = pub_path.with_suffix("")
        if not priv_path.exists():
            continue
        key_type = "rsa"
        try:
            content = pub_path.read_text(encoding="utf-8").strip()
            first_token = content.split()[0] if content else ""
            if "ed25519" in first_token:
                key_type = "ed25519"
            elif "ecdsa" in first_token:
                key_type = "ecdsa"
            elif "rsa" in first_token:
                key_type = "rsa"
        except Exception:
            pass
        keys.append(
            SSHKey(
                name=priv_path.name,
                private_key_path=str(priv_path),
                public_key_path=str(pub_path),
                key_type=key_type,
            )
        )
    return keys


def generate(name: str, key_type: str = "rsa", bits: int = 2048) -> SSHKey:
    """Generate a new SSH key pair named `name` inside ~/.ssh."""
    existing = {k.name for k in list_keys()}
    validate_name(name, existing)

    SSH_DIR.mkdir(mode=0o700, exist_ok=True)
    private_key = SSH_DIR / name
    public_key = SSH_DIR / f"{name}.pub"

    ssh_keygen_cmd = _find_ssh_keygen()
    cmd = [ssh_keygen_cmd, "-t", key_type, "-f", str(private_key), "-N", ""]
    if key_type == "rsa":
        cmd[3:3] = ["-b", str(bits)]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise KeyError_(f"Failed to generate SSH key: {e.stderr.decode(errors='replace')}")

    if platform.system() in ("Linux", "Darwin"):
        private_key.chmod(0o600)
        public_key.chmod(0o644)

    return SSHKey(
        name=name,
        private_key_path=str(private_key),
        public_key_path=str(public_key),
        key_type=key_type,
    )
