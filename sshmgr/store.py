"""Local persistence and CRUD for the SSH Configuration Manager's app state.

This module owns the app's own JSON state file (servers, jump hosts, key
metadata, settings) - a separate thing from ~/.ssh/config itself, which is a
*generated artifact* owned by ssh_config.py. The UI layer is responsible for
calling ssh_config.write(store) after any mutation here so the two never
drift apart.
"""
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

from sshmgr.models import Server, JumpHost, SSHKey, Settings

logger = logging.getLogger(__name__)

DEFAULT_STORE_PATH = Path.home() / ".ssh-bootstrap-manager" / "data.json"


class ValidationError(Exception):
    """Raised when a mutation would violate a uniqueness/required-field rule."""


class AppStore:
    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else DEFAULT_STORE_PATH
        self.servers: dict[str, Server] = {}
        self.jump_hosts: dict[str, JumpHost] = {}
        self.keys: dict[str, SSHKey] = {}
        self.settings = Settings()
        self.load()

    # ---------------------------------------------------------------- I/O
    def load(self) -> None:
        if not self.path.exists():
            return
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.servers = {
            s["alias"]: Server.from_dict(s) for s in data.get("servers", [])
        }
        self.jump_hosts = {
            j["name"]: JumpHost.from_dict(j) for j in data.get("jump_hosts", [])
        }
        self.keys = {
            k["name"]: SSHKey.from_dict(k) for k in data.get("keys", [])
        }
        self.settings = Settings.from_dict(data.get("settings", {}))
        logger.debug(f"Loaded store from {self.path}")

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "servers": [s.to_dict() for s in self.servers.values()],
            "jump_hosts": [j.to_dict() for j in self.jump_hosts.values()],
            "keys": [k.to_dict() for k in self.keys.values()],
            "settings": self.settings.to_dict(),
        }
        fd, tmp_path = tempfile.mkstemp(
            dir=self.path.parent, prefix=".data-", suffix=".json.tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self.path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        logger.debug(f"Saved store to {self.path}")

    # ----------------------------------------------------------- servers
    def list_servers(self) -> list[Server]:
        return sorted(self.servers.values(), key=lambda s: s.alias.lower())

    def search_servers(self, query: str) -> list[Server]:
        q = query.strip().lower()
        if not q:
            return self.list_servers()
        return [
            s
            for s in self.list_servers()
            if q in s.alias.lower() or q in s.hostname.lower()
        ]

    def add_server(self, server: Server) -> None:
        self._validate_server(server, is_new=True)
        self.servers[server.alias] = server
        self.save()

    def update_server(self, original_alias: str, server: Server) -> None:
        if original_alias not in self.servers:
            raise ValidationError(f"Server '{original_alias}' does not exist.")
        self._validate_server(server, is_new=(server.alias != original_alias))
        if server.alias != original_alias:
            del self.servers[original_alias]
        self.servers[server.alias] = server
        self.save()

    def delete_server(self, alias: str) -> None:
        if alias not in self.servers:
            raise ValidationError(f"Server '{alias}' does not exist.")
        del self.servers[alias]
        self.save()

    def duplicate_server(self, alias: str, new_alias: str) -> Server:
        if alias not in self.servers:
            raise ValidationError(f"Server '{alias}' does not exist.")
        original = self.servers[alias]
        copy = Server(
            alias=new_alias,
            hostname=original.hostname,
            username=original.username,
            port=original.port,
            key_name=original.key_name,
            jump_host=original.jump_host,
            extra_options=original.extra_options,
        )
        self.add_server(copy)
        return copy

    def _validate_server(self, server: Server, is_new: bool) -> None:
        if not server.alias or not server.alias.strip():
            raise ValidationError("Host Alias is required.")
        if not server.hostname or not server.hostname.strip():
            raise ValidationError("Hostname/IP Address is required.")
        if not server.username or not server.username.strip():
            raise ValidationError("Username is required.")
        if not (1 <= server.port <= 65535):
            raise ValidationError("Port must be between 1 and 65535.")
        if is_new and server.alias in self.servers:
            raise ValidationError(f"A server with alias '{server.alias}' already exists.")
        if server.jump_host and server.jump_host not in self.jump_hosts:
            raise ValidationError(f"Jump Host '{server.jump_host}' does not exist.")
        if server.key_name and server.key_name not in self.keys:
            raise ValidationError(f"SSH Key '{server.key_name}' does not exist.")

    # -------------------------------------------------------- jump hosts
    def list_jump_hosts(self) -> list[JumpHost]:
        return sorted(self.jump_hosts.values(), key=lambda j: j.name.lower())

    def servers_using_jump_host(self, name: str) -> list[Server]:
        return [s for s in self.servers.values() if s.jump_host == name]

    def add_jump_host(self, jump_host: JumpHost) -> None:
        self._validate_jump_host(jump_host, is_new=True)
        self.jump_hosts[jump_host.name] = jump_host
        self.save()

    def update_jump_host(self, original_name: str, jump_host: JumpHost) -> None:
        if original_name not in self.jump_hosts:
            raise ValidationError(f"Jump Host '{original_name}' does not exist.")
        self._validate_jump_host(jump_host, is_new=(jump_host.name != original_name))
        if jump_host.name != original_name:
            del self.jump_hosts[original_name]
            for server in self.servers.values():
                if server.jump_host == original_name:
                    server.jump_host = jump_host.name
        self.jump_hosts[jump_host.name] = jump_host
        self.save()

    def delete_jump_host(self, name: str) -> None:
        if name not in self.jump_hosts:
            raise ValidationError(f"Jump Host '{name}' does not exist.")
        del self.jump_hosts[name]
        for server in self.servers.values():
            if server.jump_host == name:
                server.jump_host = None
        self.save()

    def _validate_jump_host(self, jump_host: JumpHost, is_new: bool) -> None:
        if not jump_host.name or not jump_host.name.strip():
            raise ValidationError("Jump Host name is required.")
        if not jump_host.hostname or not jump_host.hostname.strip():
            raise ValidationError("Jump Host Hostname/IP Address is required.")
        if not jump_host.username or not jump_host.username.strip():
            raise ValidationError("Jump Host Username is required.")
        if not (1 <= jump_host.port <= 65535):
            raise ValidationError("Jump Host Port must be between 1 and 65535.")
        if is_new and jump_host.name in self.jump_hosts:
            raise ValidationError(f"A Jump Host named '{jump_host.name}' already exists.")

    # -------------------------------------------------------------- keys
    def list_keys(self) -> list[SSHKey]:
        return sorted(self.keys.values(), key=lambda k: k.name.lower())

    def add_key(self, key: SSHKey) -> None:
        if key.name in self.keys:
            raise ValidationError(f"A key named '{key.name}' already exists.")
        self.keys[key.name] = key
        self.save()

    def remove_key(self, name: str) -> None:
        if name not in self.keys:
            raise ValidationError(f"Key '{name}' does not exist.")
        del self.keys[name]
        self.save()

    # ---------------------------------------------------------- settings
    def update_settings(self, **kwargs) -> None:
        for field_name, value in kwargs.items():
            setattr(self.settings, field_name, value)
        self.save()
