"""The SSH config engine: ~/.ssh/config is a generated artifact owned by
this module. It only ever rewrites a marked "managed block" inside the
file, so any content a user (or another tool) already has in their config
is preserved untouched.
"""
import io
import os
import re
import tempfile
from pathlib import Path
from typing import Optional

import paramiko

from sshmgr.models import Server, JumpHost, SSHKey
from sshmgr.store import AppStore

MARK_START = "# >>> ssh-bootstrap-manager managed block >>>"
MARK_END = "# <<< ssh-bootstrap-manager managed block <<<"

_HANDLED_OPTIONS = {"hostname", "user", "port", "identityfile", "proxyjump"}


class SSHConfigError(Exception):
    """Raised when the generated config fails validation and cannot be saved."""


def default_config_path() -> Path:
    # Path.home() / ".ssh" / "config" resolves correctly on Windows, Linux
    # and macOS alike, so this is already cross-platform.
    return Path.home() / ".ssh" / "config"


def _render_host_block(
    alias: str,
    hostname: str,
    username: str,
    port: int,
    identity_file: Optional[str] = None,
    proxy_jump: Optional[str] = None,
    extra_options: str = "",
) -> str:
    lines = [f"Host {alias}"]
    lines.append(f"    HostName {hostname}")
    if username:
        lines.append(f"    User {username}")
    lines.append(f"    Port {port}")
    if identity_file:
        lines.append(f"    IdentityFile {identity_file}")
    if proxy_jump:
        lines.append(f"    ProxyJump {proxy_jump}")
    for opt_line in extra_options.splitlines():
        opt_line = opt_line.strip()
        if opt_line:
            lines.append(f"    {opt_line}")
    return "\n".join(lines)


def generate_block(store: AppStore) -> str:
    """Build the raw managed-block body (no markers) from the app store."""
    blocks = []
    for jh in store.list_jump_hosts():
        key = store.keys.get(jh.key_name) if jh.key_name else None
        blocks.append(
            _render_host_block(
                jh.name,
                jh.hostname,
                jh.username,
                jh.port,
                key.private_key_path if key else None,
                None,
                jh.extra_options,
            )
        )
    for s in store.list_servers():
        key = store.keys.get(s.key_name) if s.key_name else None
        blocks.append(
            _render_host_block(
                s.alias,
                s.hostname,
                s.username,
                s.port,
                key.private_key_path if key else None,
                s.jump_host,
                s.extra_options,
            )
        )
    return "\n\n".join(blocks)


def _check_duplicate_aliases(store: AppStore) -> None:
    """Last line of defense before touching disk - AppStore already enforces
    this, but the engine re-checks since it's what actually writes the file.
    """
    aliases = [jh.name for jh in store.list_jump_hosts()] + [
        s.alias for s in store.list_servers()
    ]
    seen = set()
    for alias in aliases:
        if alias in seen:
            raise SSHConfigError(f"Duplicate Host alias detected: '{alias}'")
        seen.add(alias)


def _strip_managed_hosts(text: str, store: AppStore) -> str:
    """Remove manual Host blocks that are now managed by the app to prevent duplicates."""
    managed_aliases = {jh.name for jh in store.list_jump_hosts()} | {s.alias for s in store.list_servers()}
    
    lines = text.splitlines()
    out_lines = []
    
    skip_current_block = False
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("host ") or stripped.lower().startswith("match "):
            if stripped.lower().startswith("match "):
                skip_current_block = False
            else:
                parts = stripped.split()
                aliases = parts[1:]
                unmanaged = [a for a in aliases if a not in managed_aliases]
                if not unmanaged:
                    # All aliases in this block are managed by the app, strip the whole block
                    skip_current_block = True
                    continue
                else:
                    # Keep only the unmanaged aliases on this line
                    skip_current_block = False
                    prefix = line[:len(line) - len(line.lstrip())] + parts[0]
                    out_lines.append(f"{prefix} {' '.join(unmanaged)}")
                    continue
                    
        if not skip_current_block:
            out_lines.append(line)
            
    # Clean up excessive blank lines created by stripping
    cleaned = "\n".join(out_lines)
    return re.sub(r'\n{3,}', '\n\n', cleaned)


def merge_into_full_config(existing_text: str, store: AppStore) -> str:
    """Replace the managed block inside existing_text, preserving everything
    else. If no managed block exists yet, append one.
    """
    _check_duplicate_aliases(store)
    block = generate_block(store)
    header = (
        "# This block is auto-generated by SSH Bootstrap Manager.\n"
        "# Do not edit by hand - manage servers and jump hosts from the app;\n"
        "# manual changes here will be overwritten on the next save.\n"
    )
    body = f"{header}{block}\n" if block else header
    managed = f"{MARK_START}\n{body}{MARK_END}"

    pattern = re.compile(re.escape(MARK_START) + r".*?" + re.escape(MARK_END), re.DOTALL)
    if pattern.search(existing_text):
        manual_text = pattern.sub("", existing_text)
    else:
        manual_text = existing_text
        
    cleaned_manual = _strip_managed_hosts(manual_text, store)
    
    sep = "\n\n" if cleaned_manual.strip() else ""
    new_text = cleaned_manual.rstrip("\n") + sep + managed
    return new_text if new_text.endswith("\n") else new_text + "\n"

def validate(text: str) -> list[str]:
    """Return a list of human-readable problems; empty list means valid."""
    problems: list[str] = []

    seen = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        parts = stripped.split()
        if parts and parts[0].lower() == "host":
            for alias in parts[1:]:
                if alias in seen:
                    problems.append(f"Duplicate Host entry: '{alias}'")
                seen.add(alias)
        stripped = line.strip()
        if stripped.lower().startswith("port "):
            value = stripped.split(None, 1)[1].strip()
            if not value.isdigit() or not (1 <= int(value) <= 65535):
                problems.append(f"Invalid Port value: '{value}'")

    try:
        cfg = paramiko.SSHConfig()
        cfg.parse(io.StringIO(text))
    except Exception as e:
        problems.append(f"SSH config syntax error: {e}")

    return problems


def _validate_and_atomic_write(new_text: str, path: Path) -> str:
    """Shared by write() and write_raw(): validate, back up whatever's
    currently on disk, then atomically replace it. Raises SSHConfigError
    (without touching disk) if validation fails.
    """
    problems = validate(new_text)
    if problems:
        raise SSHConfigError("; ".join(problems))

    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

    if path.exists():
        backup_path = path.with_name(path.name + ".bak")
        backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".config-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(new_text)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    if os.name != "nt":
        os.chmod(path, 0o600)

    return new_text


def write(store: AppStore, config_path: Optional[Path] = None) -> str:
    """Regenerate, validate, back up, and atomically save ~/.ssh/config.

    Raises SSHConfigError (without touching disk) if validation fails.
    """
    path = Path(config_path) if config_path else default_config_path()
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    new_text = merge_into_full_config(existing, store)
    return _validate_and_atomic_write(new_text, path)


def write_raw(text: str, config_path: Optional[Path] = None) -> str:
    """Save hand-edited config text as-is (the app's "advanced mode").
    Validated and backed up the same way as write(), but bypasses the
    store/managed-block generation entirely - the next GUI-driven change
    will still regenerate the managed block from the store, so manual
    edits inside it won't survive that; edits outside it will.
    """
    path = Path(config_path) if config_path else default_config_path()
    return _validate_and_atomic_write(text, path)


def _parse_raw_entries(text: str) -> list[dict]:
    """Minimal SSH-config parser that keeps each Host block's raw options,
    used for import so we don't lose fidelity to wildcard-merge behavior
    that paramiko's lookup() applies.
    """
    entries: list[dict] = []
    current: Optional[dict] = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        key, value = parts[0], parts[1].strip().strip('"')
        if key.lower() == "host":
            current = {"aliases": value.split(), "options": {}}
            entries.append(current)
        elif current is not None:
            current["options"][key.lower()] = value
    return entries


def write_raw(text: str) -> None:
    """Overwrite the SSH configuration file completely with the provided text.
    This is used by the advanced manual-edit mode.
    """
    path = default_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def import_existing(path: str) -> tuple[list[Server], list[JumpHost], list[SSHKey]]:
    """Parse an arbitrary SSH config file into model objects. A Host used as
    another entry's ProxyJump target is inferred to be a Jump Host.
    """
    text = Path(path).read_text(encoding="utf-8")
    entries = _parse_raw_entries(text)

    proxy_targets = {
        e["options"]["proxyjump"]
        for e in entries
        if "proxyjump" in e["options"]
    }

    servers: list[Server] = []
    jump_hosts: list[JumpHost] = []
    keys: list[SSHKey] = []
    key_name_by_path: dict[str, str] = {}

    for e in entries:
        if not e["aliases"]:
            continue
        alias = e["aliases"][0]
        if "*" in alias or "?" in alias:
            continue  # wildcard patterns aren't a single manageable host

        opts = e["options"]
        hostname = opts.get("hostname", alias)
        username = opts.get("user", "")
        port_str = opts.get("port", "22")
        port = int(port_str) if port_str.isdigit() else 22

        key_name = None
        identity = opts.get("identityfile")
        if identity:
            if identity not in key_name_by_path:
                name = Path(identity).stem
                key_name_by_path[identity] = name
                keys.append(
                    SSHKey(name=name, private_key_path=identity, public_key_path=identity + ".pub")
                )
            key_name = key_name_by_path[identity]

        extra_lines = [
            f"{k} {v}" for k, v in opts.items() if k not in _HANDLED_OPTIONS
        ]
        extra_options = "\n".join(extra_lines)

        if alias in proxy_targets:
            jump_hosts.append(
                JumpHost(
                    name=alias,
                    hostname=hostname,
                    username=username,
                    port=port,
                    key_name=key_name,
                    extra_options=extra_options,
                )
            )
        else:
            servers.append(
                Server(
                    alias=alias,
                    hostname=hostname,
                    username=username,
                    port=port,
                    key_name=key_name,
                    jump_host=opts.get("proxyjump"),
                    extra_options=extra_options,
                )
            )

    return servers, jump_hosts, keys


def export(store: AppStore, dest_path) -> None:
    """Write a standalone, portable SSH config file for the current state -
    no managed-block markers, since it's meant to be dropped in as-is
    elsewhere.
    """
    block = generate_block(store)
    content = block + "\n" if block else ""
    Path(dest_path).write_text(content, encoding="utf-8")
