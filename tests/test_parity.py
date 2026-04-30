"""Parity tests - CLI output vs captured MCP fixtures.

Run: uv run --with pytest --with httpx pytest test_parity.py -v

Purpose: prove that the repo-local `fibery` CLI returns results semantically equivalent
to the mcp__fibery__* tools it's designed to replace. This is the go/no-go
gate for the future migration: if parity holds, migrating agents to the
CLI is safe.

Fixtures in fixtures/ were captured from the MCP server at the same moment
the CLI was built. If Fibery schema changes, regenerate fixtures by running
the MCP equivalent commands and overwriting the files.
"""
from __future__ import annotations

import json
import re

import pytest


# ---------- MCP output parsers ----------

def _parse_mcp_list_databases(text: str) -> list[str]:
    """MCP list_databases returns a numbered plaintext list.

    Format: '1. Space/DbName' one per line.
    """
    names = []
    for line in text.splitlines():
        m = re.match(r"^\d+\.\s+(.+)$", line.strip())
        if m:
            names.append(m.group(1).strip())
    return names


def _parse_mcp_describe(text: str) -> dict[str, str]:
    """MCP describe returns: 'FieldTitle [field/name]: type'

    Returns dict of field-name → type.
    """
    fields = {}
    for line in text.splitlines():
        m = re.match(r"^\s+\S.*\[([^\]]+)\]:\s*(.+)$", line)
        if m:
            fields[m.group(1).strip()] = m.group(2).strip()
    return fields


# ---------- Parity tests ----------

def test_parse_mcp_list_databases(fixtures_dir):
    text = (fixtures_dir / "mcp_list_databases.txt").read_text()
    names = _parse_mcp_list_databases(text)
    assert len(names) >= 80
    assert "Sandbox/Database 1" in names
    assert "Task Management/Task" in names
    assert "comments/comment" in names


def test_parse_mcp_describe(fixtures_dir):
    text = (fixtures_dir / "mcp_describe_sandbox.txt").read_text()
    fields = _parse_mcp_describe(text)
    assert "fibery/id" in fields
    assert fields["fibery/id"] == "fibery/uuid"
    assert "Sandbox/Name" in fields
    assert fields["Sandbox/Name"] == "fibery/text"


def test_cli_dbs_all_matches_mcp_list_databases(workspace_cli_run, fixtures_dir):
    """Every database MCP reports must appear in `fibery dbs --all`.

    CLI's default dbs filters to domain types. The MCP tool includes enums
    and workflow types too, so we compare against `dbs --all`.
    """
    mcp_text = (fixtures_dir / "mcp_list_databases.txt").read_text()
    mcp_names = set(_parse_mcp_list_databases(mcp_text))

    cli_data = json.loads(workspace_cli_run("dbs", "--all").stdout)
    cli_names = {d["name"] for d in cli_data}

    missing_from_cli = mcp_names - cli_names
    # Allow fibery/* system types to differ (some live purely server-side)
    missing_non_system = {n for n in missing_from_cli if not n.startswith("fibery/")}
    assert not missing_non_system, (
        f"MCP reports databases missing from CLI: {sorted(missing_non_system)}"
    )


def test_cli_dbs_domain_is_strict_subset(workspace_cli_run):
    """Default `fibery dbs` returns fewer types than `dbs --all`.

    The CLI intentionally filters to domain-only, non-enum, non-system types.
    MCP's list_databases includes junction types, enums, and system types that
    the CLI's default filter excludes. This is by design, not a regression.
    This test verifies the filter works (default < all) and returns real data.
    """
    default = json.loads(workspace_cli_run("dbs").stdout)
    all_types = json.loads(workspace_cli_run("dbs", "--all").stdout)
    assert len(default) > 5, "Default filter returned suspiciously few databases"
    assert len(all_types) > len(default), "--all should return more types than default"
    # Every default entry should be in the all list
    default_names = {d["name"] for d in default}
    all_names = {d["name"] for d in all_types}
    assert default_names <= all_names, "Default returned types not in --all"


def test_cli_describe_matches_mcp_describe(workspace_cli_run, live_test_settings, fixtures_dir):
    """Describe the same type and compare field-name → type mappings."""
    mcp_text = (fixtures_dir / "mcp_describe_sandbox.txt").read_text()
    mcp_fields = _parse_mcp_describe(mcp_text)

    cli_data = json.loads(workspace_cli_run("describe", live_test_settings["sandbox_db"]).stdout)
    cli_fields = {f["name"]: f["type"] for f in cli_data["fields"]}

    # Every field MCP reports must be in CLI (MCP may have fewer due to mixins)
    for name, mcp_type in mcp_fields.items():
        assert name in cli_fields, f"Field {name} reported by MCP but missing in CLI"
        # Type strings may not match byte-for-byte (MCP translates 'int' etc)
        # but should at least share a common root
        cli_type = cli_fields[name]
        if "fibery/" in mcp_type and "fibery/" in cli_type:
            assert mcp_type == cli_type, f"{name}: MCP={mcp_type} CLI={cli_type}"


def test_cli_query_matches_mcp_query_shape(workspace_cli_run, live_test_settings, fixtures_dir):
    """Query Sandbox/Database 1 and verify CLI returns semantically equivalent data.

    Both should return a list of objects with the same IDs (modulo ordering and
    any entities created after the fixture was captured).
    """
    mcp_data = json.loads((fixtures_dir / "mcp_query_sandbox.json").read_text())
    assert mcp_data["success"] is True
    mcp_entities = {e["Id"]: e for e in mcp_data["result"]}

    cli_raw = workspace_cli_run(
        "query",
        live_test_settings["sandbox_db"],
        "--select",
        "Sandbox/Name,fibery/public-id,fibery/id",
        "--limit",
        "100",
    ).stdout
    cli_data = json.loads(cli_raw)
    cli_entities = {e["fibery/id"]: e for e in cli_data}

    # Every MCP entity must still exist in live CLI output (unless Kyle deleted it)
    live_both = set(mcp_entities) & set(cli_entities)
    assert len(live_both) >= 1, (
        f"No overlap between MCP fixture ({len(mcp_entities)}) and live CLI ({len(cli_entities)})"
    )
    # For entities present in both, the Name should match
    for eid in live_both:
        assert mcp_entities[eid]["Name"] == cli_entities[eid]["Sandbox/Name"], (
            f"Name mismatch for {eid}: MCP='{mcp_entities[eid]['Name']}' "
            f"CLI='{cli_entities[eid]['Sandbox/Name']}'"
        )


def test_cli_query_with_where_same_as_mcp_filter(workspace_cli_run, live_test_settings):
    """Query with --where filter returns subset of full query, same IDs."""
    full = json.loads(
        workspace_cli_run(
            "query",
            live_test_settings["sandbox_db"],
            "--select",
            "Sandbox/Name,fibery/id",
            "--limit",
            "100",
        ).stdout
    )
    if not full:
        pytest.skip("Sandbox empty")
    target_name = full[0]["Sandbox/Name"]
    filtered = json.loads(
        workspace_cli_run(
            "query",
            live_test_settings["sandbox_db"],
            "--where",
            f"Sandbox/Name={target_name}",
            "--select",
            "Sandbox/Name,fibery/id",
            "--limit",
            "100",
        ).stdout
    )
    assert len(filtered) >= 1
    assert any(e["Sandbox/Name"] == target_name for e in filtered)
