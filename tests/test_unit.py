"""Unit tests - no network. Tests helper functions and handler logic.

Run: uv run --with pytest --with httpx pytest test_unit.py -v
"""
from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


# ---------- Helper function tests ----------

def test_resolve_host_aliases(fibery_cli):
    config = {
        "workspaces": {
            "myworkspace": {
                "host": "myworkspace.fibery.io",
                "keychain_account": "fibery-myworkspace",
            },
            "backup": {
                "host": "backup.fibery.io",
            },
        }
    }
    assert fibery_cli.resolve_host("myworkspace", config=config) == "myworkspace.fibery.io"
    assert fibery_cli.resolve_host("MYWORKSPACE", config=config) == "myworkspace.fibery.io"
    assert fibery_cli.resolve_host("backup", config=config) == "backup.fibery.io"


def test_resolve_host_direct_flag_overrides_config(fibery_cli):
    config = {"workspaces": {"myworkspace": {"host": "configured.fibery.io"}}}
    assert (
        fibery_cli.resolve_host(
            "myworkspace",
            workspace_host="https://override.fibery.io/",
            config=config,
        )
        == "override.fibery.io"
    )


def test_resolve_host_unknown_exits(fibery_cli):
    with pytest.raises(SystemExit) as exc_info:
        fibery_cli.resolve_host("notarealworkspace", config={})
    assert exc_info.value.code == fibery_cli.EXIT_USER_ERROR


def test_resolve_keychain_account_uses_config(fibery_cli):
    config = {
        "workspaces": {
            "myworkspace": {
                "host": "myworkspace.fibery.io",
                "keychain_account": "custom-account",
            }
        }
    }
    assert (
        fibery_cli.resolve_keychain_account(
            "myworkspace",
            "myworkspace.fibery.io",
            config=config,
        )
        == "custom-account"
    )


def test_get_token_prefers_flag_then_env(fibery_cli):
    assert (
        fibery_cli.get_token(
            "myworkspace.fibery.io",
            workspace="myworkspace",
            token="flag-token",
            config={},
        )
        == "flag-token"
    )
    with patch.dict("os.environ", {"FIBERY_TOKEN": "env-token"}, clear=False):
        assert (
            fibery_cli.get_token(
                "myworkspace.fibery.io",
                workspace="myworkspace",
                config={},
            )
            == "env-token"
        )


def test_parse_where_simple(fibery_cli):
    assert fibery_cli._parse_where("Name=foo") == ("=", "Name", "foo")
    assert fibery_cli._parse_where("priority>5") == (">", "priority", "5")
    assert fibery_cli._parse_where("State!=Done") == ("!=", "State", "Done")
    assert fibery_cli._parse_where("count>=10") == (">=", "count", "10")


def test_parse_where_invalid_exits(fibery_cli):
    with pytest.raises(SystemExit):
        fibery_cli._parse_where("no operator here")


def test_parse_field_hint(fibery_cli):
    assert fibery_cli._parse_field_hint("priority:int") == ("priority", "int")
    assert fibery_cli._parse_field_hint("done:bool") == ("done", "bool")
    assert fibery_cli._parse_field_hint("Name") == ("Name", None)
    # fibery/public-id has colon but not at end — should be left alone
    assert fibery_cli._parse_field_hint("fibery/public-id") == ("fibery/public-id", None)


def test_coerce_types(fibery_cli):
    assert fibery_cli._coerce("5", "int") == 5
    assert fibery_cli._coerce("3.14", "float") == 3.14
    assert fibery_cli._coerce("true", "bool") is True
    assert fibery_cli._coerce("false", "bool") is False
    assert fibery_cli._coerce("yes", "bool") is True
    assert fibery_cli._coerce("", "null") is None
    assert fibery_cli._coerce("hello", None) == "hello"  # default = string
    assert fibery_cli._coerce("2", None) == "2"  # no coercion without hint


def test_coerce_invalid_hint_exits(fibery_cli):
    with pytest.raises(SystemExit):
        fibery_cli._coerce("x", "notarealtype")


def test_build_select_default(fibery_cli):
    result = fibery_cli._build_select(None)
    assert "fibery/id" in result
    assert "fibery/public-id" in result


def test_build_select_explicit(fibery_cli):
    result = fibery_cli._build_select("Name,State.enum/name")
    assert result["Name"] == ["Name"]
    assert result["State.enum/name"] == ["State", "enum/name"]
    # fibery/id always included
    assert "fibery/id" in result


def test_schema_diff_types(fibery_cli):
    live = {"fibery/types": [
        {"fibery/name": "A", "fibery/fields": [{"fibery/name": "f1"}, {"fibery/name": "f2"}]},
        {"fibery/name": "B", "fibery/fields": []},
    ]}
    target = {"fibery/types": [
        {"fibery/name": "A", "fibery/fields": [{"fibery/name": "f1"}, {"fibery/name": "f3"}]},
        {"fibery/name": "C", "fibery/fields": []},
    ]}
    diff = fibery_cli._schema_diff(live, target)
    assert diff["types_only_live"] == ["B"]
    assert diff["types_only_target"] == ["C"]
    assert diff["field_diffs"]["A"]["added"] == ["f3"]
    assert diff["field_diffs"]["A"]["removed"] == ["f2"]


def test_mandatory_base_fields_structure(fibery_cli):
    fields = fibery_cli._mandatory_base_fields("Sandbox")
    names = [f["fibery/name"] for f in fields]
    assert "fibery/id" in names
    assert "fibery/public-id" in names
    assert "fibery/creation-date" in names
    assert "fibery/modification-date" in names
    assert "Sandbox/name" in names
    # No explicit secured:false (which Fibery rejects on secured types)
    for f in fields:
        assert f["fibery/meta"].get("fibery/secured?") is None


# ---------- Handler tests with mocked HTTP ----------

def _make_ctx(fibery_cli, mock_client=None):
    return fibery_cli.Ctx(
        workspace="myworkspace",
        host="myworkspace.fibery.io",
        token="fake-token",
        client=mock_client or MagicMock(),
    )


def test_cmd_dbs_filters_non_domain(fibery_cli, capsys):
    ctx = _make_ctx(fibery_cli)
    fake_result = {
        "fibery/types": [
            {"fibery/name": "Biz/Customer",
             "fibery/meta": {"fibery/domain?": True, "fibery/secured?": True, "ui/color": "#abc"},
             "fibery/fields": []},
            {"fibery/name": "workflow/state",
             "fibery/meta": {"fibery/enum?": True},
             "fibery/fields": []},
            {"fibery/name": "fibery/file",
             "fibery/meta": {},
             "fibery/fields": []},
        ]
    }
    with patch.object(fibery_cli, "post_command", return_value=fake_result):
        args = SimpleNamespace(all=False, output="json")
        fibery_cli.cmd_dbs(ctx, args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data) == 1
    assert data[0]["name"] == "Biz/Customer"


def test_cmd_dbs_all_includes_system(fibery_cli, capsys):
    ctx = _make_ctx(fibery_cli)
    fake_result = {
        "fibery/types": [
            {"fibery/name": "Biz/Customer",
             "fibery/meta": {"fibery/domain?": True},
             "fibery/fields": []},
            {"fibery/name": "fibery/file",
             "fibery/meta": {},
             "fibery/fields": []},
        ]
    }
    with patch.object(fibery_cli, "post_command", return_value=fake_result):
        args = SimpleNamespace(all=True, output="json")
        fibery_cli.cmd_dbs(ctx, args)
    data = json.loads(capsys.readouterr().out)
    assert len(data) == 2


def test_cmd_query_builds_where_clause(fibery_cli, capsys):
    ctx = _make_ctx(fibery_cli)
    captured = {}
    def fake_post(ctx_, cmd, args_):
        captured["cmd"] = cmd
        captured["args"] = args_
        return []
    with patch.object(fibery_cli, "post_command", side_effect=fake_post):
        args = SimpleNamespace(
            type="Test/Entity",
            where=["Name=hello", "count:int>5"],
            select="Name,count",
            limit=10,
            offset=0,
            order_by=None,
            order_desc=False,
            json_query=None,
            params=None,
            output="json",
        )
        fibery_cli.cmd_query(ctx, args)
    assert captured["cmd"] == "fibery.entity/query"
    q = captured["args"]["query"]
    assert q["q/from"] == "Test/Entity"
    assert q["q/limit"] == 10
    # Two conditions should be ANDed
    assert q["q/where"][0] == "q/and"
    # Params: string then int
    params = captured["args"]["params"]
    assert params["$p0"] == "hello"
    assert params["$p1"] == 5


def test_cmd_query_json_query_passthrough(fibery_cli, capsys):
    ctx = _make_ctx(fibery_cli)
    captured = {}
    def fake_post(ctx_, cmd, args_):
        captured["args"] = args_
        return []
    raw_query = {"q/from": "X/Y", "q/select": {"a": ["a"]}, "q/limit": 1}
    with patch.object(fibery_cli, "post_command", side_effect=fake_post):
        args = SimpleNamespace(
            type=None,
            where=[],
            select=None,
            limit=50,
            offset=0,
            order_by=None,
            order_desc=False,
            json_query=json.dumps(raw_query),
            params=None,
            output="json",
        )
        fibery_cli.cmd_query(ctx, args)
    assert captured["args"]["query"] == raw_query


def test_http_error_maps_401_to_auth_exit(fibery_cli):
    response = MagicMock()
    response.status_code = 401
    response.text = ""
    response.headers = {}
    with pytest.raises(SystemExit) as exc_info:
        fibery_cli.http_error(response)
    assert exc_info.value.code == fibery_cli.EXIT_AUTH_ERROR


def test_http_error_maps_429_to_api_exit(fibery_cli):
    response = MagicMock()
    response.status_code = 429
    response.text = ""
    response.headers = {"retry-after": "5"}
    with pytest.raises(SystemExit) as exc_info:
        fibery_cli.http_error(response)
    assert exc_info.value.code == fibery_cli.EXIT_API_ERROR


def test_http_error_generic_5xx(fibery_cli):
    response = MagicMock()
    response.status_code = 500
    response.text = "internal error"
    response.headers = {}
    with pytest.raises(SystemExit) as exc_info:
        fibery_cli.http_error(response)
    assert exc_info.value.code == fibery_cli.EXIT_API_ERROR


def test_post_command_unwraps_success(fibery_cli):
    ctx = _make_ctx(fibery_cli)
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.json.return_value = [{"success": True, "result": {"hello": "world"}}]
    ctx.client.post = MagicMock(return_value=mock_response)
    result = fibery_cli.post_command(ctx, "test/cmd", {})
    assert result == {"hello": "world"}


def test_post_command_failed_command_exits(fibery_cli):
    ctx = _make_ctx(fibery_cli)
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.json.return_value = [{"success": False, "result": {"message": "nope"}}]
    ctx.client.post = MagicMock(return_value=mock_response)
    with pytest.raises(SystemExit) as exc_info:
        fibery_cli.post_command(ctx, "test/cmd", {})
    assert exc_info.value.code == fibery_cli.EXIT_API_ERROR


def test_cmd_comments_query_shape(fibery_cli, capsys):
    ctx = _make_ctx(fibery_cli)
    captured = {}
    def fake_post(ctx_, cmd, args_):
        captured["args"] = args_
        return [{"fibery/id": "abc", "comments": [
            {"fibery/id": "c1", "created": "2026-01-02T00:00:00Z",
             "document-secret": None, "author-id": "u1", "author-name": "Me",
             "parent-id": None, "fibery/public-id": "1"},
            {"fibery/id": "c2", "created": "2026-01-01T00:00:00Z",
             "document-secret": None, "author-id": "u1", "author-name": "Me",
             "parent-id": None, "fibery/public-id": "2"},
        ]}]
    with patch.object(fibery_cli, "post_command", side_effect=fake_post):
        args = SimpleNamespace(
            id="abc", type="Sandbox/Foo", with_content=False, format="md", output="json",
        )
        fibery_cli.cmd_comments(ctx, args)
    out = json.loads(capsys.readouterr().out)
    # Sorted chronologically
    assert out[0]["fibery/id"] == "c2"
    assert out[1]["fibery/id"] == "c1"
    q = captured["args"]["query"]
    assert q["q/from"] == "Sandbox/Foo"
    assert "comments" in q["q/select"]
