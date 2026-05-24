# AGENT-PLAYBOOK.md

A living catalog of known walls AI agents hit when using the Fibery CLI, plus the workaround for each. Read this before designing a multi-step flow. When you hit a new wall, append it.

This file is the orchestrator-facing companion to [AGENTS.md](AGENTS.md) (output contract, exit codes, escalation) and [CAPABILITIES.md](CAPABILITIES.md) (what is and isn't supported).

## How to use this page

For every wall: the symptom you'll see, the underlying limitation, and the workaround that lets you keep going. If the workaround is "wait for a fix", a tracking note tells you where the fix is being worked on.

## Walls

### L1. No entity-URL builder

**Symptom**: After `fibery <ws> create ... -o json` returns a `fibery/public-id`, there is no command to turn that id into a navigable URL. URL slugs use underscores where database names have spaces.

**Workaround**: build `https://<workspace>.fibery.io/<Space>/<DB-name-with-spaces-replaced-by-underscores>/<public-id>`. Verify the URL with `curl -I` before sharing.

**Tracking**: Cluster 1, ticket C1.1 - a `fibery <ws> entity url <type> <id>` subcommand plus a `--print-url` flag on mutations.

### L2. No shortcut to embed a URL inside a rich-text field

**Symptom**: `doc-write --format html` with a raw `<iframe>` is silently stripped by Fibery's sanitizer. The native UI `/embed` action inserts a ProseMirror `media` node, not an `embed` node.

**Workaround**: have the user `/embed` once in the UI to give you the exact `media` node shape, read the doc back with `fibery <ws> doc <secret> --format json --raw-content`, copy the node, and reuse the shape for future embeds. The captured shape lives in memory `reference_fibery_rtf_embed_node_shape.md`.

**Tracking**: Cluster 1, ticket C1.3 - a `doc-write <secret> --embed-url <url>` flag.

### L3. RTF sanitizer behavior is undocumented

**Symptom**: HTML you wrote disappears with no error. Common stripped tags: `<iframe>`, `<script>`, most attributes outside an allowlist. Accepted constructs: paragraphs, headings, lists, code blocks, `<details>`, and the ProseMirror `media` node.

**Workaround**: prefer `--format md`; reserve `--format html` for simple constructs you've tested. If you need an embed, see L2.

**Tracking**: Cluster 3, ticket C3.1 - a `fibery <ws> rtf-sanitizer-info` subcommand will codify the allowlist.

### L4. No `view create-embed` wrapper

**Symptom**: `view create --body-file <json>` requires six fields including container ids and a meta block. The user only had a URL.

**Workaround**: derive the body from the memory note `reference_fibery_embed_view_shape.md`. Get the space id from `fibery <ws> space list`. Fill `fibery/container-app.fibery/id` with that id, `fibery/meta.url` with your URL, and set `fibery/meta.compatibleMode: true`.

**Tracking**: Cluster 1, ticket C1.2 - a `fibery <ws> view create-embed --space <name> --url <url>` wrapper.

### L5. Keychain entry at the documented path doesn't exist

**Symptom**: `security find-generic-password -s fibery-<workspace> -a kyle` returns "specified item could not be found", but the workspace works fine via `fibery <ws> dbs`.

**Workaround**: try `security find-generic-password -s mcp-credentials -a fibery-<workspace>` instead. That's the canonical service name across this user's tooling. The `fibery` script auth helper already knows this; only the auto-extension skill's `keychain_token.sh` got it wrong.

**Tracking**: Cluster 2, ticket C2.1 - update `keychain_token.sh` to try `mcp-credentials` first. (Landed Day 1.)

### L6. No one-shot preflight check

**Symptom**: starting the auto-extension loop fails after four separate probes. Different things are missing: Keychain entry, Chrome with debug port, chrome-devtools MCP, Playwright MCP. Each surfaces only when its step runs.

**Workaround**: before invoking `/fibery-discover`, run this manually:

```bash
security find-generic-password -s mcp-credentials -a fibery-<workspace> -w >/dev/null \
  && echo "keychain OK" || echo "keychain MISSING"
curl -s http://localhost:9222/json/version >/dev/null \
  && echo "chrome OK" || echo "chrome MISSING"
```

**Tracking**: Cluster 2, ticket C2.2 - a `fibery <ws> doctor` subcommand will run this and a few more checks in one call.

### L7. Pipeline masks the real exit code

**Symptom**: `fibery <ws> view create ... 2>&1 | tee log | head -15; echo $?` prints `[fibery] ERROR: ...` then `0`. Looks like an exit-0 with an ERROR body.

**Root cause**: Bash reports `$?` for the last command in a pipeline. `head` exited 0, masking `fibery`'s non-zero exit. Verified Day 1: all 41 `[fibery] ERROR:` sites in the script already call `sys.exit(non-zero)`. This is a usage gotcha, not a CLI bug.

**Workaround**: either `set -o pipefail` before the call, or read `${PIPESTATUS[0]}` in bash. Avoid piping through `head`/`tee` if you need the exit code.

**Tracking**: documentation-only - resolved by the new "Pipeline gotcha" note in [AGENTS.md](AGENTS.md#exit-codes). (Landed Day 1.)

### L8. No discovery of supported ProseMirror node types

**Symptom**: writing a `media` node works; writing an `embed` node silently no-ops; there's no list of valid types.

**Workaround**: dump an existing doc that you know has the construct you want (e.g. a heading, a list, a media node) with `fibery <ws> doc <secret> --format json --raw-content` and copy the node shape.

**Tracking**: Cluster 1, ticket C1.4 - a `fibery <ws> doc-schema` subcommand will dump the accepted node types.

### L9. Multi-account `gh` silently breaks pushes

**Symptom**: a push to `kyle-undersight/html-plans` fails with `Repository not found` because an earlier `gh auth switch -u kradriany` made `kradriany` the active account, and that account doesn't have access to the target repo.

**Workaround**: before any `git push` from an agent context, run `gh auth status -a github.com | grep -B1 "Active account: true"` and confirm the username matches the repo owner. If not, `gh auth switch -u <owner>`.

**Tracking**: Cluster 3, ticket C3.2 - the discovery skill will warn on mismatch before pushing.

### L10. No `--print-url` on mutating commands

**Symptom**: `create` returns the full entity JSON. To share with a human, you have to construct the URL yourself (see L1) and emit it separately.

**Workaround**: same as L1.

**Tracking**: Cluster 1, tickets C1.1 and C2.4 - a `--print-url` flag on `create`, `update`, `doc-write`.

## Appending new walls

When you hit a wall not listed here:

1. Confirm it's reproducible (not a transient API error or your bad input).
2. Add an entry below in the same format: numbered Lxx, Symptom, Workaround, Tracking.
3. Open the corresponding capability or bug entry in [CAPABILITIES.md](CAPABILITIES.md) if it doesn't already exist.
4. Commit with subject `Add Lxx to AGENT-PLAYBOOK` so the change is easy to scan in the log.

The point is that the next agent to hit the same wall finds your workaround in seconds, not hours.

## See also

- [AGENTS.md](AGENTS.md) - output contract, exit codes, escalation triggers
- [CAPABILITIES.md](CAPABILITIES.md) - current support matrix
- [USAGE.md](USAGE.md) - full command reference
- [README.md § Auto-Extension Loop](../README.md#auto-extension-loop) - how new endpoints get added
