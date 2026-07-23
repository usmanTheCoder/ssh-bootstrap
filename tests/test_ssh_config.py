import pytest

from sshmgr.store import AppStore
from sshmgr.models import Server, JumpHost, SSHKey
from sshmgr import ssh_config


@pytest.fixture
def store(tmp_path):
    return AppStore(path=tmp_path / "data.json")


def test_generate_block_empty(store):
    assert ssh_config.generate_block(store) == ""


def test_generate_block_basic_server(store):
    store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root", port=22))
    block = ssh_config.generate_block(store)
    assert "Host web1" in block
    assert "HostName 1.2.3.4" in block
    assert "User root" in block
    assert "Port 22" in block


def test_generate_block_with_key_and_jump_host(store):
    store.add_key(SSHKey(name="mykey", private_key_path="/home/u/.ssh/mykey", public_key_path="/home/u/.ssh/mykey.pub"))
    store.add_jump_host(JumpHost(name="bastion", hostname="9.9.9.9", username="admin"))
    store.add_server(
        Server(alias="web1", hostname="1.2.3.4", username="root", key_name="mykey", jump_host="bastion")
    )
    block = ssh_config.generate_block(store)
    assert "Host bastion" in block
    assert "Host web1" in block
    assert "IdentityFile /home/u/.ssh/mykey" in block
    assert "ProxyJump bastion" in block
    # jump host block must appear before the server that references it
    assert block.index("Host bastion") < block.index("Host web1")


def test_merge_preserves_unrelated_content(store):
    existing = "Host unrelated\n    HostName example.com\n    User someone\n"
    store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    merged = ssh_config.merge_into_full_config(existing, store)
    assert "Host unrelated" in merged
    assert "example.com" in merged
    assert "Host web1" in merged


def test_merge_replaces_previous_managed_block_only(store):
    store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    first = ssh_config.merge_into_full_config("Host manual\n    HostName manual.example.com\n", store)

    store.add_server(Server(alias="web2", hostname="5.6.7.8", username="admin"))
    second = ssh_config.merge_into_full_config(first, store)

    assert "Host manual" in second
    assert "Host web1" in second
    assert "Host web2" in second
    # only one managed block marker pair should exist
    assert second.count(ssh_config.MARK_START) == 1
    assert second.count(ssh_config.MARK_END) == 1


def test_validate_detects_duplicate_host():
    text = "Host web1\n    HostName 1.2.3.4\nHost web1\n    HostName 5.6.7.8\n"
    problems = ssh_config.validate(text)
    assert any("Duplicate Host" in p for p in problems)


def test_validate_detects_bad_port():
    text = "Host web1\n    HostName 1.2.3.4\n    Port 99999\n"
    problems = ssh_config.validate(text)
    assert any("Invalid Port" in p for p in problems)


def test_validate_clean_config_has_no_problems(store):
    store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    merged = ssh_config.merge_into_full_config("", store)
    assert ssh_config.validate(merged) == []


def test_write_creates_file_and_backup(tmp_path, store):
    config_path = tmp_path / "config"
    config_path.write_text("Host manual\n    HostName manual.example.com\n", encoding="utf-8")

    store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    ssh_config.write(store, config_path=config_path)

    content = config_path.read_text(encoding="utf-8")
    assert "Host manual" in content
    assert "Host web1" in content

    backup_path = config_path.with_name(config_path.name + ".bak")
    assert backup_path.exists()
    assert "Host manual" in backup_path.read_text(encoding="utf-8")


def test_write_creates_config_if_missing(tmp_path, store):
    config_path = tmp_path / "newdir" / "config"
    store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    ssh_config.write(store, config_path=config_path)
    assert config_path.exists()
    assert "Host web1" in config_path.read_text(encoding="utf-8")


def test_write_no_duplicate_after_edit(tmp_path, store):
    config_path = tmp_path / "config"
    store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    ssh_config.write(store, config_path=config_path)

    store.update_server("web1", Server(alias="web1", hostname="9.9.9.9", username="root"))
    ssh_config.write(store, config_path=config_path)

    content = config_path.read_text(encoding="utf-8")
    assert content.count("Host web1") == 1
    assert "9.9.9.9" in content


def test_import_existing_infers_jump_host(tmp_path):
    config_text = (
        "Host bastion\n"
        "    HostName 9.9.9.9\n"
        "    User admin\n"
        "\n"
        "Host web1\n"
        "    HostName 1.2.3.4\n"
        "    User root\n"
        "    Port 2222\n"
        "    ProxyJump bastion\n"
        "    IdentityFile /home/u/.ssh/id_rsa\n"
    )
    config_path = tmp_path / "import_config"
    config_path.write_text(config_text, encoding="utf-8")

    servers, jump_hosts, keys = ssh_config.import_existing(config_path)

    assert len(jump_hosts) == 1
    assert jump_hosts[0].name == "bastion"
    assert len(servers) == 1
    assert servers[0].alias == "web1"
    assert servers[0].port == 2222
    assert servers[0].jump_host == "bastion"
    assert servers[0].key_name == "id_rsa"
    assert len(keys) == 1
    assert keys[0].private_key_path == "/home/u/.ssh/id_rsa"


def test_jump_host_rename_cascades_into_generated_config(store):
    store.add_jump_host(JumpHost(name="bastion", hostname="9.9.9.9", username="admin"))
    store.add_server(
        Server(alias="web1", hostname="1.2.3.4", username="root", jump_host="bastion")
    )
    store.update_jump_host(
        "bastion", JumpHost(name="bastion2", hostname="9.9.9.9", username="admin")
    )
    block = ssh_config.generate_block(store)
    assert "Host bastion2" in block
    assert "ProxyJump bastion2" in block
    assert "bastion\n" not in block.replace("bastion2", "")  # old name fully gone
    assert "Host bastion\n" not in block


def test_jump_host_delete_removes_proxyjump_from_config(store):
    store.add_jump_host(JumpHost(name="bastion", hostname="9.9.9.9", username="admin"))
    store.add_server(
        Server(alias="web1", hostname="1.2.3.4", username="root", jump_host="bastion")
    )
    store.delete_jump_host("bastion")
    block = ssh_config.generate_block(store)
    assert "ProxyJump" not in block
    assert "Host bastion" not in block
    assert "Host web1" in block


def test_export_writes_plain_config(tmp_path, store):
    store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    dest = tmp_path / "exported_config"
    ssh_config.export(store, dest)
    content = dest.read_text(encoding="utf-8")
    assert "Host web1" in content
    assert ssh_config.MARK_START not in content


def test_write_raw_saves_valid_text_and_backs_up_existing(tmp_path):
    config_path = tmp_path / "config"
    config_path.write_text("Host old\n    HostName old.example.com\n", encoding="utf-8")

    new_text = "Host manual\n    HostName manual.example.com\n    User admin\n"
    result = ssh_config.write_raw(new_text, config_path=config_path)

    assert result == new_text
    assert config_path.read_text(encoding="utf-8") == new_text
    backup_path = config_path.with_name(config_path.name + ".bak")
    assert "Host old" in backup_path.read_text(encoding="utf-8")


def test_write_raw_rejects_invalid_text_without_touching_disk(tmp_path):
    config_path = tmp_path / "config"
    original = "Host old\n    HostName old.example.com\n"
    config_path.write_text(original, encoding="utf-8")

    bad_text = "Host web1\n    HostName 1.2.3.4\nHost web1\n    HostName 5.6.7.8\n"
    with pytest.raises(ssh_config.SSHConfigError):
        ssh_config.write_raw(bad_text, config_path=config_path)

    assert config_path.read_text(encoding="utf-8") == original


def test_import_existing_empty_config(tmp_path):
    config_path = tmp_path / "empty_config"
    config_path.write_text("", encoding="utf-8")
    servers, jump_hosts, keys = ssh_config.import_existing(config_path)
    assert len(servers) == 0
    assert len(jump_hosts) == 0
    assert len(keys) == 0


def test_import_existing_invalid_config(tmp_path):
    # import_existing is a best-effort parser, it skips bad lines.
    config_path = tmp_path / "invalid_config"
    config_path.write_text("Just some random text\nHost \n    Port asdf\n", encoding="utf-8")
    servers, jump_hosts, keys = ssh_config.import_existing(config_path)
    # It might create an empty server if Host has no alias, or just skip it depending on implementation.
    # The main verification is it doesn't crash.
    assert isinstance(servers, list)
