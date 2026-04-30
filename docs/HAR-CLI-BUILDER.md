# HAR-Based CLI Builder

Reverse-engineer any web application's API by capturing Chrome DevTools HAR files and extracting the request patterns. Proven method - used to discover 15+ undocumented Fibery endpoints that the community and official docs said didn't exist.

## When to Use

- A web app's public API docs are incomplete or missing features
- You need to automate a workflow that only works via the UI
- You want to build a CLI for a SaaS product that doesn't have one
- You've exhausted blind endpoint probing and need ground truth

## The Pattern

### Step 1: Capture

1. Open the web app in Chrome
2. Open DevTools (Cmd+Opt+I) -> Network tab
3. Filter to **Fetch/XHR** (excludes static assets)
4. **Clear the log** (important - reduces noise)
5. Perform the exact UI action you want to replicate
6. **Stop immediately** after the action completes
7. Right-click in the request list -> **Save all as HAR with content**
8. Save to `~/Downloads/<app>-<action>.har`

### Step 2: Parse

```python
import json

with open('capture.har') as f:
    har = json.load(f)

entries = har['log']['entries']
for e in entries:
    url = e['request']['url']
    method = e['request']['method']
    body = e['request'].get('postData', {}).get('text', '')
    status = e['response']['status']
    resp = e['response']['content'].get('text', '')
    
    # Filter to API calls only
    if '/api/' not in url:
        continue
    if method == 'OPTIONS':
        continue
    
    print(f"{method} {url}")
    if body:
        print(f"  BODY: {json.dumps(json.loads(body), indent=2)[:500]}")
    print(f"  STATUS: {status}")
```

### Step 3: Identify the Pattern

Look for:
- **Command APIs** (`POST /api/commands`) - extract the `command` field from each request body
- **JSON-RPC endpoints** - extract the `method` field
- **REST endpoints** - note the URL pattern, method, and body shape
- **Nested batches** - some apps wrap multiple commands in a single request

### Step 4: Replay via Token Auth

Most web apps use session cookies in the browser but also support API tokens. Test whether the discovered endpoint works with token auth:

```python
import httpx

headers = {'Authorization': 'Token YOUR_API_KEY', 'Content-Type': 'application/json'}
r = httpx.post('https://app.example.com/api/commands', headers=headers, json=payload)
```

If cookie-only, the endpoint may be internal-only. If token auth works, you can automate it.

### Step 5: Wire into CLI

Once you have the exact request shape, wrap it in a CLI command with argparse.

## Lessons Learned (from Fibery CLI project)

### Naming conventions matter
Fibery uses `save` not `create` for new entities. We probed 50+ endpoint names (`create`, `add`, `new`, `insert`) and missed it. HAR capture found it in one try. **Always capture before guessing.**

### Method names are often plural
`create-folder` returned "method not found" but `create-folders` (plural) worked. Same for `delete-views`, `create-smart-folders`. Some APIs pluralize even for single-item operations.

### Batch wrappers differ
Fibery has `fibery.command/batch` (mixed operations) vs `fibery.schema/batch` (schema-only). They nest inside each other. The HAR shows the exact nesting pattern.

### Arg key inconsistency
Fibery's `schema.field/create` uses `fibery/holder-type` but `schema.field/rename` uses `holder-type` (no prefix). The HAR reveals the correct keys; docs may not.

### Redirects in file downloads
File download endpoints may return 302 redirects to cloud storage. The browser follows transparently but your HTTP client may not. Add `follow_redirects=True`.

### Hidden batch endpoints
Fibery's docs said batch document fetch was impossible. HAR revealed `POST /api/documents/commands` with `{command: "get-documents", args: [{secret: "..."},...]}` which fetches all docs in one call. The endpoint existed all along.

## Capture Checklist

For each action you want to reverse-engineer:

- [ ] Clear Network tab before starting
- [ ] Perform ONE action per capture (keep it clean)
- [ ] Save as HAR with content (includes response bodies)
- [ ] Name the file descriptively (`app-action.har`)
- [ ] Parse immediately while context is fresh
- [ ] Test with token auth before wiring into CLI
- [ ] Document the exact payload structure in your API reference

## Tool Integration

This skill pairs with:
- `fibery` - the CLI built from HAR captures
- `docs/INTERNAL-API.md` - API reference maintained from discoveries
- Any future CLI project where the web UI knows more than the docs

## Future: Automated HAR Capture

A web automation agent (Playwright, Puppeteer, or Claude Computer Use) could:
1. Open the web app
2. Start HAR recording
3. Perform UI actions programmatically
4. Save the HAR
5. Parse and compare against known endpoints
6. Flag new/changed API calls

This would turn HAR capture from a manual step into a continuous discovery pipeline.
