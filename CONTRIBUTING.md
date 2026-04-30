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

## Releases

Versioning uses Git tags such as `v0.1.0`.

Before tagging:

1. Update `CHANGELOG.md`.
2. Run unit tests.
3. Run any live tests needed for the changed surface.
4. Create and push the tag.
