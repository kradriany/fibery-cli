# fibery-cli

Command-line access to [Fibery](https://fibery.io) workspaces.

This project wraps the official HTTP API plus several UI-discovered endpoints for schema work, spaces, views, documents, files, automations, and more. It ships as a single Python script and runs through `uv`.

## Quick Start

```bash
# Install
cp fibery ~/bin/fibery && chmod +x ~/bin/fibery

# Option 1: store a workspace alias in config
mkdir -p ~/.config/fibery-cli
cat > ~/.config/fibery-cli/config.json <<'JSON'
{
  "workspaces": {
    "myworkspace": {
      "host": "myworkspace.fibery.io",
      "keychain_account": "fibery-myworkspace"
    }
  }
}
JSON

# macOS Keychain example
security add-generic-password -U -a fibery-myworkspace -s mcp-credentials -w "YOUR_TOKEN"

# Test it
fibery myworkspace dbs
fibery myworkspace query "Space/Type" --limit 5
```

You can skip config and Keychain if you want direct auth:

```bash
export FIBERY_TOKEN="YOUR_TOKEN"
fibery myworkspace --workspace-host myworkspace.fibery.io dbs
```

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Fibery API token

macOS Keychain is optional. On Linux and Windows, use `--token` or `FIBERY_TOKEN`.

## Configuration

Default config path:

- macOS and Linux: `~/.config/fibery-cli/config.json`
- Windows: `%APPDATA%\fibery-cli\config.json`

You can override that with `FIBERY_CONFIG_FILE`.

Supported config format:

```json
{
  "workspaces": {
    "myworkspace": {
      "host": "myworkspace.fibery.io",
      "keychain_account": "fibery-myworkspace"
    },
    "staging": {
      "host": "staging.fibery.io"
    }
  }
}
```

Notes:

- `host` is required for each workspace alias.
- `keychain_account` is optional. If omitted, the CLI defaults to `fibery-<workspace>`.
- Legacy top-level maps `workspace_hosts` and `keychain_accounts` are also supported.

## Credentials

The CLI resolves credentials in this order:

1. `--token`
2. `FIBERY_TOKEN`
3. macOS Keychain lookup

Examples:

```bash
# Direct token
fibery myworkspace --workspace-host myworkspace.fibery.io --token "YOUR_TOKEN" dbs

# Environment variable
export FIBERY_TOKEN="YOUR_TOKEN"
fibery myworkspace --workspace-host myworkspace.fibery.io dbs

# macOS Keychain
security add-generic-password -U -a fibery-myworkspace -s mcp-credentials -w "YOUR_TOKEN"
fibery myworkspace dbs
```

Linux and Windows options:

- Keep the token in your shell profile or a `.env` file and export `FIBERY_TOKEN` before running the CLI.
- Use a secret manager such as 1Password, Bitwarden, or GitHub Actions secrets and inject `FIBERY_TOKEN` at runtime.
- Pass `--token` from a wrapper script if you do not want the token stored on disk.

## Common Commands

| Category | Commands | Highlights |
|---|---|---|
| Entity CRUD | `query`, `create`, `update`, `delete`, `batch-create`, `batch-delete` | `--where`, `--json-query`, typed filters |
| Relations | `link`, `unlink` | `--by-name` resolution via schema |
| Schema | `schema ...` | types, fields, enums, relations, workflows, formulas |
| Spaces | `space create`, `space list`, `space update`, `space delete` | includes undocumented space lifecycle calls |
| Documents | `doc`, `doc-write`, `docs-batch`, `docs-sync` | batch fetch, sync, rich-text writes |
| Comments | `comments`, `comment-add` | threaded reads and writes |
| Files | `file upload`, `file download`, `file attach`, `file download-all` | upload plus attach flows |
| Views | `view ...` | view and folder management |
| Automations | `automation ...`, `button ...` | rules, buttons, actions |
| Other | `graphql`, `webhook`, `event-seq` | passthrough and sync helpers |

See [docs/USAGE.md](docs/USAGE.md) for the full command reference, [docs/AGENTS.md](docs/AGENTS.md) for AI-agent integration guidance, and [docs/CAPABILITIES.md](docs/CAPABILITIES.md) for a current coverage matrix.

## Undocumented Endpoints

These were found by capturing Fibery UI traffic in Chrome DevTools HAR files and replaying the requests with token auth.

| Endpoint | What it does |
|---|---|
| `fibery.app/save` + `fibery.app/install` | Create a new space |
| `fibery.app/delete` | Delete a space |
| `PUT /api/documents/{secret}` | Write rich-text content |
| `POST /api/documents/commands` `get-documents` | Batch-fetch multiple docs |
| `schema.enum/create` | Create enum types |
| `workflow/install` | Install workflow states |
| `workflow/update-state-type` | Change workflow state category |
| `schema.field/delete-meta` | Remove field metadata |
| `fibery.entity.batch/create` | Create many entities |
| `fibery.entity.batch/delete` | Delete many entities |
| `POST /api/field-creator/field` | Create formula and lookup fields |
| `POST /api/field-creator/field/duplicate` | Duplicate a field |
| `create-folders` | Create view folders |
| `create-smart-folders` | Create smart folders |
| `fibery.app/update` | Update space color and icon |

Reference docs:

- [docs/INTERNAL-API.md](docs/INTERNAL-API.md)
- [docs/HAR-CLI-BUILDER.md](docs/HAR-CLI-BUILDER.md)

## Auto-Extension Loop

This CLI was bootstrapped by reverse-engineering Fibery's UI traffic — see [docs/HAR-CLI-BUILDER.md](docs/HAR-CLI-BUILDER.md). The same loop can be automated: capture the live UI for a missing action, diff the network log against known endpoints, generate a new subcommand, verify, commit. Any tooling that follows the contract below can contribute to this repo.

**Recommended trigger conditions:**

- A user or agent explicitly requests a missing capability
- A `fibery` invocation exits with `method not found`, `unknown command`, or a 404 on a Fibery URL
- A scheduled diff of `fibery.app/get-version` reports a new build hash

**Recommended safety gates before pushing:**

1. Network diff yields ≥1 endpoint not already in [docs/INTERNAL-API.md](docs/INTERNAL-API.md)
2. Token replay returns 2xx for every wired endpoint
3. `ast.parse(fibery)` is clean
4. `uv run --script fibery --help` exits 0 and lists the new subcommand
5. Independent code review (human or LLM) returns no blocking findings
6. New subcommand runs against a sandbox space and returns 2xx with non-empty body
7. `git diff --stat` touches only: `fibery`, `docs/INTERNAL-API.md`, `docs/USAGE.md`, `CHANGELOG.md`
8. Working tree was clean before the run

**Tagging convention:** auto-generated commits use the tag `auto/discover/<YYYYMMDD-HHMMSS>`. To revert: `git revert <tag> && git push`.

**Sandbox convention:** use a dedicated workspace space named `Sandbox` and prefix test entities with `discover-<YYYYMMDD-HHMM>-` to avoid collisions between runs.

A reference implementation as a Claude Code skill is available; the loop is tool-agnostic and can be implemented in any framework that can drive a browser (Playwright, Puppeteer, Selenium, Chrome DevTools Protocol directly) and observe the network log.

### Known capability gaps

Items below are not yet wired. They're prioritized targets for the next round of UI-driven discovery:

- Standalone space-level documents (not bound to entities) — useful as freeform notes for human or agent consumers
- DB and field description updates after type creation (current API only writes descriptions at type creation)
- DB snapshot export (entity-data dump for migrations; `file download-all` covers attachments only)
- Cross-DB queries that traverse relations (current sub-query is single-type)
- Embed-view blocks in rich-text (announced in Fibery's May 2026 release notes)
- Validation rules, automatic-linking operators, AI page creation, user-visibility management (Nov 2025 – May 2026 release-note features)

## Testing

```bash
cd tests

# Fast, no network
uv run --with pytest --with httpx pytest test_unit.py -v

# Live workspace
export FIBERY_TEST_WORKSPACE="myworkspace"
export FIBERY_TEST_WORKSPACE_HOST="myworkspace.fibery.io"
export FIBERY_TEST_TOKEN="YOUR_TOKEN"
uv run --with pytest --with httpx pytest test_integration.py -v

# Sandbox writes
export FIBERY_TEST_SANDBOX_SPACE="Sandbox"
export FIBERY_TEST_SANDBOX_DB="Sandbox/Database 1"
PYTEST_FIBERY_SANDBOX=1 uv run --with pytest --with httpx pytest test_sandbox.py -v
```

The test matrix is documented in [tests/README.md](tests/README.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the HAR capture workflow, test expectations, and release process.

## License

MIT
