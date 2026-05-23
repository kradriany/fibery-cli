# Contributing

## Setup

```bash
cp fibery ~/bin/fibery && chmod +x ~/bin/fibery
uv run --with pytest --with httpx pytest tests/test_unit.py -v
```

Live tests use env vars instead of hardcoded workspace aliases:

```bash
export FIBERY_TEST_WORKSPACE="myworkspace"
export FIBERY_TEST_WORKSPACE_HOST="myworkspace.fibery.io"
export FIBERY_TEST_TOKEN="YOUR_TOKEN"
```

## Development Workflow

1. Make the smallest change that proves the fix.
2. Add or update tests when the change affects command parsing, auth, request payloads, or output shape.
3. Run `tests/test_unit.py` before opening a pull request.
4. Run integration or sandbox tests only when the change touches live API behavior.
5. Update `docs/USAGE.md` and `docs/INTERNAL-API.md` when flags, payloads, or undocumented endpoints change.

## HAR Capture Workflow

Use this when Fibery exposes a UI action that is missing from the official API docs.

1. Open Fibery in Chrome.
2. Open DevTools and switch to the Network tab.
3. Clear the log.
4. Perform one UI action.
5. Save the network traffic as a HAR file with content.
6. Inspect the request path, method, payload, and response.
7. Reproduce the call with token auth in `fibery`.
8. Add the endpoint details to `docs/INTERNAL-API.md`.
9. Add a test when the behavior is stable enough to cover.

Keep HAR files out of git. The repo ignores `*.har`.

## Pull Requests

- Keep changes focused.
- Document new flags and env vars.
- Include sample commands when behavior changes.
- Note any destructive test coverage you ran.

## Auto-Discovery Commits

Some commits land here via the auto-extension loop described in [README.md § Auto-Extension Loop](README.md#auto-extension-loop). They look ordinary at first glance - single-author, four-file scope, conventional message - but reviewers should treat them differently.

### How to recognize one

- Tag: `auto/discover/<YYYYMMDD-HHMMSS>` on the commit
- Diff scope: only `fibery`, `docs/INTERNAL-API.md`, `docs/USAGE.md`, `CHANGELOG.md`
- Commit message includes the discovered endpoint (e.g. `fibery.view/reorder-columns`) and the safety-gate summary

### Reviewer checklist

When reviewing an auto-discovery commit:

1. **Endpoint is real.** Confirm `docs/INTERNAL-API.md` shows a sample 2xx response, not just a request. The loop fails closed on this but defense-in-depth helps.
2. **No analytics or prefetch wired.** Endpoints with `analytics`, `telemetry`, `get-`, `query-`, or JSON-RPC `getX`/`queryX` method names should never become CLI commands.
3. **Payload sample doesn't leak secrets.** Workspace UUIDs are fine; user emails, tokens, or PII are not.
4. **`CHANGELOG.md` entry is informative.** The auto-generator emits a one-liner; ad-hoc edits are welcome.
5. **No `.har` files committed.** The auto-loop allowlists four files; if the diff is wider, something went wrong.

### Reverting

Use the tag, not the commit hash, so future log filters keep working:

```bash
git revert auto/discover/<YYYYMMDD-HHMMSS>
git push
```

The Claude Code reference implementation exposes this as `/fibery-discover-revert <tag>`; other agent frameworks should expose an equivalent.

### Safety-gate contract (summary)

Every auto-discovery commit must pass eight gates before push. Full list in [README.md § Auto-Extension Loop](README.md#auto-extension-loop). A reviewer who sees a tagged commit can assume all eight passed - but if any one looks suspect, revert and open an issue.

## Releases

Versioning uses Git tags such as `v0.1.0`.

Before tagging:

1. Update `CHANGELOG.md`.
2. Run unit tests.
3. Run any live tests needed for the changed surface.
4. Create and push the tag.
