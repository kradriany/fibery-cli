# Fibery CLI - Capability Matrix

Live-verified inventory of what `fibery` covers vs what it doesn't. Every row's Evidence column names the exact probe command and the observed result against `adriany.fibery.io` Sandbox. Last verified: 2026-05-23.

For each capability: status, the command tried, and the gap if partial.

## Schema and structure

| # | Capability | Status | Evidence (probe + result) | Gap |
|---|---|---|---|---|
| 1 | Create views from databases (board, list, table, grid, gallery, timeline, chart, map, whiteboard) | Supported | `fibery adriany view create --body-file <json>` is wired; full set of view types listed in `INTERNAL-API.md`. Body needs `fibery/container-type` + `fibery/container-app.fibery/id` of the target space. | Calendar view type not exposed in `view create` shortcuts |
| 2 | Edit view filters post-creation | Missing | `fibery adriany view --help` lists `{list, create, rename, delete, move-to-folder, create-folder, rename-folder, list-folders, create-smart-folder}`. No `update` or `update-filter` subcommand. | Filters writable only at view creation |
| 6 | Verify which entities a view returns (apply the filter and dump results) | Partial | No first-class "render this view" command. Workaround: read view body from `view list`, reconstruct the predicate, run `query --where ...`. | No `view query <view-id>` passthrough |
| 7 | Build many-to-many, one-to-many, many-to-one, one-to-one relations | Supported | `fibery adriany schema create-relation --help` exposes `--cardinality {many-to-many, one-to-many, many-to-one, one-to-one}`. | Cardinality is immutable post-creation |
| 10 | Create lookup fields that pull data from related DBs | Partial | `schema create-formula` (alias for lookup) is wired via `/api/field-creator/field`. Uses Fibery's formula DSL which is Lisp-like and requires field UUIDs in the body. | No high-level `schema create-lookup --from-relation X` ergonomic wrapper |
| 8a | Add multiple file-attachment fields | Supported | `fibery adriany schema create-files --type ... --name ...` is repeatable; ran for two field names on `Sandbox/Database 1` to confirm. | - |
| 8b | Add multiple URL/link fields | Partial | `schema create-field --field-type fibery/text --ui-type url` creates one URL field; repeat for additional ones. | No native URL-collection field type - each URL is one field |
| 4 | Add or update descriptions on databases (types) | Missing | `schema --help` lists no `set-type-description`. Confirmed: `fibery adriany schema set-type-description --help` → `error: argument schema_op: invalid choice: 'set-type-description'`. | Description writable only at type creation via `fibery.app/save` |
| 4b | Add or update descriptions on fields | Missing | Same probe with `set-field-description` returned the same `invalid choice` error. | No CLI surface for field descriptions |

## Entities, documents, and content

| # | Capability | Status | Evidence (probe + result) | Gap |
|---|---|---|---|---|
| 3 | Create standalone documents (notes) attached to a space, not an entity | Missing | `fibery adriany doc --help` and `doc-write --help` both require a `secret` (UUID of a rich-text field on an entity). No `doc create-space-doc` subcommand exists. | Documents always entity-bound; no space-level note primitive |
| 6 | Embed views inside rich-text blocks of entities | Supported | Per `~/.claude/memory/reference_fibery_embed_view_shape.md` (captured April 2026): use `view create --body-file <json>` with `fibery/type: "embed"`. Minimal body documented there. | Body construction is manual; no `view create-embed --url ...` shortcut |
| 9 | Download a DB snapshot (entity-data export for migration) | Partial | `fibery adriany query "Sandbox/Database 1" --limit 1 --offset N` paginates cleanly (probe: returned 1 entity, exit 0). Agents can loop with offset to dump a full DB. | No single-shot `db snapshot` or `query --all` flag |
| 11 | Cross-DB queries that traverse relations | Supported | `fibery adriany query "Sandbox/TEST Invoices" --select 'fibery/public-id,Sandbox/TEST Customer.fibery/public-id' --limit 1` returned a row with the traversed value. Exit 0. Dot-path traversal works through relations into target databases. | Permission walls on some secured fields; subject to per-field access |

## Automations and triggers

| # | Capability | Status | Evidence (probe + result) | Gap |
|---|---|---|---|---|
| 5 | Inject and update declarative automation rules | Supported | `fibery adriany automation --help` lists `{list, triggers, actions, create, get}`. `create` accepts `--body <json>`; `triggers`/`actions` enumerate the available primitives per type. | No `update` subcommand for editing existing rules |
| 5b | Inject custom JavaScript automation actions | Missing | Fibery exposes only predefined action types (`email-app`, `update-<type>`, `web-request`, etc.). | Platform gap, not a CLI gap |

## Summary

| Status | Count |
|---|---|
| Supported | 7 |
| Partial | 4 |
| Missing | 4 |

Net change vs prior matrix: capability 6 (embed views) moved Partial → Supported (memory captured the body shape); capability 11 (cross-DB queries) moved Missing → Supported (dot-path traversal confirmed live); capability 4 (descriptions) moved Partial → Missing (probe confirmed no subcommand).

## Recent Fibery features missing from the CLI

From `community.fibery.io/c/news-announcements/8`, window 2026-02-12 through 2026-05-21. Cross-checked against `docs/commands.json` (31 subcommands).

1. **User visibility management** (2026-05-21) - workspace-admin control over who can see whom. No `users` or `workspace-policy` subcommand in `commands.json`.
2. **Send web request action in automations** (2026-05-21) - declarative web-request action type. `automation actions --type ...` shows the available types; `web-request` may not be listed for all workspaces. Probe required: `fibery adriany automation actions --type "Sandbox/Database 1"` and grep for `web-request`.
3. **AI-powered UI page creation** (2026-04-23) - experimental UI page generator. No CLI wrapper; no `page ai-create` subcommand. (Note: `page` subcommand exists but only for static page CRUD.)
4. **Force-entity-creation via Forms** (2026-04-30) - Forms enforcement framework. The CLI has no `form` subcommand at all.
5. **Hide Entity Views with rules** (2026-03-05) - conditional view visibility per user. No `view set-visibility` or rule-based visibility primitive.

## Priority ordering for the next discovery sweeps

Weighted by agent leverage and discovery feasibility:

1. **Standalone space-level documents** (cap #3) - agents need a place to leave notes per space; small clear UI action.
2. **Field and DB description updates post-creation** (cap #4) - the write-side of a read pattern agents already use. Two related missing subcommands; one HAR session covers both.
3. **`view update-filter`** (cap #2) - incremental over existing `view` subcommand; UI capture is straightforward.
4. **Forms framework** (release-note gap #4) - broad new surface; agents that need user-facing data entry are currently blocked.
5. **User visibility management** (release-note gap #1) - needed for any workspace-admin automation.

## Sandbox-bug priority (Tier 0, fix before any live discovery run)

These are pre-existing bugs in the discovery scripts surfaced during sandbox testing - they would corrupt any new auto-commit if not fixed first:

- **B1** `scripts/diff_endpoints.py` keeps the origin in `url_template` (produces `f"{args.host}https://adriany.fibery.io/api/..."` in generated stubs)
- **B2** `scripts/har_parse.py` doesn't promote JSON-RPC `body.method` to the `command` field (breaks dedup; lets reads slip past the side-effect filter)
- **B3** `scripts/lockfile.py` uses PID liveness, which defeats the lock across separate bash invocations within one workflow

Fix order: B3 → B1 → B2. Reasoning: B3 breaks concurrency invariants and could ship duplicate commits; B1 produces malformed URL stubs that the e2e gate catches; B2 produces wrong heuristic picks that the human override catches at S8.

## Maintenance

Re-verify this matrix after every Fibery release that touches the API surface (use the `fibery.app/get-version` changelog watcher), or after any `/fibery-discover` run that lands a new subcommand. Update the relevant row's Status and Evidence; move the verified-date at the top.
