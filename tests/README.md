# Tests

Test suite for the repo-local `fibery` CLI.

## Running

```bash
cd tests

# Fast, no network
uv run --with pytest --with httpx pytest test_unit.py -v

# Live workspace
export FIBERY_TEST_WORKSPACE="myworkspace"
export FIBERY_TEST_WORKSPACE_HOST="myworkspace.fibery.io"
export FIBERY_TEST_TOKEN="YOUR_TOKEN"
uv run --with pytest --with httpx pytest test_integration.py -v

# Parity vs captured MCP fixtures
uv run --with pytest --with httpx pytest test_parity.py -v

# Destructive sandbox writes
export FIBERY_TEST_SANDBOX_SPACE="Sandbox"
export FIBERY_TEST_SANDBOX_DB="Sandbox/Database 1"
PYTEST_FIBERY_SANDBOX=1 uv run --with pytest --with httpx pytest test_sandbox.py -v
```

## Files

| File | Risk | What it tests | Runtime |
|---|---|---|---|
| `test_unit.py` | None | Helper functions, handler logic, error mapping. All HTTP mocked. | ~0.05s |
| `test_integration.py` | Low | Subprocess execution against a live workspace. Mostly read-only, with a few temp entity create/delete canaries. | ~10s |
| `test_parity.py` | Low | CLI output vs captured MCP fixtures. | ~5s |
| `test_sandbox.py` | High | Entity CRUD, rich-text writes, and schema mutations in a sandbox database. | ~15s |

## Requirements

- `uv`
- `pytest`
- `httpx`
- Live tests: a Fibery workspace, host, and token
- Sandbox tests: an isolated sandbox space and database you can write to

The `conftest.py` fixtures read these env vars:

- `FIBERY_TEST_WORKSPACE`
- `FIBERY_TEST_WORKSPACE_HOST`
- `FIBERY_TEST_TOKEN`
- `FIBERY_TEST_SANDBOX_SPACE`
- `FIBERY_TEST_SANDBOX_DB`
- `FIBERY_TEST_TASK_TYPE`

If `FIBERY_TEST_WORKSPACE_HOST` is omitted, the tests use your local CLI config.

## Fixtures

`fixtures/mcp_*.{txt,json}` capture historical MCP output used for parity checks. If the Fibery schema you test against changes enough to invalidate those snapshots, regenerate the fixtures from the same MCP calls and update the expected output.
