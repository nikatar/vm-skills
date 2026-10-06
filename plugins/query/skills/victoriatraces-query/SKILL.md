---
name: victoriatraces-query
description: >
  Query VictoriaTraces via curl or MCP using the Jaeger-compatible API. Use when discovering traced services
  and operations, searching traces by service/operation/duration/tags, retrieving traces by ID,
  or mapping service dependencies. Triggers on: trace queries, span search, trace ID lookup,
  service discovery, operation discovery, service dependencies, distributed tracing, Jaeger API.
compatibility: OpenCode, Claude Code
allowed-tools: Bash(curl:*), Bash(jq:*), Bash(date:*)
---

# VictoriaTraces Query

Query VictoriaTraces Jaeger-compatible HTTP API via curl or an MCP server. Covers service/operation discovery, trace search, trace retrieval by ID, and dependency mapping.

## Agent compatibility

This skill works with OpenCode (`@victoriatraces-query`) and Claude Code.
Discover the available MCP tools and their actual argument and response schemas; do not guess tool names or copy HTTP parameters into MCP calls. Prefer a permitted tool for the requested operation and target. HTTP examples below apply only to HTTP.
Use configured HTTP only when the matching MCP operation is absent or unavailable, never to bypass a permission or authentication denial or an empty result. Keep the same environment, backend instance, and tenant when switching transports; never extract MCP credentials or send credentials to guessed hosts.

For backend access, `permission.rejected` or `Permission denied` means stop that operation, not missing capability. Do not retry via another command, execute/fetch, webfetch, another agent, or the parent. Report the denial and request scoped approval; a rejected compound command does not establish permission for any of its backend operations.
Bound queries by the supplied scope, time window, and limits. Report missing capability, denied access, failed requests, and successful empty results separately. Before retrying a mutation with an unknown outcome, verify its state and obtain approval; do not blindly replay it.

## Environment

```bash
# $VM_TRACES_URL - base URL including /select/jaeger prefix
#   Example: export VM_TRACES_URL="https://vtselect.example.com/select/jaeger"
# $VM_CURL_CONFIG - curl config file with auth header (set for remote, unset for local)
#   Remote: export VM_CURL_CONFIG="$HOME/.config/victoriametrics/curl.conf"
#   Local:  leave unset (defaults to /dev/null - no auth)
```

IMPORTANT: The Jaeger API lives under `/select/jaeger/api/...`, NOT root `/api/...`. The `$VM_TRACES_URL` env var already includes the `/select/jaeger` prefix, so all endpoints below use `$VM_TRACES_URL/api/...`.

## Auth Pattern

All curl commands load auth from a curl config file:

```bash
curl -q --config "${VM_CURL_CONFIG:-/dev/null}" -s \
  "$VM_TRACES_URL/api/services" | jq .
```

When `VM_CURL_CONFIG` is unset, curl reads `/dev/null` and sends no auth header. When set, it must point to a mode-0600 curl config file containing `header = "Authorization: Bearer <token>"`. Never print its contents.

## Critical Rules

- Trace search `start`/`end` use Unix MICROSECONDS (16 digits, e.g., `1709769600000000`)
- Dependencies `endTs`/`lookback` use Unix MILLISECONDS (13 digits, e.g., `1709769600000`)
- `service` is required for trace search — you must know the service name first
- `minDuration`/`maxDuration` are string durations (e.g., `"1s"`, `"500ms"`)
- Trace IDs not found return 404 in the `errors` array, not an HTTP 404
- Trace search with time ranges outside retention returns plain text error, not JSON — handle gracefully
- Always discover services first, then operations, then search traces

## Core Endpoints

### List Services

```bash
curl -q --config "${VM_CURL_CONFIG:-/dev/null}" -s \
  "$VM_TRACES_URL/api/services" | jq '.data[]'
```

No parameters. Returns all traced service names. Always start here to discover what's available.

### Service Operations

```bash
curl -q --config "${VM_CURL_CONFIG:-/dev/null}" -s \
  "$VM_TRACES_URL/api/services/my-service/operations" | jq '.data[]'
```

`service` is a PATH parameter. Returns operation names for the given service.

### Search Traces

```bash
# Basic search (last hour, limit 20) — timestamps in microseconds (16 digits)
curl -q --config "${VM_CURL_CONFIG:-/dev/null}" -s \
  "$VM_TRACES_URL/api/traces?service=my-service&start=$(($(date +%s%6N) - 3600000000))&end=$(date +%s%6N)&limit=20" | jq .

# With operation and duration filter
curl -q --config "${VM_CURL_CONFIG:-/dev/null}" -s \
  "$VM_TRACES_URL/api/traces?service=my-service&operation=GET+/api/health&start=$(($(date +%s%6N) - 3600000000))&end=$(date +%s%6N)&minDuration=100ms&limit=20" | jq .

# With tag filter (Jaeger JSON format)
curl -q --config "${VM_CURL_CONFIG:-/dev/null}" -s \
  "$VM_TRACES_URL/api/traces?service=my-service&start=$(($(date +%s%6N) - 3600000000))&end=$(date +%s%6N)&tags=%7B%22http.status_code%22%3A%22500%22%7D&limit=20" | jq .

# With tag filter (VictoriaTraces extended format — key=value pairs, space-separated)
curl -q --config "${VM_CURL_CONFIG:-/dev/null}" -s -G \
  --data-urlencode 'tags=http.status_code=500 resource_attr:service.namespace=production' \
  "$VM_TRACES_URL/api/traces?service=my-service&start=$(($(date +%s%6N) - 3600000000))&end=$(date +%s%6N)&limit=20" | jq .
```

Parameters: `service` (required), `operation`, `start` (Unix µs), `end` (Unix µs), `limit`, `minDuration` (e.g., `1s`), `maxDuration`, `tags` (URL-encoded JSON object or VictoriaTraces key=value format)

### Get Trace by ID

```bash
curl -q --config "${VM_CURL_CONFIG:-/dev/null}" -s \
  "$VM_TRACES_URL/api/traces/abc123def456789" | jq .
```

Returns full trace with all spans. If trace not found, response contains `"errors": [{"code": 404, "msg": "trace not found"}]`.

### Service Dependencies

```bash
# Dependencies for the last hour
curl -q --config "${VM_CURL_CONFIG:-/dev/null}" -s \
  "$VM_TRACES_URL/api/dependencies?endTs=$(date +%s%3N)&lookback=3600000" | jq '.data[]'
```

Parameters: `endTs` (Unix ms, required), `lookback` (duration in ms, required). Returns edges between services showing call relationships.

## Timestamp Format

Trace search and dependencies use DIFFERENT timestamp units:

| Endpoint | Parameter | Unit | Digits | Example |
|----------|-----------|------|--------|---------|
| `/api/traces` | `start`, `end` | Microseconds | 16 | `1709769600000000` |
| `/api/dependencies` | `endTs` | Milliseconds | 13 | `1709769600000` |
| `/api/dependencies` | `lookback` | Milliseconds | 13 | `3600000` (1 hour) |

```bash
# Current time in microseconds (for trace search)
date +%s%6N

# 1 hour ago in microseconds
echo $(($(date +%s%6N) - 3600000000))

# Specific time to microseconds (GNU date)
date -d "2026-03-07T09:00:00Z" +%s%6N

# Current time in milliseconds (for dependencies)
date +%s%3N

# Duration values for minDuration/maxDuration are strings: "1s", "500ms", "100us"
# Duration value for lookback is ms number: 3600000 = 1 hour
```

## Response Parsing (jq)

```bash
# List service names
... | jq '.data[]'

# Extract trace IDs from search results
... | jq '.data[] | .traceID'

# Get span count per trace
... | jq '.data[] | {traceID: .traceID, spans: (.spans | length)}'

# Extract spans with duration > 1s (duration is in microseconds)
... | jq '.data[].spans[] | select(.duration > 1000000) | {operation: .operationName, duration_ms: (.duration / 1000)}'

# Get root span of each trace
... | jq '.data[] | .spans[] | select(.references == null or (.references | length) == 0) | {traceID: .traceID, operation: .operationName, service: .processID}'

# Extract service-to-service calls from dependencies
... | jq '.data[] | "\(.parent) -> \(.child) (\(.callCount) calls)"'

# Get all tags from a span
... | jq '.data[].spans[] | {operation: .operationName, tags: [.tags[] | {(.key): .value}] | add}'

# Find error spans
... | jq '.data[].spans[] | select(.tags[] | select(.key == "error" and .value == true)) | {traceID: .traceID, operation: .operationName}'
```

## Common Patterns

```bash
# Full discovery workflow: services -> operations -> traces
curl -q --config "${VM_CURL_CONFIG:-/dev/null}" -s "$VM_TRACES_URL/api/services" | jq '.data[]'
curl -q --config "${VM_CURL_CONFIG:-/dev/null}" -s "$VM_TRACES_URL/api/services/my-service/operations" | jq '.data[]'
curl -q --config "${VM_CURL_CONFIG:-/dev/null}" -s "$VM_TRACES_URL/api/traces?service=my-service&start=$(($(date +%s%6N) - 3600000000))&end=$(date +%s%6N)&limit=10" | jq '.data[] | .traceID'

# Find slow traces (> 5 seconds)
curl -q --config "${VM_CURL_CONFIG:-/dev/null}" -s \
  "$VM_TRACES_URL/api/traces?service=my-service&start=$(($(date +%s%6N) - 3600000000))&end=$(date +%s%6N)&minDuration=5s&limit=20" | jq '.data[] | {traceID: .traceID, spans: (.spans | length)}'

# Look up a trace ID found in logs
curl -q --config "${VM_CURL_CONFIG:-/dev/null}" -s \
  "$VM_TRACES_URL/api/traces/abc123def456789" | jq '.data[].spans[] | {operation: .operationName, duration_ms: (.duration / 1000), service: .processID}'

# Map service dependencies (last 24 hours) — dependencies use milliseconds
curl -q --config "${VM_CURL_CONFIG:-/dev/null}" -s \
  "$VM_TRACES_URL/api/dependencies?endTs=$(date +%s%3N)&lookback=86400000" | jq '.data[]'
```

## Environment Switching

```bash
# Check current environment
echo "VM_TRACES_URL: $VM_TRACES_URL"
echo "VM_CURL_CONFIG: ${VM_CURL_CONFIG:-(unset - no auth)}"
```

## Important Notes

- The Jaeger API prefix `/select/jaeger` is included in `$VM_TRACES_URL` — do NOT add it again
- `tags` parameter supports both Jaeger JSON format (`{"key":"value"}`) and VictoriaTraces extended format (`key=value resource_attr:key=value scope_attr:key=value`)
- Span durations in responses are in MICROSECONDS (not milliseconds)
- Process info is referenced by `processID` in spans, mapped in the trace's `processes` object
- GET is sufficient for all endpoints — POST also works for trace search
- For full endpoint details, parameters, and response formats, see `references/api-reference.md`
