"""Integration tests against a live workspace.

Run: uv run --with pytest --with httpx pytest test_integration.py -v

These tests require:
  - FIBERY_TEST_WORKSPACE set to a workspace alias
  - FIBERY_TEST_WORKSPACE_HOST and FIBERY_TEST_TOKEN, or matching local config
  - A sandbox space and database visible to that workspace

Most tests are read-only. A few create and delete temporary sandbox entities.
"""
from __future__ import annotations

import json

import pytest


@pytest.mark.integration
def test_date_prints_iso_with_workspace(workspace_cli_run, live_test_settings):
    r = workspace_cli_run("date")
    data = json.loads(r.stdout)
    assert "iso" in data
    assert data["workspace"] == live_test_settings["workspace"]
    assert data["host"]
    if live_test_settings["workspace_host"]:
        assert data["host"] == live_test_settings["workspace_host"]


@pytest.mark.integration
def test_dbs_returns_list_with_sandbox(workspace_cli_run, live_test_settings):
    r = workspace_cli_run("dbs")
    data = json.loads(r.stdout)
    assert isinstance(data, list)
    assert len(data) > 0
    names = [d["name"] for d in data]
    sandbox_space = live_test_settings["sandbox_space"]
    assert any(sandbox_space in n for n in names), f"{sandbox_space} not in {names[:5]}"


@pytest.mark.integration
def test_dbs_all_flag_includes_more_types(workspace_cli_run):
    a = json.loads(workspace_cli_run("dbs").stdout)
    b = json.loads(workspace_cli_run("dbs", "--all").stdout)
    assert len(b) > len(a), "--all should expand the list"


@pytest.mark.integration
def test_describe_task_management_task(workspace_cli_run, live_test_settings):
    task_type = live_test_settings["task_type"]
    r = workspace_cli_run("describe", task_type)
    data = json.loads(r.stdout)
    assert data["name"] == task_type
    assert data["field_count"] > 5
    field_names = [f["name"] for f in data["fields"]]
    # Core fields must be present
    assert "fibery/id" in field_names
    assert "fibery/public-id" in field_names
    assert "fibery/creation-date" in field_names


@pytest.mark.integration
def test_query_task_management_task_limit(workspace_cli_run, live_test_settings):
    r = workspace_cli_run(
        "query",
        live_test_settings["task_type"],
        "--select",
        "fibery/public-id,fibery/id",
        "--limit",
        "3",
    )
    data = json.loads(r.stdout)
    assert isinstance(data, list)
    assert len(data) <= 3
    for row in data:
        assert "fibery/id" in row
        assert "fibery/public-id" in row


@pytest.mark.integration
def test_query_sandbox_database_1(workspace_cli_run, live_test_settings):
    r = workspace_cli_run(
        "query",
        live_test_settings["sandbox_db"],
        "--select",
        "Sandbox/Name,fibery/public-id",
        "--limit",
        "10",
    )
    data = json.loads(r.stdout)
    assert isinstance(data, list)
    # Should have at least one entity from earlier smoke tests
    assert len(data) >= 1


@pytest.mark.integration
def test_query_with_where_filter_string(workspace_cli_run, live_test_settings):
    # public-id is text; default string coercion should work
    r = workspace_cli_run(
        "query",
        live_test_settings["sandbox_db"],
        "--where",
        "fibery/public-id=3",
        "--select",
        "Sandbox/Name,fibery/public-id",
        check=False,
    )
    if r.returncode != 0:
        pytest.skip(f"No entity with public-id=3 in Sandbox (setup dependent)")
    data = json.loads(r.stdout)
    assert isinstance(data, list)


@pytest.mark.integration
def test_schema_dump_returns_types(workspace_cli_run):
    r = workspace_cli_run("schema", "dump")
    data = json.loads(r.stdout)
    assert "fibery/types" in data
    assert len(data["fibery/types"]) > 20


@pytest.mark.integration
def test_webhook_list_is_array(workspace_cli_run):
    r = workspace_cli_run("webhook", "list")
    data = json.loads(r.stdout)
    assert isinstance(data, list)


@pytest.mark.integration
def test_unknown_workspace_exits_user_error(cli_run):
    r = cli_run("nonexistent-workspace", "date", check=False)
    assert r.returncode == 1
    assert "Unknown workspace" in r.stderr


@pytest.mark.integration
def test_graphql_introspection(workspace_cli_run, live_test_settings):
    r = workspace_cli_run(
        "graphql",
        live_test_settings["sandbox_space"],
        "--query",
        "{ __schema { queryType { name } } }",
    )
    data = json.loads(r.stdout)
    assert data["data"]["__schema"]["queryType"]["name"] == "Query"


@pytest.mark.integration
def test_doc_write_canary(workspace_cli_run, live_test_settings):
    """Canary test for undocumented PUT /api/documents/{secret}.

    Creates a temp entity, writes to its doc field, reads back, verifies
    content matches, then cleans up. If this test fails, the PUT endpoint
    has been removed or changed by Fibery.
    """
    import uuid
    marker = f"canary-{uuid.uuid4().hex[:8]}"

    # Create temp entity to get a doc secret
    sandbox_db = live_test_settings["sandbox_db"]
    created = json.loads(
        workspace_cli_run(
            "create",
            sandbox_db,
            "--fields",
            json.dumps({"Sandbox/Name": marker}),
        ).stdout
    )
    entity_id = created["fibery/id"]

    try:
        # Get the description doc secret
        rows = json.loads(
            workspace_cli_run(
                "query",
                sandbox_db,
                "--json-query",
                json.dumps({
                    "q/from": sandbox_db,
                    "q/select": {"s": ["Sandbox/Description", "Collaboration~Documents/secret"]},
                    "q/where": ["=", ["fibery/id"], "$id"],
                    "q/limit": 1,
                }),
                "--params",
                json.dumps({"$id": entity_id}),
            ).stdout
        )
        secret = rows[0]["s"]
        assert secret, "No doc secret returned"

        # Write via PUT (the undocumented endpoint)
        content = f"Canary test content: {marker}"
        write_result = json.loads(workspace_cli_run("doc-write", secret, "--content", content).stdout)
        assert write_result["written"] is True, "doc-write returned written=false"

        # Read back
        read_result = json.loads(workspace_cli_run("doc", secret, "--format", "md").stdout)
        assert read_result["content"] == content, (
            f"Round-trip failed: wrote '{content}' but read '{read_result.get('content')}'"
        )
    finally:
        workspace_cli_run("delete", entity_id, "--type", sandbox_db, "--yes", check=False)


@pytest.mark.integration
def test_space_list_returns_spaces(workspace_cli_run, live_test_settings):
    data = json.loads(workspace_cli_run("space", "list").stdout)
    assert isinstance(data, list)
    assert len(data) > 5
    names = [s["fibery/name"] for s in data]
    assert live_test_settings["sandbox_space"] in names


@pytest.mark.integration
def test_event_seq_returns_number(workspace_cli_run):
    data = json.loads(workspace_cli_run("event-seq").stdout)
    assert isinstance(data["sequence_id"], int)
    assert data["sequence_id"] > 0


@pytest.mark.integration
def test_link_and_unlink_by_name(workspace_cli_run, live_test_settings):
    """Test link/unlink with --by-name on the Priority enum field."""
    import uuid
    marker = f"link-test-{uuid.uuid4().hex[:8]}"
    sandbox_db = live_test_settings["sandbox_db"]
    created = json.loads(
        workspace_cli_run(
            "create",
            sandbox_db,
            "--fields",
            json.dumps({"Sandbox/Name": marker}),
        ).stdout
    )
    entity_id = created["fibery/id"]
    try:
        # Link
        workspace_cli_run("link", entity_id, "--type", sandbox_db, "--field", "Sandbox/Priority", "--by-name", "High")

        # Verify
        rows = json.loads(
            workspace_cli_run(
                "query",
                sandbox_db,
                "--json-query",
                json.dumps({
                    "q/from": sandbox_db,
                    "q/select": {"p": ["Sandbox/Priority", "enum/name"]},
                    "q/where": ["=", ["fibery/id"], "$id"],
                    "q/limit": 1,
                }),
                "--params",
                json.dumps({"$id": entity_id}),
            ).stdout
        )
        assert rows[0]["p"] == "High"

        # Unlink
        workspace_cli_run("unlink", entity_id, "--type", sandbox_db, "--field", "Sandbox/Priority", "--by-name", "High")
    finally:
        workspace_cli_run("delete", entity_id, "--type", sandbox_db, "--yes", check=False)
