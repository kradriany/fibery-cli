"""Destructive sandbox tests against a configured sandbox space.

Run: PYTEST_FIBERY_SANDBOX=1 uv run --with pytest --with httpx pytest test_sandbox.py -v

SKIPPED by default (via conftest.py) unless PYTEST_FIBERY_SANDBOX=1. These
tests write to the configured sandbox space. They clean up after themselves,
but a failure mid-test may leave stray entities or types.

All writes target the Sandbox space to prevent production data damage.
"""
from __future__ import annotations

import json
import time
import uuid

import pytest


pytestmark = pytest.mark.sandbox


def _cli_json(workspace_cli_run, *args):
    return json.loads(workspace_cli_run(*args).stdout)


class TestEntityCrud:
    """Create → query → update → delete cycle on Sandbox/Database 1."""

    def test_full_entity_lifecycle(self, workspace_cli_run, live_test_settings):
        marker = f"pytest-cli-{uuid.uuid4().hex[:8]}"
        sandbox_db = live_test_settings["sandbox_db"]

        # Create
        created = _cli_json(workspace_cli_run, "create", sandbox_db,
                            "--fields", json.dumps({"Sandbox/Name": marker}))
        assert created["Sandbox/Name"] == marker
        entity_id = created["fibery/id"]
        assert entity_id

        try:
            # Query back
            queried = _cli_json(workspace_cli_run, "query", sandbox_db,
                                "--where", f"Sandbox/Name={marker}",
                                "--select", "Sandbox/Name,fibery/id")
            assert len(queried) == 1
            assert queried[0]["fibery/id"] == entity_id

            # Update
            new_marker = marker + "-updated"
            _cli_json(workspace_cli_run, "update", entity_id,
                      "--type", sandbox_db,
                      "--fields", json.dumps({"Sandbox/Name": new_marker}))

            requeried = _cli_json(workspace_cli_run, "query", sandbox_db,
                                  "--where", f"fibery/id={entity_id}",
                                  "--select", "Sandbox/Name")
            assert len(requeried) == 1
            assert requeried[0]["Sandbox/Name"] == new_marker
        finally:
            # Cleanup
            workspace_cli_run("delete", entity_id, "--type", sandbox_db, "--yes", check=False)

        # Verify deletion
        after = _cli_json(workspace_cli_run, "query", sandbox_db,
                          "--where", f"fibery/id={entity_id}")
        assert len(after) == 0


class TestDocAndComments:
    """Rich-text doc round-trip and comments traversal."""

    def test_doc_write_and_read(self, workspace_cli_run, live_test_settings):
        marker = f"pytest-doc-{uuid.uuid4().hex[:8]}"
        sandbox_db = live_test_settings["sandbox_db"]
        created = _cli_json(workspace_cli_run, "create", sandbox_db,
                            "--fields", json.dumps({"Sandbox/Name": marker}))
        entity_id = created["fibery/id"]
        try:
            # Fetch the description secret
            rows = _cli_json(workspace_cli_run, "query", sandbox_db,
                             "--json-query", json.dumps({
                                 "q/from": sandbox_db,
                                 "q/select": {
                                     "fibery/id": ["fibery/id"],
                                     "doc-secret": ["Sandbox/Description",
                                                    "Collaboration~Documents/secret"],
                                 },
                                 "q/where": ["=", ["fibery/id"], "$id"],
                                 "q/limit": 1,
                             }),
                             "--params", json.dumps({"$id": entity_id}))
            assert len(rows) == 1
            secret = rows[0].get("doc-secret")
            assert secret, "Fibery should auto-generate a document secret for rich-text fields"

            # Write content
            content = "Hello from pytest sandbox"
            write_result = _cli_json(workspace_cli_run, "doc-write", secret, "--content", content)
            assert write_result["written"] is True

            # Read back
            read_result = _cli_json(workspace_cli_run, "doc", secret, "--format", "md")
            assert read_result["content"] == content
        finally:
            workspace_cli_run("delete", entity_id, "--type", sandbox_db, "--yes", check=False)


class TestSchemaManipulation:
    """Full schema manipulation cycle: create-type, create-field, create-relation,
    rename, set-meta, delete. All confined to Sandbox space."""

    def test_type_lifecycle(self, workspace_cli_run):
        type_name = f"PytestType{uuid.uuid4().hex[:6]}"
        full_name = f"Sandbox/{type_name}"

        # Create type
        result = _cli_json(workspace_cli_run, "schema", "create-type",
                           "--space", "Sandbox", "--name", type_name)
        assert result["created"] == full_name

        try:
            # Add primitive fields
            for fname, ftype in [
                ("Sandbox/count", "fibery/int"),
                ("Sandbox/done", "fibery/bool"),
                ("Sandbox/notes", "fibery/text"),
            ]:
                r = _cli_json(workspace_cli_run, "schema", "create-field",
                              "--type", full_name, "--name", fname,
                              "--field-type", ftype)
                assert r["created"] == fname

            # Verify
            described = _cli_json(workspace_cli_run, "describe", full_name)
            field_names = {f["name"] for f in described["fields"]}
            assert "Sandbox/count" in field_names
            assert "Sandbox/done" in field_names
            assert "Sandbox/notes" in field_names

            # Rename field
            _cli_json(workspace_cli_run, "schema", "rename-field",
                      "--type", full_name,
                      "Sandbox/count", "Sandbox/quantity")
            re_described = _cli_json(workspace_cli_run, "describe", full_name)
            names = {f["name"] for f in re_described["fields"]}
            assert "Sandbox/quantity" in names
            assert "Sandbox/count" not in names

            # Set field meta (default value)
            _cli_json(workspace_cli_run, "schema", "set-field-meta",
                      "--type", full_name, "--name", "Sandbox/done",
                      "--meta", json.dumps({"fibery/default-value": True}))

            # Delete a field
            _cli_json(workspace_cli_run, "schema", "delete-field",
                      "--type", full_name, "--name", "Sandbox/notes", "--yes")
            after_del = _cli_json(workspace_cli_run, "describe", full_name)
            after_names = {f["name"] for f in after_del["fields"]}
            assert "Sandbox/notes" not in after_names

            # Rename the type
            renamed_name = f"Sandbox/{type_name}Renamed"
            _cli_json(workspace_cli_run, "schema", "rename-type", full_name, renamed_name)
            full_name = renamed_name
        finally:
            # Cleanup
            workspace_cli_run("schema", "delete-type", full_name, "--delete-entities", "--yes", check=False)


class TestBatchAndDiff:
    def test_schema_diff_detects_drift(self, workspace_cli_run, tmp_path):
        # Dump live schema, then modify the target and diff
        live = _cli_json(workspace_cli_run, "schema", "dump")
        # Build a target that removes one type so diff has something to report
        target_types = [t for t in live["fibery/types"] if not t.get("fibery/meta", {}).get("fibery/domain?")]
        target_file = tmp_path / "target.json"
        target_file.write_text(json.dumps({"fibery/types": target_types}))
        diff = _cli_json(workspace_cli_run, "schema", "diff", "--file", str(target_file))
        assert len(diff["types_only_live"]) > 0
