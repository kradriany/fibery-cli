# AGENTS.md - Using `fibery` from AI agents

This page is for AI agents (Claude Code, Cursor, custom LangChain workers, Goose, etc.) that call the `fibery` CLI on a user's behalf. Humans should start with [README.md](../README.md) and [USAGE.md](USAGE.md).

## Why this exists

Agents need three things the CLI doesn't surface by default: a predictable output contract, a known set of error signatures to escalate on, and a way to extend the tool when a needed capability is missing. Without those, agents fall into a loop of retrying broken commands or fabricating workarounds. This document covers each.

Companion docs:

- [CAPABILITIES.md](CAPABILITIES.md) - what is and isn't supported today
- [INTERNAL-API.md](INTERNAL-API.md) - endpoint reference (incl. UI-discovered ones)
- [HAR-CLI-BUILDER.md](HAR-CLI-BUILDER.md) - how this CLI was built, and how to extend it

## Output contract

- **Default to `-o json`.** Every subcommand emits a single JSON document to stdout on success. `raw` and `table` are for humans; `json` is the contract for agents.
- **stderr is for humans.** Treat stderr as diagnostics, not as data. Do not parse it.
- **One invocation, one document.** No streaming, no NDJSON unless explicitly stated in a subcommand's help. Agents can pipe stdout into `jq` or load with `json.loads(...)`.
- **Empty results are valid.** `query` returning `[]` or `{}` is not an error.

## Exit codes

| Code | Meaning | Agent should |
|---|---|---|
| `0` | Success | Continue |
| `1` | Generic failure (HTTP non-2xx, runtime error) | Read stderr; consider escalation if stderr matches the patterns below |
| `2` | Usage error (bad flags or args) | Fix the command and retry |
| `3` | Authentication failure | Stop - refresh the token; do not retry on the same credentials |
| `4` | Resource not found (entity, db, view, doc) | Stop - confirm with the user before fabricating an alternate path |
| `75` | Discovery loop is queued behind another run | Wait or move to other work; the queue will drain |

The `75` code matches `EX_TEMPFAIL` from `sysexits.h` so generic shell tooling treats it as a soft failure.

## Error signatures that warrant escalation

If stderr or the HTTP body contains any of these phrases, the missing capability cannot be solved by retrying. Invoke the auto-extension loop (see [README.md § Auto-Extension Loop](../README.md#auto-extension-loop)) instead:

- `method not found`
- `unknown command`
- `not implemented`
- `command not supported`
- `404` against a `*.fibery.io/api/...` URL

The Claude Code reference implementation is the `/fibery-discover` skill; equivalent flows for other agent frameworks are welcome. The contract is the same: capture the UI, diff the network log, generate a new subcommand, pass the eight safety gates, commit with an `auto/discover/<timestamp>` tag.

## Sandbox conventions

When an agent needs to test a write, mutate schema, or trial a new automation, do it in a sandbox:

- **Designated space**: a workspace space named `Sandbox`. Create it once if missing (`fibery <workspace> space create --name Sandbox`).
- **Entity prefix**: every test entity should be prefixed `discover-<YYYYMMDD-HHMM>-<short-action>`. Makes runs trivially scannable and cleanable.
- **Never write to production from a discovery run.** If `--where` returns a real entity, abort and surface it.
- **No auto-cleanup.** Sandbox is throwaway - leave evidence in place for the human to inspect. The user purges on their own schedule.

## Idempotency

| Operation | Idempotent? | Notes |
|---|---|---|
| `query`, `dbs`, `describe`, `schema`, `view --list`, `doc` | Yes | Pure reads |
| `link`, `unlink` | Yes | Replays return the same end state |
| `create`, `batch-create` | **No** | Always check first with `query --where` |
| `update`, `batch-update` | Yes | Same payload returns same final state |
| `delete`, `batch-delete` | Effectively yes | Re-deleting a deleted entity returns 404 - handle gracefully |
| `doc-write` | Conditional | `--append` is idempotent in spirit but appends each call; default-overwrite is idempotent |
| `automation create` | **No** | Creates a new rule per invocation; query existing rules first |

## Rate and concurrency

- **Reads are safe in parallel.** Fibery handles bursts; default to up to 4 concurrent `query` calls.
- **Writes should be serialized per database.** Fibery does not guarantee transaction isolation on rapid same-type creates.
- **Discovery loops should be serialized globally.** Use a single-writer lock; queue concurrent invocations rather than running them in parallel (the reference skill does this via `~/.claude/state/fibery-discover.lock`).

## What to do when you hit a wall

The expected flow when the CLI returns one of the escalation signatures:

1. **Do not keep retrying** with different command names. The endpoint genuinely doesn't exist in the CLI yet.
2. **Do not fabricate workarounds** that may leave partial state behind. Fibery has no transaction rollback.
3. **Invoke the discovery loop** (`/fibery-discover <action description>` in Claude Code, or the equivalent for your framework). The loop captures the live UI for the action and lands a new subcommand subject to the eight safety gates.
4. **Wait for the new subcommand** to appear in `fibery --help`, then retry your original task with it.
5. **If discovery itself fails** (no new endpoints, cookie-only auth, code review blocked), the wall is real. Surface it to the user with the diagnostics file the loop writes.

## See also

- [README.md](../README.md) - overview and the auto-extension loop contract
- [USAGE.md](USAGE.md) - full command reference
- [CAPABILITIES.md](CAPABILITIES.md) - current coverage matrix
- [INTERNAL-API.md](INTERNAL-API.md) - undocumented Fibery endpoints
