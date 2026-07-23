import pytest

from sshmgr.store import AppStore, ValidationError
from sshmgr.models import Server, JumpHost, SSHKey


@pytest.fixture
def store(tmp_path):
    return AppStore(path=tmp_path / "data.json")


def test_add_and_list_server(store):
    store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    assert [s.alias for s in store.list_servers()] == ["web1"]


def test_duplicate_alias_rejected(store):
    store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    with pytest.raises(ValidationError):
        store.add_server(Server(alias="web1", hostname="5.6.7.8", username="root"))


def test_required_fields(store):
    with pytest.raises(ValidationError):
        store.add_server(Server(alias="", hostname="1.2.3.4", username="root"))
    with pytest.raises(ValidationError):
        store.add_server(Server(alias="web1", hostname="", username="root"))
    with pytest.raises(ValidationError):
        store.add_server(Server(alias="web1", hostname="1.2.3.4", username=""))


def test_invalid_port_rejected(store):
    with pytest.raises(ValidationError):
        store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root", port=0))
    with pytest.raises(ValidationError):
        store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root", port=70000))


def test_jump_host_must_exist(store):
    with pytest.raises(ValidationError):
        store.add_server(
            Server(alias="web1", hostname="1.2.3.4", username="root", jump_host="bastion")
        )
    store.add_jump_host(JumpHost(name="bastion", hostname="9.9.9.9", username="admin"))
    store.add_server(
        Server(alias="web1", hostname="1.2.3.4", username="root", jump_host="bastion")
    )


def test_update_server_rename(store):
    store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    store.update_server("web1", Server(alias="web2", hostname="1.2.3.4", username="root"))
    assert "web1" not in store.servers
    assert "web2" in store.servers


def test_delete_server(store):
    store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    store.delete_server("web1")
    assert store.list_servers() == []
    with pytest.raises(ValidationError):
        store.delete_server("web1")


def test_duplicate_server(store):
    store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    copy = store.duplicate_server("web1", "web1-copy")
    assert copy.alias == "web1-copy"
    assert len(store.list_servers()) == 2


def test_search_servers(store):
    store.add_server(Server(alias="web1", hostname="1.2.3.4", username="root"))
    store.add_server(Server(alias="db1", hostname="5.6.7.8", username="root"))
    assert [s.alias for s in store.search_servers("WEB")] == ["web1"]
    assert [s.alias for s in store.search_servers("")] == ["db1", "web1"]


def test_delete_jump_host_clears_dependents(store):
    store.add_jump_host(JumpHost(name="bastion", hostname="9.9.9.9", username="admin"))
    store.add_server(
        Server(alias="web1", hostname="1.2.3.4", username="root", jump_host="bastion")
    )
    store.delete_jump_host("bastion")
    assert store.servers["web1"].jump_host is None


def test_rename_jump_host_updates_dependents(store):
    store.add_jump_host(JumpHost(name="bastion", hostname="9.9.9.9", username="admin"))
    store.add_server(
        Server(alias="web1", hostname="1.2.3.4", username="root", jump_host="bastion")
    )
    store.update_jump_host(
        "bastion", JumpHost(name="bastion2", hostname="9.9.9.9", username="admin")
    )
    assert store.servers["web1"].jump_host == "bastion2"


def test_persistence_round_trip(tmp_path):
    path = tmp_path / "data.json"
    store1 = AppStore(path=path)
    store1.add_key(SSHKey(name="id_rsa", private_key_path="/x/id_rsa", public_key_path="/x/id_rsa.pub"))
    store1.add_server(Server(alias="web1", hostname="1.2.3.4", username="root", key_name="id_rsa"))

    store2 = AppStore(path=path)
    assert store2.servers["web1"].key_name == "id_rsa"
    assert store2.keys["id_rsa"].private_key_path == "/x/id_rsa"


def test_add_server_skip_key(store):
    # Verify a server can be created without generating or providing a new key
    store.add_server(Server(alias="no_key_server", hostname="1.2.3.4", username="root", key_name=None))
    assert store.servers["no_key_server"].key_name is None


def test_edge_cases_long_alias(store):
    long_alias = "a" * 300
    store.add_server(Server(alias=long_alias, hostname="1.2.3.4", username="root"))
    assert store.servers[long_alias].alias == long_alias


def test_edge_cases_ipv6(store):
    store.add_server(Server(alias="ipv6_server", hostname="2001:0db8:85a3:0000:0000:8a2e:0370:7334", username="root"))
    assert store.servers["ipv6_server"].hostname == "2001:0db8:85a3:0000:0000:8a2e:0370:7334"


def test_edge_cases_special_chars_in_username(store):
    store.add_server(Server(alias="special_user", hostname="1.2.3.4", username="user.name+test@domain.com"))
    assert store.servers["special_user"].username == "user.name+test@domain.com"

