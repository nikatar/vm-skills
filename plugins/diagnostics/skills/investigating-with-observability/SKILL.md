---
name: investigating-with-observability
description: Use when investigating issues, debugging problems for applications, or responding to alerts in the Kubernetes cluster using VictoriaMetrics, VictoriaLogs, or VictoriaTraces.
compatibility: OpenCode, Claude Code
allowed-tools: Bash(curl:*), Bash(jq:*), Bash(date:*), Agent, Read
---

# Troubleshooting with Observability Skills

## Agent compatibility

This skill works with OpenCode (`@investigating-with-observability`) and Claude Code.
When the agent supports delegation (OpenCode `subagent`, Claude `Agent`), helper
investigations may run in parallel. If delegation is unavailable or denied, run the same helper steps sequentially
in the main agent.

Discover the available MCP tools and their actual argument and response schemas; do not guess tool names or copy HTTP parameters into MCP calls. Prefer a permitted tool for the requested operation and target. HTTP examples below apply only to HTTP.
Use configured HTTP only when the matching MCP operation is absent or unavailable, never to bypass a permission or authentication denial or an empty result. Keep the same environment, backend instance, and tenant when switching transports; never extract MCP credentials or send credentials to guessed hosts.

For backend access, `permission.rejected` or `Permission denied` means stop that operation, not missing capability. Do not retry via another command, execute/fetch, webfetch, another agent, or the parent. Report the denial and request scoped approval; a rejected compound command does not establish permission for any of its backend operations.
Bound queries by the supplied scope, time window, and limits. Report missing capability, denied access, failed requests, and successful empty results separately. Investigation is read-only; any proposed deployment change needs separate approval.

## Core Principle

Random querying wastes time and produces misleading results. Empty results from wrong metric names look identical to "no problem exists." Jumping between signals without a hypothesis leads to thrashing.

**Discover before you query. Hypothesize before you correlate. Confirm before you conclude.**

If you haven't completed Phase 1, you cannot propose root causes. If you haven't correlated across at least two signal types, your conclusion is a guess.

## The Investigation Protocol

Complete each phase before proceeding to the next.

```
Phase 1: Gather Signals     → What's already known? What's alerting?
Phase 2: Discover and Scope  → What data exists? What are the real names?
Phase 3: Hypothesize and Test → Form one theory, query to confirm or refute
Phase 4: Correlate and Confirm → Cross-reference across signal types, find root cause
```

### Phase 1: Gather Signals

Before writing any query, establish what's already known.

**1. Check backend capabilities** — run the HTTP and MCP gating check from the Subagent Dispatch section.

**2. Dispatch signal-gathering subagents in parallel (or sequentially if the agent does not support delegation):**

| Helper | Condition | What it does |
|----------|-----------|-------------|
| AlertManager check | A permitted VM alerts or AlertManager operation is available through MCP or configured HTTP | Checks each available backend independently; reports unavailable operations |

The AlertManager check helper handles VM alerts and AlertManager queries only where each operation is available. It can run with either backend alone; do not dispatch a separate metrics discovery helper for alerts.

Read the helper prompt files (`agents/alertmanager-check.md`, etc.) and run them as subagents when delegation is permitted (OpenCode `subagent`, Claude `Agent`). In each helper task include:

- The prompt file content
- The investigation target (namespace, service, or component name if known)
- Available operations and transport configuration per backend, with the exact target/tenant and permitted tools
- The time range
- Query limits and budget; helpers must use their own permissions, not assume they inherit the parent's access
- The required output format

If the current agent cannot delegate, execute the same steps sequentially in the main agent.

**3. Synthesize results** — once helpers return:

- Combine alert findings from all sources
- Establish a timeline: when did symptoms start? What changed?
- If timeline is unclear, ask the user

**4. Identify which signal type to start with:**

| Symptom | Start with | Then correlate with |
|---------|-----------|-------------------|
| Resource/rate issue | Metrics | Logs |
| Errors/crashes | Logs | Metrics |
| Latency/slow requests | Traces | Logs |
| Alert firing | Metrics (alert details) | Logs + Traces |

### Phase 2: Discover and Scope

**Never guess metric names, log field names, or service names.** Discovery is not optional — it prevents the single most common investigation failure: drawing conclusions from empty results caused by wrong names.

**Dispatch discovery helpers in parallel** for ALL available backends. Read each helper prompt file and run them as subagents when delegation is permitted. Include in each helper task:

- The prompt file content
- Target namespace and/or service name (from Phase 1 findings)
- Time range for the investigation (RFC3339 format)
- Available operations and transport configuration per backend, exact target/tenant, permitted tools, and query budget
- Any specific keywords or components to search for
- Required output format

| Helper | Condition |
|----------|-----------|
| Metrics discovery | `VM_METRICS_URL` available or a VictoriaMetrics MCP is permitted |
| Logs discovery | `VM_LOGS_URL` available or a VictoriaLogs MCP is permitted |
| Traces discovery | `VM_TRACES_URL` available or a VictoriaTraces MCP is permitted |

**Synthesize discovery results:**

- Merge discovered names across all backends
- Note which backends have data for the target and which don't
- Identify the richest signal source for Phase 3 hypothesis testing

**Consult skill references for complex queries.** You do NOT know LogsQL syntax from training data — it is NOT Loki LogQL. For complex queries beyond what the subagents already ran, invoke the corresponding `*-query` skill or use the LogsQL Quick Reference below.

### Phase 3: Hypothesize and Test

After discovery, form a specific hypothesis before querying further.

**State it clearly:** "I think [component X] is [failing/slow/OOM] because [evidence Y from Phase 1]."

**Test minimally:**

- Query ONE thing to confirm or refute the hypothesis
- Don't query everything at once — you'll drown in data
- Use instant queries first (cheaper, faster) before range queries

**If the hypothesis is wrong:**

- Don't add more queries on top — form a NEW hypothesis
- Re-examine what Phase 1 and Phase 2 revealed
- Ask: did discovery show anything unexpected?

**After 3 failed hypotheses: STOP.**
Three wrong guesses means you're missing something fundamental. Either:

- A key data source hasn't been discovered yet
- The scope is wrong (different namespace, different service, different time range)
- You need to ask the user for more context

### Phase 4: Correlate and Confirm

A single signal type is not proof. Correlate across at least two before concluding.

**Dispatch correlation helpers in parallel** for the signal types you need. Reuse the same helper prompt files from `agents/`, but provide specific queries rather than discovery tasks. Include in each helper task:

- The prompt file content
- The specific query to run (metric expression, log filter, trace search parameters)
- The exact time range to query (narrowed from Phase 3 findings)
- Available operations and transport configuration per backend, exact target/tenant, permitted tools, and query budget
- What to look for (the confirmed hypothesis from Phase 3)
- Required output format

Example parallel dispatch for correlation:

- Metrics helper: run `rate(http_requests_total{code=~"5..", namespace="myapp"}[5m])` from T1 to T2
- Logs helper: search `{namespace="myapp"} error` from T1 to T2, return sample messages
- Traces helper: "Search traces for service `myapp` with `minDuration=1s` from T1 to T2"

**Correlation techniques:**

- **Time-based**: Identify anomaly timestamp in metrics, query logs/traces at that time
- **Trace ID**: Find trace IDs in traces, search logs for `trace_id:"<id>"`
- **Pod name**: Get pod name from metrics labels, use it in log stream filters

**Only after correlation:** propose root cause and remediation.

## Red Flags — STOP and Return to Phase 1

If you catch yourself:

- Proposing a root cause after querying only one signal type
- Writing a LogsQL query from memory without checking syntax
- Querying a metric name you haven't confirmed exists via discovery
- Getting empty results and concluding "no problem"
- Skipping the alerts check because "it's probably not that"
- Running five different queries hoping one shows something
- Saying "let me just try..." instead of forming a hypothesis

**All of these mean: STOP. You're guessing, not investigating.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I know the metric name" | Maybe. Discovery takes 2 seconds and prevents 20 minutes of chasing empty results. |
| "Alerts won't help here" | Alerts are free to check and frequently contain the exact answer. Skip at your peril. |
| "Just need to check logs quickly" | Quick log checks without discovery produce wrong field names and misleading results. |
| "Empty results = no problem" | Empty results more often mean wrong query than absent problem. Verify names first. |
| "I'll correlate later" | Single-signal conclusions are guesses. Correlate before claiming root cause. |
| "LogsQL is like LogQL/Elasticsearch" | It's not. The syntax differences cause silent failures. Consult the reference. |

## Environment

HTTP targets are configured through env vars; MCP targets are configured separately. Check availability without printing URLs that might contain credentials:

```bash
echo "VM_METRICS_URL:      ${VM_METRICS_URL:+configured}"
echo "VM_LOGS_URL:         ${VM_LOGS_URL:+configured}"
echo "VM_TRACES_URL:       ${VM_TRACES_URL:+configured}"
echo "VM_ALERTMANAGER_URL: ${VM_ALERTMANAGER_URL:+configured}"
echo "VM_CURL_CONFIG:      ${VM_CURL_CONFIG:+configured}"
```

If unsure which environment the application runs in, ask user.

## Subagent / helper dispatch

This skill dispatches parallel helpers at phase boundaries to speed up investigations. Each helper carries embedded API reference and returns structured findings. Run them via the agent's native delegation mechanism when it is available and permitted; otherwise execute the same steps sequentially in the main agent.

### Env Var and MCP Gating

Before each dispatch round, check which backends are available:

```bash
echo "METRICS:${VM_METRICS_URL:+available}"
echo "LOGS:${VM_LOGS_URL:+available}"
echo "TRACES:${VM_TRACES_URL:+available}"
echo "ALERTMANAGER:${VM_ALERTMANAGER_URL:+available}"
```

Discover matching permitted MCP operations and their schemas, even if the corresponding `VM_*_URL` is unset. A connected server alone does not prove that a particular operation is supported. Choose transport per operation, so VM alerts may use MCP while AlertManager uses HTTP.

**Only dispatch helpers with configured, permitted access for at least one relevant operation.** Let the helper report whether requests succeed; do not assume configuration proves connectivity. Do not dispatch if neither HTTP nor MCP access is available, or use another transport to bypass denied access.

### How to Dispatch

1. Read the helper prompt file from the `agents/` directory (relative to this skill's directory)
2. Run the helper as a subagent when supported (OpenCode `subagent`, Claude `Agent`), including:
   - The prompt file content as the base instructions
   - Investigation context: target namespace, service name, time range (RFC3339)
   - Available operations and transport configuration per backend, exact target/tenant, permitted tools, and query budget
   - Any specific queries or metrics to look for
   - Required output format
3. If the agent does not support delegation or delegation is denied, run the same prompt content sequentially in the main agent.

Pass this transport policy and the helper's output format explicitly. Helpers start with fresh context and their own permissions. The files below are task templates, not automatically registered OpenCode agent profiles; use an existing suitable agent when permitted.

### Agent / helper files

| Helper | File | Requires | Used in |
|-------|------|----------|---------|
| AlertManager check | `agents/alertmanager-check.md` | At least one permitted VM alerts or AlertManager operation via MCP or configured HTTP | Phase 1 |
| Metrics discovery | `agents/metrics-discovery.md` | `VM_METRICS_URL` or permitted VictoriaMetrics MCP | Phase 2, 4 |
| Logs discovery | `agents/logs-discovery.md` | `VM_LOGS_URL` or permitted VictoriaLogs MCP | Phase 2, 4 |
| Traces discovery | `agents/traces-discovery.md` | `VM_TRACES_URL` or permitted VictoriaTraces MCP | Phase 2, 4 |

## Skill-to-API Mapping

```
victoriametrics-query  = Metrics only (MetricsQL/PromQL) → $VM_METRICS_URL
victorialogs-query     = Logs only (LogsQL)              → $VM_LOGS_URL
victoriatraces-query   = Traces only (Jaeger API)        → $VM_TRACES_URL
alertmanager-query     = AlertManager (silences, routing) → $VM_ALERTMANAGER_URL
```

Never cross APIs between backends. Use the correct env var and endpoint for each data type.

AlertManager provides what VM alerts cannot: **silences** and **inhibition state**. If it is unavailable, independently query VM alerts when permitted, and report that silence/inhibition data is missing. VM alerts do not replace those operations or justify bypassing an AlertManager access denial.

## Timestamp Formats

| Backend | Parameter | Format | Example |
|---------|-----------|--------|---------|
| VictoriaMetrics | start/end | RFC3339 string | `2026-02-06T09:00:00Z` |
| VictoriaLogs | start (REQUIRED), end | RFC3339 string | `2026-02-06T09:00:00Z` |
| VictoriaTraces | start/end | Unix microseconds NUMBER | `1738836000000000` (16 digits) |
| VictoriaTraces (dependencies) | endTs/lookback | Unix milliseconds NUMBER | `1738836000000` (13 digits) / `3600000` |

This table describes HTTP examples, not MCP tool schemas. Bound log discovery and range requests with explicit `start`/`end`. Instant `stats_query` instead uses `time` plus a bounded `_time:` filter; never leave the log window unbounded.

## Discovery Protocol

Follow this order for each signal type. For full API details and additional endpoints, invoke the corresponding query skill.

### Metrics Discovery → `victoriametrics-query` skill

1. **Search metadata** by keyword: `$VM_METRICS_URL/api/v1/metadata?metric=<keyword>&limit=10`
2. **Label values** for scoping: `$VM_METRICS_URL/api/v1/label/<label_name>/values` (filter with `match[]`)
3. **Series** for a namespace: `$VM_METRICS_URL/api/v1/series?limit=20` with `match[]={namespace="X"}`
4. **Then query** — instant at `api/v1/query` or range at `api/v1/query_range` (range requires `start`, RFC3339)

### Logs Discovery → `victorialogs-query` skill

For the HTTP discovery and query endpoints below, provide explicit `start` and `end` (RFC3339). Use `--data-urlencode` for the query parameter. Instant stats use `time` and a bounded `_time:` filter instead; adapt MCP calls to their discovered schemas.

1. **Stream field names**: `$VM_LOGS_URL/select/logsql/stream_field_names?start=<RFC3339_start>&end=<RFC3339_end>`
2. **Stream field values**: `$VM_LOGS_URL/select/logsql/stream_field_values?start=<RFC3339_start>&end=<RFC3339_end>&field=namespace`
3. **Facets** (best discovery tool — all field distributions in one call): `$VM_LOGS_URL/select/logsql/facets?start=<RFC3339_start>&end=<RFC3339_end>`
4. **Non-stream field names**: `$VM_LOGS_URL/select/logsql/field_names?start=<RFC3339_start>&end=<RFC3339_end>`
5. **Then query** (JSON Lines response): `$VM_LOGS_URL/select/logsql/query?start=<RFC3339_start>&end=<RFC3339_end>&limit=100`

### Traces Discovery → `victoriatraces-query` skill

Service and operation discovery endpoints accept no time-range parameters. Dependency and trace searches use the supplied incident bounds:

1. **List services**: `$VM_TRACES_URL/api/services`
2. **Operations for a service**: `$VM_TRACES_URL/api/services/<service>/operations`
3. **Dependencies** (Unix milliseconds): `$VM_TRACES_URL/api/dependencies?endTs=<incident_end_ms>&lookback=<incident_duration_ms>`
4. **Then search traces** (`service` required, times in Unix microseconds, 16 digits): `$VM_TRACES_URL/api/traces?service=<svc>&start=<µs>&end=<µs>&limit=20`

## LogsQL Quick Reference

For full LogsQL syntax, invoke the `victorialogs-query` skill. Key points:

- LogsQL is space-separated (AND by default). Pipes use `|`.
- Stream filters: `{namespace="myapp"}`
- Word filters: `{namespace="myapp"} error`
- OR: `(error OR warning)`, Regex: `~"err|warn"`, Field-specific: `level:error`
- Time filter: `_time:1h` (alternative to API `start`/`end` params — use one OR the other, never both)
- Negation: `-"expected error"`
- Stats: `| stats by (level) count() as total`

**Common mistakes:** `| grep` does NOT exist (use word filters or `~"regex"`). `| filter` is valid ONLY after `| stats`. Stream field names depend on ingestion config — discover them first.

## Investigation Playbooks

### "Application is slow"

1. **Phase 1**: Check alerts. Establish timeline — when did latency increase?
2. **Phase 2**: Discover traced services and metrics matching the app
3. **Phase 3**: Hypothesize — "latency is in [service X] based on [alert/user report]"
   - Query latency/error rate metrics for that service
   - Search traces with `minDuration` filter to find slow spans
4. **Phase 4**: Correlate trace timestamps with logs around those times

### "Pod crash looping"

1. **Phase 1**: Check alerts (may already show KubePodCrashLooping). Get pod name.
2. **Phase 2**: Discover metrics for restart counts, memory usage. Discover log streams for the pod.
3. **Phase 3**: Hypothesize — OOM? Liveness probe failure? Startup crash?
   - Regular interval crashes → liveness probe. Memory spike before crash → OOM.
4. **Phase 4**: Correlate error logs with metric timestamps to confirm cause.

### "Resource growing"

1. **Phase 1**: Check alerts. How fast is it growing?
2. **Phase 2**: Discover resource usage metrics for the namespace/pod
3. **Phase 3**: Hypothesize — leak? Increased load? Missing limits?
   - Use `deriv()` or `increase()` to quantify growth rate
   - Check per-pod breakdown to isolate the culprit
4. **Phase 4**: Correlate with deployment events in logs. Did growth start after a deploy?

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Guessing metric names | Use metadata endpoint: `$VM_METRICS_URL/api/v1/metadata?metric=keyword` |
| Writing LogsQL from memory | Consult LogsQL Quick Reference above or victorialogs-query skill |
| Wrong timestamp format | See Timestamp Formats table above |
| Skipping alerts check | Query available, permitted VM alerts and/or AlertManager operations first |
| Empty results → "no problem" | Verify metric/field names exist via discovery first |
| Not using `facets` for log exploration | `facets` returns field distributions in one call |
| Not URL-encoding queries | Use `--data-urlencode 'query=...'` for POST requests |
| Unbounded VictoriaLogs window | Use explicit `start`/`end`, or a bounded `_time:` filter with `time` for instant stats |
| Copying HTTP parameters into MCP calls | HTTP selectors use `match[]`; MCP may use `match`. Follow the actual tool schema |
| Wrong timestamp type for traces | Search uses MICROSECONDS (16 digits), dependencies use MILLISECONDS (13 digits) |
| Confusing `stats_query` vs `stats_query_range` | Instant uses `time`, range uses `start`/`end`/`step` |
| Mixing `_time:` filter with API `start` | Use one OR the other, never both |
| Searching "error" catching vmselect noise | Add `-"vm_slow_query_stats"` to exclude PromQL text |
| Grouping logs by `cluster` field | Vector logs lack `cluster` stream field — use `kubernetes.pod_namespace` |
| Blocking on AlertManager failure | Use VM alerts as primary, AlertManager as best-effort |
| Single-signal conclusion | Correlate across at least two signal types before claiming root cause |
