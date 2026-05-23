# Fibery CLI — Capability Matrix

A point-in-time inventory of what `fibery` covers vs what it doesn't. Maintained as the auto-extension loop fills gaps. Last reviewed: 2026-05-23.

For each capability: status, evidence pointer, and the specific gap if partial.

## Schema and structure

| Capability | Status | Evidence | Gap |
|---|---|---|---|
| Create views from databases (board, list, table, grid, gallery, timeline, chart, map, whiteboard) | Supported | `view create`; `INTERNAL-API.md` `create-views` via `/api/views/json-rpc` | Calendar view type not exposed |
| Edit view filters post-creation | Partial | `view ...` family; filters only writable at creation via `items[0].filter` | No `view update-filter` subcommand; cannot mutate filters on an existing view |
| Verify which entities a view returns (apply the filter and dump results) | Partial | `query` with `--where` re-implements the filter manually | No "render this view's filter" passthrough; agents have to re-translate UI filters into `--where` |
| Build many-to-many, one-to-many, many-to-one, one-to-one relations | Supported | `schema create-relation --cardinality ...` | Cardinality is immutable after creation |
| Create lookup fields from a related DB | Partial | `schema create-formula` via `/api/field-creator/field`; formula DSL is Lisp-like | Requires manual field UUID lookup; no high-level `schema create-lookup` wrapper |
| Add multiple file-attachment fields | Partial | `schema create-files` creates one collection | No first-class "multiple file sections" — needs repeated invocations and clear naming |
| Add multiple link/URL-collection fields | Partial | URL stored as `fibery/text --ui-type url` (single value) | No URL-collection field type |
| Add or update descriptions on databases (types) | Partial | `fibery/description` writable at space creation via `fibery.app/save` | No `schema set-type-description` for post-creation updates |
| Add or update descriptions on fields | Partial | `set-field-meta` covers some keys | No clear `--description` flag wired to a documented meta key |

## Entities, documents, and content

| Capability | Status | Evidence | Gap |
|---|---|---|---|
| Standalone documents (notes) attached to a space, not an entity | Missing | `doc`/`doc-write` only target rich-text fields on entities | No `doc create-space-doc` subcommand; documents are always entity-bound |
| Embed views inside rich-text blocks of entities | Partial | ProseMirror JSON supports entity-embed nodes; view-embed announced May 2026 | No CLI command demonstrated; ship as a discovery target |
| Download a DB snapshot (entity-data export for migration) | Missing | `file download-all` downloads file attachments, not entity data | No `query --export-all` or `db snapshot` command |
| Cross-DB rich views (queries that traverse relations across DBs) | Missing | Sub-query supported only within a single type; permission walls block dot-path traversal | No multi-DB join/query builder; primary unmet need for analytics views |

## Automations and triggers

| Capability | Status | Evidence | Gap |
|---|---|---|---|
| Inject and update declarative automation rules (Fibery's built-in actions) | Supported | `automation create/get --body <json>`; `/api/automations/auto-rules/for-type/{id}` | — |
| Inject custom JavaScript automation actions | Missing | Fibery exposes only predefined action types (`email-app`, `update-<type>`, etc.) | Custom JS execution is a Fibery platform gap, not a CLI gap |
| Buttons | Supported | `button ...` | — |

## Recent Fibery features missing from the CLI

From Fibery's public release notes (Nov 2025 – May 2026). Each is a candidate for the next discovery sweep.

1. **Embed View blocks in rich text** (May 2026) — announced as shipped in the UI; no CLI endpoint identified
2. **AI-powered UI page creation** (April 2026) — experimental UI feature for auto-generated entity layouts; no CLI wrapper
3. **Automatic entity linking with expanded operators** (April 2026) — extended relation-linking logic beyond what `link/unlink` exposes
4. **Validation rules framework** (early 2026) — field-level validation rules; no `schema create-validation-rule` subcommand
5. **User visibility management** (May 2026) — workspace-admin controls over user visibility; no CLI command

## Priority ordering for the discovery loop

Recommended order for the next live `/fibery-discover` runs, weighted by agent leverage and discovery difficulty:

1. **Standalone space-level documents** (capability gap #3) — smallest, clearest UI action; agents need a place to leave notes per space
2. **Field and DB description updates post-creation** (#4) — write side of the read pattern agents already use
3. **DB snapshot export** (#9) — unblocks migrations and verification flows
4. **Embed View blocks in rich text** (release-note #1) — May 2026 feature, fresh HAR likely available
5. **Cross-DB query traversal** (#11) — likely needs UI-layer reverse engineering to bypass the documented permission walls

## Maintenance

This matrix should be updated after every discovery sweep. Items that get wired move to "Supported" with a pointer to the new subcommand; new gaps surfaced by Fibery releases get appended at the bottom of the recent-features list.
