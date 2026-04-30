# Fibery Internal API Reference

Undocumented and under-documented endpoints discovered via Chrome DevTools HAR capture (April 2026). All confirmed working with token auth (`Authorization: Token <api-key>`) unless noted otherwise.

Source HARs: `~/Downloads/myworkspace.fibery.io.har` (space creation), `~/Downloads/myworkspace.fibery.io 2.har` (fields, relations, automations, views).

---

## Command API (`POST /api/commands`)

### Space/App Lifecycle (UNDOCUMENTED)

The Fibery docs and community forums say "no Space creation API." Wrong. The UI uses these commands, and they work with token auth.

**Create a space:**
```json
[{
  "command": "fibery.command/batch",
  "args": {
    "commands": [
      {
        "command": "fibery.app/save",
        "args": {
          "app": {
            "fibery/id": "<new-uuid>",
            "fibery/name": "My Space",
            "fibery/title": "My Space",
            "fibery/namespace": "My Space",
            "fibery/description": "Description here",
            "fibery/version": "1.0.0",
            "fibery/show-in-menu?": true,
            "fibery/color": "#F7D130",
            "fibery/icon": "puzzle-piece",
            "fibery/status": "app/installed",
            "fibery/categories": [],
            "fibery/created-by": "",
            "fibery/schema": {
              "fibery/name": "My Space",
              "fibery/types": []
            }
          }
        }
      },
      {
        "command": "fibery.app/install",
        "args": {
          "name": "My Space",
          "version": "1.0.0"
        }
      }
    ]
  }
}]
```

**Delete a space** (two-step: uninstall then delete):
```json
[{"command": "fibery.app/uninstall", "args": {"fibery/id": "<app-uuid>"}}]
[{"command": "fibery.app/delete", "args": {"fibery/id": "<app-uuid>"}}]
```

**List all spaces:**
```json
[{
  "command": "fibery.entity/query",
  "args": {
    "query": {
      "q/from": "fibery/app",
      "q/select": {
        "fibery/id": ["fibery/id"],
        "fibery/name": ["fibery/name"],
        "fibery/title": ["fibery/title"],
        "fibery/status": ["fibery/status"],
        "fibery/color": ["fibery/color"],
        "fibery/icon": ["fibery/icon"]
      },
      "q/limit": 100
    }
  }
}]
```

### Enum/Single-Select Creation (UNDOCUMENTED)

`schema.enum/create` is a dedicated command for creating the enum type. Combined with `schema.field/create` for the relation fields and `fibery.entity.batch/create` for the options.

**Create a multi-select dropdown with options:**
```json
[{
  "command": "fibery.command/batch",
  "args": {
    "commands": [
      {
        "command": "fibery.schema/batch",
        "args": {
          "commands": [
            {
              "command": "schema.enum/create",
              "args": {
                "fibery/name": "Space/FieldName_Space/HolderType",
                "fibery/meta": {"fibery/type-component?": true}
              }
            },
            {
              "command": "schema.field/create",
              "args": {
                "fibery/holder-type": "Space/HolderType",
                "fibery/name": "Space/FieldName",
                "fibery/type": "Space/FieldName_Space/HolderType",
                "fibery/meta": {
                  "fibery/collection?": true,
                  "fibery/type-component?": true,
                  "fibery/relation": "<new-uuid>"
                }
              }
            },
            {
              "command": "schema.field/create",
              "args": {
                "fibery/holder-type": "Space/FieldName_Space/HolderType",
                "fibery/name": "Space/entities",
                "fibery/type": "Space/HolderType",
                "fibery/meta": {
                  "fibery/collection?": true,
                  "fibery/relation": "<same-uuid-as-above>"
                }
              }
            }
          ]
        }
      },
      {
        "command": "fibery.entity.batch/create",
        "args": {
          "type": "Space/FieldName_Space/HolderType",
          "entities": [
            {"enum/name": "Option 1", "fibery/rank": 0, "enum/color": null, "enum/icon": null},
            {"enum/name": "Option 2", "fibery/rank": 1000000, "enum/color": null, "enum/icon": null}
          ]
        }
      }
    ]
  }
}]
```

**Single-select vs multi-select**: Set `"fibery/collection?": false` on the holder-type side for single-select.

**Enum naming convention**: `Space/FieldName_Space/HolderType` (underscore-joined field + holder).

### Batch Operations (UNDOCUMENTED variants)

**`fibery.entity.batch/create`** - create many entities in one call (different from `fibery.command/batch` wrapping individual `fibery.entity/create` calls):
```json
[{
  "command": "fibery.entity.batch/create",
  "args": {
    "type": "Space/Type",
    "entities": [
      {"Space/Name": "Entity 1", "fibery/rank": 0},
      {"Space/Name": "Entity 2", "fibery/rank": 1000000}
    ]
  }
}]
```

**`fibery.entity.batch/delete`** - delete many entities:
```json
[{
  "command": "fibery.entity.batch/delete",
  "args": {
    "type": "Space/Type",
    "entities": [{"fibery/id": "<uuid-1>"}, {"fibery/id": "<uuid-2>"}],
    "opts": {"fail-if-not-found?": false}
  }
}]
```

### Collection Item Management (documented but under-explained)

**`fibery.entity/add-collection-items`** - link entities via a relation field:
```json
[{
  "command": "fibery.entity/add-collection-items",
  "args": {
    "type": "Space/ParentType",
    "entity": {"fibery/id": "<parent-uuid>"},
    "field": "Space/RelationField",
    "items": [{"fibery/id": "<target-uuid-1>"}, {"fibery/id": "<target-uuid-2>"}]
  }
}]
```

Works for enum fields too (multi-select options are collection items).

### Schema Field Meta Operations

**`schema.field/delete-meta`** - remove a specific meta key from a field (UNDOCUMENTED, inverse of `schema.field/set-meta`):
```json
{
  "command": "schema.field/delete-meta",
  "args": {
    "holder-type": "Space/Type",
    "name": "Space/FieldName",
    "key": "fibery/readonly?"
  }
}
```

Uses plain keys (no `fibery/` prefix), same as `schema.field/set-meta`.

### Schema Enum Creation

**`schema.enum/create`** - create the enum type (must be inside `fibery.schema/batch`):
```json
{
  "command": "schema.enum/create",
  "args": {
    "fibery/name": "Space/EnumName_Space/HolderType",
    "fibery/meta": {"fibery/type-component?": true}
  }
}
```

### Event Sequencing (UNDOCUMENTED)

**`fibery.event/last-sequence-id`** - returns the current event sequence number. Useful for incremental sync (poll for changes since a known sequence ID).
```json
[{"command": "fibery.event/last-sequence-id", "args": {}}]
// Response: [{"success": true, "result": 13763}]
```

### Schema Query Variant

**`fibery.schema/query-info`** - alternative to `fibery.schema/query`, used by the UI on page load:
```json
[{"command": "fibery.schema/query-info", "args": {}}]
```

### Permission/Capability Queries (UNDOCUMENTED)

```json
[{"command": "fibery.app/query-user-capabilities", "args": {"return-app-with-empty-capabilities?": true}}]
[{"command": "fibery.entity/query-user-capabilities", "args": {...}}]
[{"command": "fibery.type/query-user-capabilities", "args": {...}}]
[{"command": "fibery.type/query-author-capability-access", "args": {...}}]
```

### Batch Wrapper Note

**`fibery.command/batch`** is different from **`fibery.schema/batch`**:
- `fibery.command/batch` wraps mixed command types (entity + schema + app operations)
- `fibery.schema/batch` wraps only schema mutation commands (`schema.*/...`)
- The UI nests them: `fibery.command/batch` → `fibery.schema/batch` → `schema.field/create`

---

## REST Endpoints

### Field Creator (UNDOCUMENTED)

`POST /api/field-creator/field` - high-level field creation including formula fields:
```json
{
  "fieldObject": {
    "fibery/holder-type": "Space/Type",
    "fibery/id": "<new-uuid>",
    "fibery/name": "Space/FieldName",
    "fibery/description": "description",
    "fibery/type": "fibery/text",
    "fibery/meta": {
      "fibery/readonly?": true,
      "formula/formula?": true,
      "formula/formula": {
        "expression": ["q/concat", ["<field-uuid>"], "$formulaParam1"],
        "params": {"$formulaParam1": " - "}
      }
    }
  }
}
// Response: {"createdSynced": true}
```

### Schema (simple GET)

`GET /api/schema` - returns the full workspace schema as a single GET request (no POST body needed). Alternative to `POST /api/commands` with `fibery.schema/query`.

### Documents

`PUT /api/documents/{secret}` - write rich-text content:
```json
{"content": "Markdown content here", "format": "md"}
// Response: true
```

`GET /api/documents/{secret}?format=md|html|json` - read rich-text content.

`POST /api/documents/commands?format=json` - document commands:

**Batch fetch (MAJOR DISCOVERY - eliminates single-doc-at-a-time limitation):**
```json
{"command": "get-documents", "args": [{"secret": "uuid-1"}, {"secret": "uuid-2"}, {"secret": "uuid-3"}]}
// Returns array of {secret, content: {doc: {type: "doc", content: [...]}}} in ProseMirror JSON
// Add ?format=md for markdown output
```

**Create/update:**
```json
{"command": "create-or-update-documents", "args": []}
```

### Automations (UNDOCUMENTED)

**Create automation rule:**
`POST /api/automations/auto-rules/for-type/{typeId}`
```json
{
  "enabled": true,
  "name": "Rule name",
  "triggers": [{
    "trigger": "collection-item-added",
    "args": {"changedCollectionField": "<field-uuid>"}
  }],
  "actions": [{
    "action": "update-<type-uuid>",
    "args": {"fields": {"type": "value", "value": {}}}
  }]
}
```

**Trigger types observed**: `collection-item-added`
**Action types observed**: `update-<type-uuid>`

**List/manage:**
- `GET /api/automations/auto-rules/for-type/{typeId}` - list rules
- `GET /api/automations/auto-rules/{ruleId}` - get single rule
- `GET /api/automations/auto-rules/for-type/{typeId}/triggers` - available triggers
- `GET /api/automations/auto-rules/for-type/{typeId}/actions` - available actions
- `POST /api/automations/auto-rules/for-type/{typeId}/set-order` - reorder rules
- `GET /api/automations/buttons/for-type/{typeId}` - list buttons
- `GET /api/automations/buttons/public/for-type/{typeId}` - public buttons
- `GET /api/automations/utility/current-month-stats` - usage stats

### Canvas (UNDOCUMENTED)

`POST /api/canvas`
```json
{"command": "DuplicateBoards", "args": {"duplicateCommands": []}}
```

### AI (UNDOCUMENTED)

- `POST /api/ai-commands/` - JSON-RPC, methods: `getSettings`
- `POST /api/ai-views` - AI-powered view generation

### Notifications (UNDOCUMENTED)

- `POST /api/notifications/people-field/types/{typeId}/fields/{fieldId}` - configure notifications per people field
- `POST /api/notifications/in-app/search/count` - notification count
- `GET /api/notifications/rules` - notification rules
- `GET /api/notifications/watch/type/{typeId}/entity/{entityId}` - watch status

### Access Control (UNDOCUMENTED)

`POST /api/access-templates/json-rpc`
Methods: `getAssigneesAccess`
```json
{"jsonrpc": "2.0", "method": "getAssigneesAccess", "params": {"typeId": "<uuid>", "fieldId": "<uuid>"}}
```

### Sharing (UNDOCUMENTED)

- `GET /api/sharing/commands/check/{typeId}/{entityId}` - check sharing status
- `GET /api/sharing/commands/list-shares/{typeId}/{entityId}` - list shares

---

## JSON-RPC Endpoints

### `/api/views/json-rpc`

| Method | Purpose |
|---|---|
| `query-views` | List views (with filters) |
| `query-folders` | List view folders |
| `query-menu-items` | Menu item configuration |
| `query-smart-folders` | Smart folder definitions |
| `query-view-user-settings` | Per-user view settings |
| `can-create-views` | Check creation permissions |
| `create-views` | Create new views (grid, board, gallery, list, timeline, chart, map, whiteboard) |
| `create-menu-items` | Add items to navigation menu |
| `query-view-permissions` | View-level permissions |
| `query-view-references` | Cross-references between views |
| `get-view-type-id` | Resolve view type |

### `/api/layouts/json-rpc`

| Method | Purpose |
|---|---|
| `get-custom-emojis` | Custom emoji definitions |
| `get-entities-layouts` | Entity card/form layouts |
| `get-layouts-settings` | Layout configuration |
| `get-database-relation-field-configs` | Relation field display config |
| `get-user-layouts` | Per-user layout overrides |
| `get-databases-order` | Database ordering within a space |
| `get-databases-order-for-apps` | Database ordering across spaces |

### `/api/forms/json-rpc`

| Method | Purpose |
|---|---|
| `get-quick-add-forms` | Quick-add form definitions per type |

### `/api/app-gallery/json-rpc`

| Method | Purpose |
|---|---|
| `getShare` | Check if a space is shared to gallery |
| `getGallery` | Browse template gallery (categories + apps) |

### `/api/license/json-rpc`

| Method | Purpose |
|---|---|
| `plans` | Current plan details |

---

## Rich-Text Field Creation Pattern

From the HAR, the UI creates a rich-text (Description) field using this exact pattern inside `schema.type/create`:

```json
{
  "fibery/name": "Space/Description",
  "fibery/type": "Collaboration~Documents/Document",
  "fibery/meta": {
    "fibery/entity-component?": true,
    "ui/object-editor-order": -1
  }
}
```

Key: `fibery/type` is `Collaboration~Documents/Document` and `fibery/entity-component?` must be `true`.

---

## Relation Creation Pattern

The UI creates a self-relation (Database 1 to Database 1) like this:

```json
{
  "command": "fibery.schema/batch",
  "args": {
    "commands": [
      {
        "command": "schema.field/create",
        "args": {
          "fibery/holder-type": "Space/Type",
          "fibery/name": "Space/Type",
          "fibery/type": "Space/Type",
          "fibery/meta": {
            "fibery/relation": "<shared-uuid>"
          }
        }
      },
      {
        "command": "schema.field/create",
        "args": {
          "fibery/holder-type": "Space/Type",
          "fibery/name": "Space/Types",
          "fibery/type": "Space/Type",
          "fibery/meta": {
            "fibery/collection?": true,
            "fibery/relation": "<same-shared-uuid>"
          }
        }
      },
      {
        "command": "schema.field/delete-meta",
        "args": {"holder-type": "Space/Type", "name": "Space/Types", "key": "fibery/readonly?"}
      },
      {
        "command": "schema.field/delete-meta",
        "args": {"holder-type": "Space/Type", "name": "Space/Type", "key": "fibery/readonly?"}
      },
      {
        "command": "schema.field/delete-meta",
        "args": {"holder-type": "Space/Type", "name": "Space/Types", "key": "link-rule/link-rule?"}
      },
      {
        "command": "schema.field/delete-meta",
        "args": {"holder-type": "Space/Type", "name": "Space/Types", "key": "link-rule/link-rule"}
      }
    ]
  }
}
```

Note: the UI also runs `schema.field/delete-meta` to clean up `fibery/readonly?` and `link-rule/*` meta keys that get auto-set.

---

## Field Type Specialization via `ui/type` Meta

Fibery has few primitive types. Specialized field behaviors (URL, email, phone) are `fibery/text` fields with `ui/type` meta set. This is how the UI creates them.

**Available `ui/type` values (observed in production schemas):**
- `"email"` - renders as clickable mailto link, validates email format
- `"phone"` - renders as clickable tel link
- `"url"` - renders as clickable hyperlink

**Example: create an email field:**
```json
{"command": "fibery.schema/batch", "args": {"commands": [
  {"command": "schema.field/create", "args": {
    "fibery/holder-type": "Space/Type",
    "fibery/name": "Space/Contact Email",
    "fibery/type": "fibery/text",
    "fibery/meta": {"ui/type": "email"}
  }}
]}}
```

Then optionally set the meta:
```json
{"command": "schema.field/set-meta", "args": {
  "holder-type": "Space/Type", "name": "Space/Contact Email",
  "key": "ui/type", "value": "email"
}}
```

---

## Number Formatting via Meta

Number fields (`fibery/int`, `fibery/decimal`) support rich formatting via meta keys. These control display only - the underlying data type doesn't change.

**Available meta keys:**
| Key | Values | Purpose |
|---|---|---|
| `ui/number-format` | `"Money"`, `"Number"`, `"Percent"` | Display format |
| `ui/number-currency-code` | `"USD"`, `"EUR"`, `"GBP"`, etc. | Currency symbol (Money format) |
| `ui/number-precision` | `0`, `1`, `2`, ... | Decimal places |
| `ui/number-thousand-separator?` | `true` / `false` | Comma grouping |
| `ui/number-unit` | `"days"`, `"hours"`, or `null` | Unit suffix |

**Example: configure a revenue field as USD money:**
```json
// Set each meta key individually (schema.field/set-meta takes one key/value per call)
{"command": "fibery.schema/batch", "args": {"commands": [
  {"command": "schema.field/set-meta", "args": {"holder-type": "Space/Type", "name": "Space/Revenue", "key": "ui/number-format", "value": "Money"}},
  {"command": "schema.field/set-meta", "args": {"holder-type": "Space/Type", "name": "Space/Revenue", "key": "ui/number-currency-code", "value": "USD"}},
  {"command": "schema.field/set-meta", "args": {"holder-type": "Space/Type", "name": "Space/Revenue", "key": "ui/number-precision", "value": 2}},
  {"command": "schema.field/set-meta", "args": {"holder-type": "Space/Type", "name": "Space/Revenue", "key": "ui/number-thousand-separator?", "value": true}}
]}}
```

---

## Workflow States (State Machine Fields)

Fibery has a built-in workflow system. When the `workflow/workflow` mixin is installed on a type, it gets a `workflow/state` field with a state machine (states + transitions). This is different from a plain enum - workflow states support:
- Ordered state transitions
- Final states (done/cancelled)
- Color per state
- Automation triggers on state change

**Types with workflow states in production:** Task Management/Task, CRM/Contacts, 4DF Invoice Board/Invoices, Business/Award Credit Tracker.

**Install workflow via mixin:**
```json
{"command": "fibery.app/install-mixins", "args": {
  "types": {"Space/Type": ["workflow/workflow"]}
}}
```

After installation, configure states via the state type (`workflow/state_Space/Type`). States are entities with `enum/name`, `workflow/Final`, `workflow/color`, and `fibery/rank` fields.

**Discovered via HAR 3:** `workflow/install` is the command. Takes the type, a states array, and a default state ID.

**Create workflow with states:**
```json
[{
  "command": "workflow/install",
  "args": {
    "type": "Space/Type",
    "states": [
      {"fibery/id": "<uuid>", "enum/name": "To Do", "enum/color": null, "enum/icon": null, "workflow/Type": "Not started"},
      {"fibery/id": "<uuid>", "enum/name": "In Progress", "enum/color": null, "enum/icon": null, "workflow/Type": "Started"},
      {"fibery/id": "<uuid>", "enum/name": "Done", "enum/color": null, "enum/icon": null, "workflow/Type": "Finished"}
    ],
    "default-state-id": "<first-state-uuid>"
  }
}]
```

**`workflow/Type` values:** `"Not started"`, `"Started"`, `"Finished"` - these control the state category (determines color band and reporting).

**Setting state on an entity:** Use standard `fibery.entity/update` with `workflow/state`:
```json
{"command": "fibery.entity/update", "args": {
  "type": "Space/Type",
  "entity": {"fibery/id": "<entity-uuid>", "workflow/state": {"fibery/id": "<state-uuid>"}}
}}
```

**Additional mixins discovered in HAR 3:**
- `icon/icon-mixin` - adds `icon/icon` field (emoji icons on entities, set via `icon/icon: ":+1:"`)
- `avatar/avatar-mixin` - adds avatar/image field
- `whiteboards/whiteboards-mixin` - adds whiteboard capability

---

## Formula Fields via `/api/field-creator/field`

Formula fields are NOT created via the command API. They use a dedicated REST endpoint.

**Endpoint:** `POST /api/field-creator/field`

**Formula expression format:** Uses field UUIDs (not names) in a Lisp-like expression DSL:
- `["q/concat", [field-uuid-1], "$param1"]` - string concatenation
- `["-", [field-uuid-1], [field-uuid-2]]` - subtraction
- `["q/if", ["=", ...], then, else]` - conditional
- `["q/date-or-date-time-to-text", [field-uuid]]` - date formatting
- `["q/number-to-text", [field-uuid]]` - number to string

**CLI gap:** Formula field creation not wired into the CLI. Would need a `schema create-formula` command wrapping the REST endpoint. Requires field UUIDs which need a schema lookup first.

---

## Button Creation via Automations REST API

Buttons are automation rules of type `BUTTON` (vs `AUTO` for triggers). Created via the same REST endpoint as automations.

**Endpoint:** `POST /api/automations/buttons/for-type/{typeId}`

```json
{
  "enabled": true,
  "name": "Send Follow-up",
  "actions": [{
    "action": "email-app-$-app-$-send",
    "args": {
      "to": {"type": "value", "value": ""},
      "subject": {"type": "value", "value": ""},
      "message": {"type": "value", "value": ""},
      "markdown": {"type": "value", "value": false}
    }
  }]
}
```

**Action types observed:** `email-app-$-app-$-send` (send email), `update-<type-uuid>` (update entity fields).

**Button management:**
- `GET /api/automations/buttons/for-type/{typeId}` - list buttons
- `GET /api/automations/buttons/for-type/{typeId}/actions` - available actions
- `POST /api/automations/buttons/for-type/{typeId}/set-order` - reorder buttons

---

## RTF Advanced Content (ProseMirror JSON)

Documents stored via `/api/documents/{secret}` support three formats: `md` (markdown), `html`, and `json` (ProseMirror).

**ProseMirror JSON** is Fibery's internal document representation. It supports:
- @mentions (user references)
- Entity embeds (inline entity references)
- Slash command outputs
- Rich formatting (tables, code blocks, callouts)
- File attachments inline

**Writing advanced content:** Use `doc-write` with `--format json` and pass ProseMirror JSON. The structure is a tree of typed nodes.

**CLI gap:** `doc-write` currently works best with markdown. ProseMirror JSON writing is supported (`PUT` accepts `format: "json"`) but we haven't documented the node schema or tested advanced content round-trips. Needs: example payloads for @mentions, entity embeds, and tables.

---

## View Creation via `/api/views/json-rpc`

The HAR revealed that Fibery creates views (grid, board, gallery, list, timeline, chart, map, whiteboard) via a JSON-RPC endpoint.

**Endpoint:** `POST /api/views/json-rpc`

**Methods:**
- `create-views` - create one or more views
- `can-create-views` - check permissions before creating
- `create-menu-items` - add view to navigation sidebar

**View types observed:** `grid`, `board`, `gallery`, `list`, `timeline`, `chart`, `map`, `whiteboard`

**Full view/folder management methods (discovered in HAR 4):**

```json
// Create folder
{"method": "create-folders", "params": {"values": [{
  "fibery/id": "<new-uuid>", "fibery/name": "Folder Name",
  "fibery/rank": 6683349842739893,
  "fibery/container-app": {"fibery/id": "<space-uuid>"},
  "fibery/private?": false, "fibery/Parent Folder": null
}]}}

// Rename folder
{"method": "update-folders", "params": {"updates": [{"id": "<folder-uuid>", "values": {"fibery/name": "New Name"}}]}}

// Create smart folder
{"method": "create-smart-folders", "params": {"values": [{
  "fibery/app": {"fibery/id": "<space-uuid>"},
  "fibery/name": "Smart Folder", "fibery/rank": 6683349843739893,
  "fibery/meta": {"items": []}, "includeViews": [], "includeFolders": [],
  "fibery/id": "<new-uuid>"
}]}}

// Configure smart folder (add type filter)
{"method": "update-smart-folders", "params": {"updates": [{"id": "<sf-uuid>", "values": {
  "fibery/meta": {"items": [{"params": {}, "query": {"q/from": "<type-uuid>"}, "groupBy": null, "filter": null}]}
}}]}}

// Rename view
{"method": "update-views", "params": {"updates": [{"id": "<view-uuid>", "values": {"fibery/name": "New Name"}}]}}

// Move view to folder (via update-views with fibery/Folder)
{"method": "update-views", "params": {"updates": [{"id": "<view-uuid>", "values": {"fibery/Folder": "<folder-uuid>"}}]}}

// Delete views
{"method": "delete-views", "params": {"ids": ["<view-uuid>"]}}
```

**Also discovered:**
- `schema.type/set-meta` - set type-level meta (e.g. `ui/color`), inside `fibery.schema/batch`
- `fibery.app/update` - update space properties: `{fibery/id, fibery/icon, fibery/color}`

---

## Complete Primitive Field Type Inventory

| Type | Purpose | Notes |
|---|---|---|
| `fibery/text` | Plain text | Specialize with `ui/type` meta for email/phone/url |
| `fibery/int` | Integer | Format with `ui/number-*` meta for money/percent |
| `fibery/decimal` | Decimal number | Same formatting meta as int |
| `fibery/bool` | Boolean | |
| `fibery/date` | Date only | ISO format YYYY-MM-DD |
| `fibery/date-time` | Date + time | ISO format with timezone |
| `fibery/date-range` | Date range | Start + end dates |
| `fibery/uuid` | UUID | System use (fibery/id) |
| `fibery/rank` | Rank/ordering | Auto-managed for drag-sort |
| `fibery/email` | Email address | System type (fibery/user only). For custom fields use `fibery/text` + `ui/type: "email"` |
| `fibery/emoji` | Emoji | Used for enum icons |
| `fibery/color` | Color hex | Used for enum colors |
| `fibery/location` | Geographic location | Lat/long |
| `fibery/json-value` | Arbitrary JSON | Used for specs/configs |
| `fibery/file` | File attachment | Use file API for upload/download |
| `fibery/user` | User reference | Points to workspace user |
| `fibery/view` | View reference | Used by documents-mixin |
| `Collaboration~Documents/Document` | Rich text | Use with `fibery/entity-component?: true` meta |
| `workflow/state_*` | Workflow state | Auto-created by workflow mixin |

---

## Secured Field Traversal Limitation

When querying entities with relation traversal (dot-path notation like `["Sandbox/Account", "Sandbox/name"]`), Fibery's permissions layer blocks access if the target field is on a secured type. Error: "Query with permissions does not support collection field expression ended with secured field."

**Workaround:** Use sub-queries for collection fields, or client-side joins for single-entity references.

```json
// Instead of: "account_name": ["Sandbox/Account", "Sandbox/name"]
// Use sub-query:
"account": {"q/from": ["Sandbox/Account"], "q/select": {"n": ["Sandbox/name"]}, "q/limit": 1}
```

This only works for collection fields (one-to-many side). For many-to-one references (single entity), no sub-query syntax exists - must query separately and join client-side.

---

## Key Insights

1. **`save` not `create`** - Fibery uses `fibery.app/save` for space creation, not any `create` variant. Blind probing will miss this.

2. **Two batch wrappers** - `fibery.command/batch` for mixed operations, `fibery.schema/batch` for schema-only. They nest.

3. **Enum naming convention** - Enum type name is `Space/FieldName_Space/HolderType` with an underscore join.

4. **`fibery.entity.batch/create`** is distinct from wrapping multiple `fibery.entity/create` in a batch. It takes `entities` (array) instead of `entity` (single).

5. **`fibery.event/last-sequence-id`** could enable incremental sync (poll for events > last known ID) but we haven't found the corresponding "get events since ID" command yet.

6. **Formula fields** go through `/api/field-creator/field`, not the command API. The formula expression uses field UUIDs, not names.

7. **Automation creation** is REST-based (`POST /api/automations/auto-rules/for-type/{typeId}`), not command-based. Triggers and actions reference type UUIDs.

8. **HAR capture pattern** - Always capture UI actions via Chrome DevTools HAR before assuming an API doesn't exist. The public Fibery docs are incomplete.

9. **`workflow/install`** is a top-level command (not inside schema/batch) for installing state machines. Takes type, states array with `workflow/Type` categories, and a default state ID.

10. **All available mixins** (discovered across 3 HARs):
    - `fibery/rank-mixin` - drag-sort ordering
    - `Collaboration~Documents/ReferencesMixin` - cross-references
    - `comments/comments-mixin` - threaded comments
    - `workflow/workflow` - state machine (but install via `workflow/install` not `install-mixins`)
    - `documents/documents-mixin` - legacy documents
    - `icon/icon-mixin` - emoji icons on entities
    - `avatar/avatar-mixin` - image avatars
    - `whiteboards/whiteboards-mixin` - whiteboard capability

11. **Specialized text fields** use `ui/type` meta, not separate primitive types. URL, email, phone are all `fibery/text` underneath. Set `ui/type` via `set-field-meta` or at creation time.

12. **Number formatting** is display-only via `ui/number-format` meta (`"Money"`, `"Number"`, `"Percent"`). The underlying type stays `fibery/int` or `fibery/decimal`.

13. **File downloads return 302 redirects** to cloud storage (likely S3/GCS). Must use `follow_redirects=True` with httpx. Without it, you get a 302 with an HTML body instead of the file content. The redirect URL is a pre-signed cloud URL that doesn't need the auth token.

14. **File field creation** uses `fibery/type: "fibery/file"` with `fibery/collection?: true` and `fibery/entity-component?: true`. Files are then attached via `fibery.entity/add-collection-items` using the file entity's `fibery/id`. File entities have `fibery/name`, `fibery/secret`, `fibery/content-type`, `fibery/content-length`.

15. **`fibery.entity.batch/create` requires uniform field sets** across all entities in the batch. Missing optional fields must be explicitly set to `null`. The API rejects batches where entities have different field keys.
