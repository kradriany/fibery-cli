# Fibery CLI

`fibery` is a single-file Fibery API client. It covers entity CRUD, schema manipulation, space lifecycle, views, folders, documents, comments, files, automations, buttons, GraphQL, webhooks, and incremental sync.

Built from official docs + 15+ undocumented endpoints discovered via Chrome DevTools HAR capture. See `docs/INTERNAL-API.md` for the full internal API reference and `docs/HAR-CLI-BUILDER.md` for the discovery methodology.

## Workspace Routing

```bash
fibery <workspace> <command> [args]
```

The `workspace` argument is an alias from your config file. You can also bypass config with `--workspace-host`.

Example config:

```json
{
  "workspaces": {
    "myworkspace": {
      "host": "myworkspace.fibery.io",
      "keychain_account": "fibery-myworkspace"
    }
  }
}
```

## Output Formats

```bash
fibery myworkspace -o json dbs      # pretty JSON (default)
fibery myworkspace -o raw dbs       # compact JSON
fibery myworkspace -o table dbs     # text table
```

---

## Command Reference

### Entity CRUD

```bash
# Query
fibery myworkspace query "Task Management/Task" --limit 5
fibery myworkspace query "Task Management/Task" --where "Sandbox/Name=hello" --select "Sandbox/Name,fibery/public-id"
fibery myworkspace query "Task Management/Task" --where "priority:int>5" --order-by "fibery/creation-date" --order-desc
fibery myworkspace query "Task Management/Task" --json-query '{"q/from":"...","q/select":{...}}' --params '{"$key":"val"}'

# Create / Update / Delete
fibery myworkspace create "Space/Type" --fields '{"Space/Name":"hello"}'
fibery myworkspace update <uuid> --type "Space/Type" --fields '{"Space/Name":"updated"}'
fibery myworkspace delete <uuid> --type "Space/Type" --yes

# Batch
fibery myworkspace batch-create "Space/Type" --file entities.json    # uniform field sets required
fibery myworkspace batch-delete --type "Space/Type" --ids "uuid1,uuid2" --yes
```

### Relations (link / unlink)

```bash
# By UUID
fibery myworkspace link <entity-id> --type "Space/Type" --field "Space/Tags" --items "uuid1,uuid2"
fibery myworkspace unlink <entity-id> --type "Space/Type" --field "Space/Tags" --items "uuid1"

# By name (auto-resolves via schema lookup - works for enums, relations, people)
fibery myworkspace link <entity-id> --type "Space/Type" --field "Space/Status" --by-name "Active"
fibery myworkspace link <entity-id> --type "Space/Type" --field "Space/Tags" --by-name "VIP,Champion"

# Assign people
fibery myworkspace link <entity-id> --type "Space/Type" --field "Space/Assigned To" --by-name "Workspace Admin"

# Set workflow state (use update, not link)
fibery myworkspace update <uuid> --type "Space/Type" --fields '{"workflow/state":{"fibery/id":"<state-uuid>"}}'
```

### Schema

```bash
# Inspect
fibery myworkspace dbs                                    # list domain databases
fibery myworkspace dbs --all                              # include system/enum types
fibery myworkspace describe "Space/Type"                  # fields + meta
fibery myworkspace schema dump > schema.json              # full workspace schema

# Create types
fibery myworkspace schema create-type --space Sandbox --name MyType --color "#F7D130"
fibery myworkspace schema create-type --space Sandbox --name Thing \
  --with-mixins "fibery/rank-mixin,Collaboration~Documents/ReferencesMixin,comments/comments-mixin"

# Create fields - all 20 Fibery field types
fibery myworkspace schema create-field --type "Space/Type" --name "Space/Count" --field-type fibery/int
fibery myworkspace schema create-field --type "Space/Type" --name "Space/Email" --field-type fibery/text --ui-type email
fibery myworkspace schema create-field --type "Space/Type" --name "Space/Website" --field-type fibery/text --ui-type url
fibery myworkspace schema create-field --type "Space/Type" --name "Space/Phone" --field-type fibery/text --ui-type phone
fibery myworkspace schema create-field --type "Space/Type" --name "Space/Team" --field-type fibery/user --ui-type people
fibery myworkspace schema create-field --type "Space/Type" --name "Space/Revenue" --field-type fibery/decimal --money
fibery myworkspace schema create-field --type "Space/Type" --name "Space/Revenue" --field-type fibery/decimal --money --currency EUR
fibery myworkspace schema create-field --type "Space/Type" --name "Space/Rate" --field-type fibery/decimal --percent
fibery myworkspace schema create-field --type "Space/Type" --name "Space/Score" --field-type fibery/int --precision 0
fibery myworkspace schema create-field --type "Space/Type" --name "Space/Location" --field-type fibery/location
fibery myworkspace schema create-field --type "Space/Type" --name "Space/Start" --field-type fibery/date-time
fibery myworkspace schema create-field --type "Space/Type" --name "Space/Period" --field-type fibery/date-range

# Enum / single-select / multi-select
fibery myworkspace schema create-enum --type "Space/Type" --name "Space/Status" --options "Open,In Progress,Done"
fibery myworkspace schema create-enum --type "Space/Type" --name "Space/Tags" --options "A,B,C" --multi

# Rich-text and files
fibery myworkspace schema create-rich-text --type "Space/Type" --name "Space/Description"
fibery myworkspace schema create-files --type "Space/Type" --name "Space/Attachments"

# Relations
fibery myworkspace schema create-relation --from-type "Space/A" --to-type "Space/B" \
  --name-forward "Space/related" --name-back "Space/reverse" --cardinality many-to-many
# Cardinalities: many-to-many, one-to-many, many-to-one, one-to-one

# Workflow states
fibery myworkspace schema create-workflow --type "Space/Type" \
  --states "To Do:todo|In Progress:started|Done:done|Cancelled:finished"
# Categories: todo (Not started), started (Started), done/finished (Finished)

# Formula / lookup (via field-creator REST endpoint)
fibery myworkspace schema create-formula --body '{"fibery/holder-type":"Space/Type",...}'

# Modify
fibery myworkspace schema rename-type "Space/Old" "Space/New"          # also moves between spaces
fibery myworkspace schema rename-field --type "Space/Type" "Space/old" "Space/new"
fibery myworkspace schema set-field-meta --type "Space/Type" --name "Space/Field" --meta '{"key":"value"}'
fibery myworkspace schema delete-field-meta --type "Space/Type" --name "Space/Field" --key "fibery/readonly?"
fibery myworkspace schema reorder-fields --type "Space/Type" --fields "Space/Name,Space/Email,Space/Status"
fibery myworkspace schema convert-field --type "Space/Type" --name "Space/Field" --new-type fibery/int --yes
fibery myworkspace schema install-mixins --type "Space/Type" --mixins "comments/comments-mixin,icon/icon-mixin"

# Delete (destructive)
fibery myworkspace schema delete-field --type "Space/Type" --name "Space/Field" --yes
fibery myworkspace schema delete-type "Space/Type" --delete-entities --yes

# Batch + diff
fibery myworkspace schema batch --file schema-commands.json
fibery myworkspace schema diff --file target-schema.json
```

### Space Management

```bash
fibery myworkspace space list                                      # list all spaces
fibery myworkspace space list --all                                # include system spaces
fibery myworkspace space create "My Space" --color "#F7D130"       # create (undocumented!)
fibery myworkspace space update "My Space" --color "#2196F3" --icon "flask"
fibery myworkspace space delete "My Space" --yes                   # deletes all types + space
```

### Documents (Rich Text)

```bash
# Read
fibery myworkspace doc <secret> --format md                        # markdown (default)
fibery myworkspace doc <secret> --format html
fibery myworkspace doc <secret> --format json                      # ProseMirror JSON
fibery myworkspace doc <secret> --raw-content                      # body only, no envelope

# Write (undocumented PUT endpoint)
fibery myworkspace doc-write <secret> --content "# Hello"
fibery myworkspace doc-write <secret> --content-file body.md
echo "body" | fibery myworkspace doc-write <secret>

# Batch fetch (undocumented get-documents endpoint - single API call, no rate limiting)
fibery myworkspace docs-batch --secrets "secret1,secret2,secret3" --format md
fibery myworkspace docs-batch --secrets-file secrets.txt

# Incremental sync (modification-date cache)
fibery myworkspace docs-sync --type "Space/Type" --field "Space/Description" --cache-dir ~/.fibery-cache/
fibery myworkspace docs-sync --type "Space/Type" --field "Space/Description" --cache-dir ~/.fibery-cache/ --full
```

### Comments

```bash
# Read (requires comments/comments-mixin on the type)
fibery myworkspace comments <entity-id> --type "Space/Type"
fibery myworkspace comments <entity-id> --type "Space/Type" --with-content

# Create
fibery myworkspace comment-add <entity-id> --type "Space/Type" --content "Follow up on this"
fibery myworkspace comment-add <entity-id> --type "Space/Type" --content-file note.md
echo "note" | fibery myworkspace comment-add <entity-id> --type "Space/Type"
```

### Files

```bash
# Upload + download (downloads follow 302 redirects to cloud storage)
fibery myworkspace file upload ./report.pdf
fibery myworkspace file download <secret> --out ./report.pdf
fibery myworkspace file upload-multi --paths "a.pdf,b.pdf,c.pdf"
fibery myworkspace file sign <secret>                              # 60-min signed URL

# Attach to entity (upload + link in one step)
fibery myworkspace file attach --paths "a.pdf,b.pdf" --type "Space/Type" --entity-id <uuid> --field "Space/Files"

# Query + bulk download
fibery myworkspace file list-on --type "Space/Type" --entity-id <uuid> --field "Space/Files"
fibery myworkspace file download-all --type "Space/Type" --entity-id <uuid> --field "Space/Files" --out-dir ./docs/
```

### Views, Folders + Smart Folders

Views need proper meta structure to render. The `items` array in meta must include `query` (data source), `units` (visible columns), and type-specific keys. Views without this crash the Fibery UI.

```bash
# List + query
fibery myworkspace view list
fibery myworkspace view list --space-id <uuid>
fibery myworkspace view list-folders

# Create views (types: grid, board, list, gallery, timeline, chart, map, whiteboard)
# Minimal working view requires: container-app, type, name, and properly structured meta
fibery myworkspace view create --body '<view-json>'

# Rename + delete
fibery myworkspace view rename <view-uuid> --name "New Name"
fibery myworkspace view delete --ids "uuid1,uuid2" --yes

# Folders
fibery myworkspace view create-folder --space-id <uuid> --name "My Folder"
fibery myworkspace view rename-folder <folder-uuid> --name "New Name"
fibery myworkspace view move-to-folder <view-uuid> --folder-id <folder-uuid>

# Smart folders
fibery myworkspace view create-smart-folder --space-id <uuid> --name "My Smart Folder"
```

#### View Meta Structure (critical for working views)

Views crash with `r.filter` error if meta is malformed. Use the correct structure per view type:

**Grid view:**
```json
{
  "fibery/meta": {
    "x": null, "y": null,
    "items": [{
      "query": {"q/from": "<type-uuid>", "q/order-by": [[[" <rank-field-uuid>"], "q/asc"]]},
      "units": [
        {"kind": "field", "type": "title", "checked": true},
        {"kind": "field", "type": "number", "checked": true, "expression": ["<field-uuid>"]},
        {"kind": "field", "type": "text", "checked": true, "expression": ["<field-uuid>"]},
        {"kind": "field", "type": "date", "checked": true, "expression": ["<field-uuid>"]},
        {"kind": "field", "type": "reference", "checked": true, "expression": ["<field-uuid>"]},
        {"kind": "field", "type": "workflow-state", "checked": true, "expression": ["<field-uuid>"]}
      ],
      "filter": null,
      "xExpression": null,
      "yExpression": null
    }]
  }
}
```

**Board view** - same as grid plus `"params": {}, "coverExpression": null`

**List view** - same as grid but uses `"params": {}, "groupBy": null, "groupingExpression": null` instead of x/yExpression

**Unit type mapping** (maps fibery field types to view column types):

| Field type | Unit type |
|---|---|
| `fibery/text` | `text` |
| `fibery/int`, `fibery/decimal` | `number` |
| `fibery/bool` | `bool` |
| `fibery/date`, `fibery/date-time` | `date` |
| `fibery/date-range` | `date-range` |
| `fibery/user` | `people` |
| `fibery/file` | `files` |
| `fibery/location` | `location` |
| `Collaboration~Documents/Document` | `rich-text-snippet` |
| `workflow/state_*` | `workflow-state` |
| Single-select enum | `select` |
| Multi-select enum | `multi-select` |
| Relation (single) | `reference` |
| Relation (collection) | `collection-count` |

#### Folder Assignment

`update-views` sets the folder: `{"fibery/Folder": {"fibery/id": "<folder-uuid>"}}`. Use folder IDs from `create-folders` response or `query-folders` - do NOT use client-generated UUIDs as Fibery may assign different IDs.

#### View Workflow (tested end-to-end)

1. Create folder via `view create-folder`
2. Note the folder ID from the response
3. Create view via `view create` with proper meta/items/units
4. Move to folder via `view move-to-folder` using the response folder ID
5. Verify by querying `view list` and checking `fibery/Folder` is set

### People Fields + Users

```bash
# Create a people field
fibery myworkspace schema create-field --type "Space/Type" --name "Space/Owner" --field-type fibery/user --ui-type people

# List workspace users
fibery myworkspace query "fibery/user" --json-query '{"q/from":"fibery/user","q/select":{"name":["user/name"],"email":["user/email"]},"q/limit":50}'

# Assign a user to a people field
fibery myworkspace link <entity-id> --type "Space/Type" --field "Space/Owner" --items "<user-uuid>"
fibery myworkspace link <entity-id> --type "Space/Type" --field "Space/Owner" --by-name "Workspace Admin"
```

### Workflow State Management

```bash
# Install workflow on a type
fibery myworkspace schema create-workflow --type "Space/Type" \
  --states "Draft:todo|Sent:started|Paid:done|Void:finished"

# Set state on an entity (use update with workflow/state object)
fibery myworkspace update <entity-uuid> --type "Space/Type" \
  --fields '{"workflow/state": {"fibery/id": "<state-uuid>"}}'

# Query state UUIDs
fibery myworkspace query "workflow/state_Space/Type" \
  --json-query '{"q/from":"workflow/state_Space/Type","q/select":{"id":["fibery/id"],"name":["enum/name"]},"q/limit":20}'

# Edit states after creation (rename, reorder, change category)
fibery myworkspace update <state-uuid> --type "workflow/state_Space/Type" \
  --fields '{"enum/name":"New Name","fibery/rank":0}'
# Change state category (Not started/Started/Finished):
# Use workflow/update-state-type command via raw post
```

### Moving Databases Between Spaces

```bash
# rename-type with a different space prefix moves the database
fibery myworkspace schema rename-type "OldSpace/MyType" "NewSpace/MyType"
# Entities, fields, and data travel with it
```

### Number Formatting

```bash
# Money (at creation)
fibery myworkspace schema create-field --type "Space/Type" --name "Space/Revenue" --field-type fibery/decimal --money
fibery myworkspace schema create-field --type "Space/Type" --name "Space/Price" --field-type fibery/decimal --money --currency EUR

# Percentage
fibery myworkspace schema create-field --type "Space/Type" --name "Space/Rate" --field-type fibery/decimal --percent

# Retrofit existing field
fibery myworkspace schema set-field-meta --type "Space/Type" --name "Space/Revenue" \
  --meta '{"ui/number-format":"Money","ui/number-currency-code":"USD","ui/number-precision":2,"ui/number-thousand-separator?":true}'
```

### Automations + Buttons

```bash
fibery myworkspace automation list --type-id <uuid>
fibery myworkspace automation triggers --type-id <uuid>
fibery myworkspace automation actions --type-id <uuid>
fibery myworkspace automation create --type-id <uuid> --body '{"enabled":true,"name":"Rule",...}'
fibery myworkspace automation get <rule-id>
fibery myworkspace button list --type-id <uuid>
fibery myworkspace button actions --type-id <uuid>
fibery myworkspace button create --type-id <uuid> --body '{"enabled":true,"name":"Button",...}'
```

### Other

```bash
fibery myworkspace date                                            # workspace info + ISO date
fibery myworkspace event-seq                                       # event sequence ID for sync
fibery myworkspace graphql "Space" --query '{ findTypes(limit:5) { name } }'
fibery myworkspace webhook list
fibery myworkspace webhook create --body '{"url":"...","events":[...]}'
```

---

## Type Hints on --where

Default is string. Add `:int`, `:float`, `:bool` to coerce:

```bash
--where "priority:int>5"
--where "done:bool=true"
--where "fibery/public-id=3"      # string (default, no coercion)
```

## Available Field Types

| UI Name | --field-type | Shorthand |
|---|---|---|
| Number (int) | `fibery/int` | `--money`, `--percent`, `--precision` |
| Number (decimal) | `fibery/decimal` | `--money --currency USD` |
| Text | `fibery/text` | |
| URL | `fibery/text` | `--ui-type url` |
| Email | `fibery/text` | `--ui-type email` |
| Phone | `fibery/text` | `--ui-type phone` |
| People | `fibery/user` | `--ui-type people` |
| Checkbox | `fibery/bool` | |
| Date | `fibery/date` | |
| Date + Time | `fibery/date-time` | |
| Date Range | `fibery/date-range` | |
| Location | `fibery/location` | |
| Single Select | - | `schema create-enum --options "A,B,C"` |
| Multi Select | - | `schema create-enum --options "A,B" --multi` |
| Workflow | - | `schema create-workflow --states "..."` |
| Rich Text | - | `schema create-rich-text` |
| Files | - | `schema create-files` |
| Formula | - | `schema create-formula --body '{...}'` |
| Relation | - | `schema create-relation` |
| Avatar | - | `schema install-mixins --mixins avatar/avatar-mixin` |
| Icon | - | `schema install-mixins --mixins icon/icon-mixin` |
| Whiteboards | - | `schema install-mixins --mixins whiteboards/whiteboards-mixin` |

## Available Mixins

| Mixin | What it adds |
|---|---|
| `fibery/rank-mixin` | Drag-sort ordering (included by default on create-type) |
| `Collaboration~Documents/ReferencesMixin` | Cross-reference tracking |
| `comments/comments-mixin` | Threaded comments |
| `icon/icon-mixin` | Emoji icons on entities (set via `icon/icon: ":emoji:"`) |
| `avatar/avatar-mixin` | Image avatars |
| `whiteboards/whiteboards-mixin` | Whiteboard capability |
| `workflow/workflow` | State machine (use `schema create-workflow` instead of install-mixins) |
| `documents/documents-mixin` | Legacy documents view |

## Capabilities Verified in Testing

The TEST CRM + TEST AR schemas in the Sandbox space exercise the full CLI surface:

**Schema operations tested:**
- Create 6 databases across CRM (Accounts, Contacts, Interactions) and AR (Invoices, Payments, Line Items)
- All 20 Fibery field types including url, email, phone, people, money-formatted decimals, workflow states
- 3 enum (single-select), 1 multi-select, 3 workflow state machines (8 states on Invoices)
- 7 relations (one-to-many, many-to-many) linking CRM and AR entities
- Rich-text fields with markdown content, file attachment fields
- Field reordering via `reorder-fields` batch command

**Entity operations tested:**
- Batch create (4 accounts, 6 contacts, 5 interactions, 4 invoices, 4 line items, 3 payments)
- Link/unlink by UUID and by name (statuses, tags, tiers, payment methods, account relations)
- Workflow state assignment on interactions and invoices
- People field assignment
- Comment creation and retrieval with markdown content
- File upload, attach, list, and bulk download with redirect following
- Rich-text document write and batch read

**View operations tested:**
- Create grid, board, list, gallery, timeline views with proper meta/units/query structure
- Create folders and move views into folders
- View deletion and folder cleanup
- Unit type mapping for all field types (text, number, date, bool, select, multi-select, reference, collection-count, workflow-state, rich-text-snippet, people, files)

**Cross-entity queries tested:**
- Invoice summaries with totals, paid, balance due
- Contact directory with account relations and multi-select tags
- Interaction timeline with attendees and workflow states
- Payment log with method, status, and Stripe references

## Known Limitations

1. **No user invitation API.** Users are managed via Fibery UI admin panel only.
2. **Relation cardinality is immutable.** Can't change one-to-many to many-to-many. Must delete and recreate.
3. **Secured field traversal blocked on dot-paths.** Use sub-queries for collection fields, client-side joins for single-entity references.
4. **batch-create requires uniform field sets.** All entities must have the same field keys (use null for optional fields).
5. **doc-write uses an undocumented PUT endpoint.** Canary test in test suite monitors it.
6. **Formula fields reference field UUIDs not names.** Must look up UUIDs from schema first.
7. **Workflow state editing is entity updates** on `workflow/state_Space/Type`, not a dedicated command.
8. **View folder IDs must come from API responses.** Client-generated UUIDs in create-folders may not match what Fibery stores. Always use the ID from the create-folders response.
9. **Views require proper meta structure.** Missing `units`, `filter`, or type-specific keys causes UI crashes (`r.filter` error). Use the unit type mapping table above.
10. **File downloads return 302 redirects.** httpx needs `follow_redirects=True`. Fixed in CLI.

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | User error (bad args, unknown workspace) |
| 2 | API error (5xx, 429, schema error) |
| 3 | Auth error (401, missing keychain token) |

## Credentials

```bash
# macOS Keychain
security find-generic-password -a fibery-myworkspace -s mcp-credentials -w
security add-generic-password -U -a fibery-myworkspace -s mcp-credentials -w "TOKEN"

# Direct auth
export FIBERY_TOKEN="YOUR_TOKEN"
fibery myworkspace --workspace-host myworkspace.fibery.io dbs
```

Credential lookup order:

1. `--token`
2. `FIBERY_TOKEN`
3. macOS Keychain

Get tokens from Fibery: Account Settings -> API Keys.

## Testing

```bash
cd tests
export FIBERY_TEST_WORKSPACE="myworkspace"
export FIBERY_TEST_WORKSPACE_HOST="myworkspace.fibery.io"
export FIBERY_TEST_TOKEN="YOUR_TOKEN"
uv run --with pytest --with httpx pytest test_unit.py test_integration.py test_parity.py -v
PYTEST_FIBERY_SANDBOX=1 uv run --with pytest --with httpx pytest test_sandbox.py -v
```

## Related Docs

- `docs/INTERNAL-API.md` - complete undocumented API reference with payload examples
- `docs/HAR-CLI-BUILDER.md` - the HAR capture pattern used to discover these endpoints
- `tests/README.md` - test suite documentation

## Troubleshooting

| Issue | Fix |
|---|---|
| `No token in Keychain` | `security add-generic-password -U -a fibery-<ws> -s mcp-credentials -w 'TOKEN'` |
| `401 Unauthorized` | Token expired. Get new one from Fibery UI. |
| `429 Rate limited` | 3 req/sec per token. Use `docs-batch` for multi-doc fetch. |
| `Type not found` | Check `Space/Name` spelling. Run `dbs --all`. |
| File download returns HTML | Missing `follow_redirects=True`. Fixed in current CLI. |
| `null database was not found` | Schema mutation args use plain keys (no `fibery/` prefix for rename/delete/set-meta). |
| Batch create fails with field mismatch | All entities need identical field keys. Set missing fields to null. |
| Relation traversal blocked | "Query with permissions" error. Use sub-queries instead of dot-paths. |
| View crashes with `r.filter` | View meta missing required keys. Rebuild with proper `units` + `filter` + type-specific keys. |
| Folder assignment doesn't persist | Use folder ID from `create-folders` or `query-folders` response, not client-generated UUIDs. |
| Views show "No items to display" | View `items[0].query.q/from` must be a type UUID, and `units` must include field expressions with correct field UUIDs. |
