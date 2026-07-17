"""Plain data models for the SSH Configuration Manager.

These are pure data holders (no I/O, no validation beyond type coercion) -
validation and uniqueness rules live in store.py, since they depend on the
full collection of servers/jump hosts, not a single record.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class SSHKey:
    name: str
    private_key_path: str
    public_key_path: str
    key_type: str = "rsa"

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "SSHKey":
        return SSHKey(
            name=data["name"],
            private_key_path=data["private_key_path"],
            public_key_path=data["public_key_path"],
            key_type=data.get("key_type", "rsa"),
        )


@dataclass
class JumpHost:
    name: str
    hostname: str
    username: str
    port: int = 22
    key_name: Optional[str] = None
    extra_options: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "JumpHost":
        return JumpHost(
            name=data["name"],
            hostname=data["hostname"],
            username=data["username"],
            port=int(data.get("port", 22)),
            key_name=data.get("key_name"),
            extra_options=data.get("extra_options", ""),
        )


@dataclass
class Server:
    alias: str
    hostname: str
    username: str
    port: int = 22
    key_name: Optional[str] = None
    jump_host: Optional[str] = None
    extra_options: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Server":
        return Server(
            alias=data["alias"],
            hostname=data["hostname"],
            username=data["username"],
            port=int(data.get("port", 22)),
            key_name=data.get("key_name"),
            jump_host=data.get("jump_host"),
            extra_options=data.get("extra_options", ""),
        )


@dataclass
class Settings:
    theme: str = "dark"
    git_repo_url: Optional[str] = None
    auto_sync: bool = False
    last_sync_timestamp: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Settings":
        return Settings(
            theme=data.get("theme", "dark"),
            git_repo_url=data.get("git_repo_url"),
            auto_sync=data.get("auto_sync", False),
            last_sync_timestamp=data.get("last_sync_timestamp"),
        )
