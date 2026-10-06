# VictoriaMetrics skills

A collection of portable [Agent Skills](https://agentskills.io/) for interacting with the VictoriaMetrics ecosystem.
These skills help AI agents and automation tools understand, operate, and troubleshoot VictoriaMetrics products such as metrics, logs, and traces storage.

They follow the open [Agent Skills](https://agentskills.io/) format and are intended for:

- **Claude Code** (via the Claude plugin marketplace or `npx skills`)
- **OpenCode** (via `@skill-id` or `.opencode/skills`)

> The skills use the same `SKILL.md` format for any Agent Skills-compatible agent. Invocation and configuration differ per agent.

## Available Plugins

| Plugin | Skills | Purpose |
|--------|--------|---------|
| [query](plugins/query/) | victoriametrics-query, victorialogs-query, victoriatraces-query, alertmanager-query | Query metrics, logs, traces, and alerts |
| [diagnostics](plugins/diagnostics/) | vm-trace-analyzer, investigating-with-observability, victoriametrics-cardinality-analysis, victoriametrics-unused-metrics-analysis, stream-aggregation-helper | Query trace analysis, multi-signal investigations, cardinality optimization, unused metric detection, stream aggregation design |
| [vmanomaly](plugins/vmanomaly/) | vmanomaly-query, vmanomaly-config, vmanomaly-review | Operate the vmanomaly API, build and tune anomaly-detection configurations, and review detection quality |
| [docs](plugins/docs/) | victoriametrics-docs | Look up a command-line flag, an HTTP API path or a query construct in the published documentation |

## Installation

### Via [skills.sh](https://skills.sh)

Install all skills:

```
npx skills add VictoriaMetrics/skills
```

Install a specific skill:

```
npx skills add VictoriaMetrics/skills --skill victoriametrics-query
npx skills add VictoriaMetrics/skills --skill victorialogs-query
npx skills add VictoriaMetrics/skills --skill victoriatraces-query
npx skills add VictoriaMetrics/skills --skill alertmanager-query
npx skills add VictoriaMetrics/skills --skill victoriametrics-docs
npx skills add VictoriaMetrics/skills --skill investigating-with-observability
npx skills add VictoriaMetrics/skills --skill vm-trace-analyzer
npx skills add VictoriaMetrics/skills --skill victoriametrics-cardinality-analysis
npx skills add VictoriaMetrics/skills --skill victoriametrics-unused-metrics-analysis
npx skills add VictoriaMetrics/skills --skill stream-aggregation-helper
npx skills add VictoriaMetrics/skills --skill vmanomaly-query
npx skills add VictoriaMetrics/skills --skill vmanomaly-config
npx skills add VictoriaMetrics/skills --skill vmanomaly-review
```

### Via Claude Code plugin marketplace

Add the marketplace source:

```
/plugin marketplace add VictoriaMetrics/skills
```

Install plugins:

```
/plugin install query@victoriametrics-tools # Query VictoriaStack components and AlertManager
/plugin install diagnostics@victoriametrics-tools # Troubleshooting and query trace analysis
/plugin install vmanomaly@victoriametrics-tools # Configure, operate, tune, and review anomaly detection
/plugin install docs@victoriametrics-tools # Look up flags, API paths and query constructs in the published docs
```

### For OpenCode

Skills are discovered from `.opencode/skills`, `.agents/skills`, `.claude/skills`, or the global `~/.config/opencode/skills` directory.

Alternatively, clone this repository and add its `plugins` directory to the `skills` array in your existing global `~/.config/opencode/opencode.jsonc` or project configuration. OpenCode discovers the nested skills recursively:

```jsonc
{
  "skills": ["~/path/to/your/checkout/plugins"]
}
```

Replace the example with the actual absolute or `~/` path to your checkout. Merge this entry with existing settings rather than replacing the configuration. Use only one installation method to avoid duplicate skill IDs; no symlinks are needed.

Then mention a skill by ID, e.g. `@victoriametrics-query`.

## Skills

### Query plugin

| Skill | Purpose |
|-------|---------|
| victoriametrics-query | Run PromQL/MetricsQL queries, discover metrics and labels, inspect alerts, rules, TSDB status, and debug configs |
| victorialogs-query | Search logs with LogsQL, run stats queries, discover fields and streams, analyze log volume |
| victoriatraces-query | Discover services and operations, search traces by duration/tags, retrieve traces by ID, map dependencies |
| alertmanager-query | List active/silenced alerts, create and manage silences, check alert inhibition state |

### Diagnostics plugin

| Skill | Purpose |
|-------|---------|
| vm-trace-analyzer | Analyze VictoriaMetrics query trace JSON to diagnose slow queries and produce performance reports |
| investigating-with-observability | Orchestrate multi-signal investigations across metrics, logs, and traces with structured phases |
| victoriametrics-cardinality-analysis | Analyze time series cardinality to find optimization opportunities — unused metrics, high-cardinality labels, histogram bloat |
| victoriametrics-unused-metrics-analysis | Find unused and rarely-queried metrics, then suggest drop rules and relabel configs to reduce waste |
| stream-aggregation-helper | Design vmagent stream aggregation rules — gate, intake, pick interval/output/by-without, generate YAML, plan rollout, verify with `vm_streamaggr_*` |

### Docs plugin

| Skill | Purpose |
|-------|---------|
| victoriametrics-docs | Confirm a command-line flag, an HTTP API path or a MetricsQL/LogsQL construct against the published documentation before naming it |

### vmanomaly plugin

| Skill | Purpose |
|-------|---------|
| vmanomaly-query | Operate vmanomaly v1.30+ HTTP APIs for health, compatibility, schemas, profiling, shared autotune, validation, and bounded detection tasks |
| vmanomaly-config | Triage static alerting versus ML, select and tune a model from real time-series characteristics, and produce validated deployment artifacts |
| vmanomaly-review | Audit an existing configuration against runtime schemas and real data, reproduce detections, and verify proposed fixes |

Each vmanomaly skill is independently installable. When query or diagnostics skills are also
available, the vmanomaly workflows can use them for metric/log discovery, cardinality checks,
existing-alert review, and multi-signal incident correlation.

## Usage by agent

### Claude Code

Once installed, skills are available as slash commands and may be triggered automatically when Claude detects a matching request. `vm-trace-analyzer` retains explicit invocation in Claude Code. The plugin marketplace installation uses these namespaced commands:

```
/query:victoriametrics-query            - query metrics, discover labels, check alerts and rules
/query:victorialogs-query               - search logs, run stats, discover fields
/query:victoriatraces-query             - search traces, discover services, map dependencies
/query:alertmanager-query               - list alerts, manage silences
/diagnostics:vm-trace-analyzer          - perform an analysis of the query performance based on provided trace
/diagnostics:investigating-with-observability - structured multi-signal investigation
/diagnostics:victoriametrics-cardinality-analysis  - cardinality analysis and optimization recommendations
/diagnostics:victoriametrics-unused-metrics-analysis - find unused metrics and suggest drop rules
/diagnostics:stream-aggregation-helper             - design and verify stream aggregation rules
/vmanomaly:vmanomaly-query                         - inspect and operate the vmanomaly API
/vmanomaly:vmanomaly-config                        - build and tune a validated anomaly configuration
/vmanomaly:vmanomaly-review                        - audit an existing anomaly configuration
/docs:victoriametrics-docs                         - check a flag, an API path or a query construct against the docs
```

### OpenCode

Mention the skill ID with `@`:

```
@victoriametrics-query What is the request rate for my-api over the last 6 hours?
@investigating-with-observability Pod X is crash looping — investigate
@victoriametrics-docs Is there a flag to change the retention period?
```

**Example prompts that trigger skills:**

- "What alerts are currently firing?" → `alertmanager-query`
- "Show me error logs for namespace production in the last hour" → `victorialogs-query`
- "Find slow traces for the checkout service" → `victoriatraces-query`
- "What's the request rate for my-api over the last 6 hours?" → `victoriametrics-query`
- "This query is slow, here's the trace JSON — analyze it" → `vm-trace-analyzer`
- "Pod X is crash looping — investigate" → `investigating-with-observability`
- "Which metrics have the highest cardinality?" → `victoriametrics-cardinality-analysis`
- "Find metrics that nobody queries" → `victoriametrics-unused-metrics-analysis`
- "Help me aggregate this high-cardinality metric at vmagent" → `stream-aggregation-helper`
- "Profile this query and choose a vmanomaly model" → `vmanomaly-config`
- "Check whether my persisted vmanomaly state is compatible with v1.30" → `vmanomaly-query`
- "Review why this anomaly model produces too many detections" → `vmanomaly-review`
- "Is there a flag to change the retention period?" → `victoriametrics-docs`

## Transport: MCP first, HTTP fallback

The skills can use either **MCP servers** (when available and permitted) or direct **HTTP** via `curl`.

| Priority | When to use |
|----------|-------------|
| **1. MCP** | A permitted MCP tool covers the exact operation and points at the right environment/tenant. |
| **2. HTTP** | No MCP tool covers the operation, or MCP is unavailable, and the matching `VM_*_URL` is configured. |
| **3. Stop and report** | Neither transport is available for the operation. |

Rules:

- Choose the transport **per operation**, not once for the whole skill.
- When both transports are available for the same operation, prefer MCP.
- An empty result is a valid result — do not switch transports just because a query returns no data.
- A permission denial is not a reason to fall back to HTTP; stop and explain.
- After an error or timeout on a mutating call (silence, reload, task creation), do not blindly retry with the other transport. First confirm whether the operation already executed.
- When switching transports for a backend, keep the **same environment, backend instance, and tenant**. Different backends may use different transports.
- `VM_*_URL` being unset does not mean the service is absent if an MCP server is connected.

## Environment Variables

The HTTP examples in query, diagnostics and vmanomaly skills use `curl` and require the matching URL below. MCP operations do not require these variables.
The `victoriametrics-docs` skill reads the published documentation over HTTP and needs none of them.

```bash
VM_METRICS_URL        # VictoriaMetrics query endpoint (e.g., http://localhost:8428)
VM_LOGS_URL           # VictoriaLogs endpoint (e.g., http://localhost:9428)
VM_TRACES_URL         # VictoriaTraces with /select/jaeger prefix (e.g., http://localhost:10428/select/jaeger)
VM_ALERTMANAGER_URL   # AlertManager endpoint (optional)
VM_ANOMALY_URL        # vmanomaly endpoint, including path prefix if configured (e.g., http://localhost:8490)
VM_CURL_CONFIG        # Path to a mode-0600 curl config file containing the auth header
                      # (leave unset for unauthenticated local instances - defaults to /dev/null)
```

### Authentication setup

Skills pass credentials to `curl` through a [curl config file](https://curl.se/docs/manpage.html#-K)
instead of command-line arguments. This keeps tokens out of process listings, shell history, and
agent transcripts. Every command uses the same pattern:

```bash
curl -q --config "${VM_CURL_CONFIG:-/dev/null}" -s "$VM_METRICS_URL/api/v1/query?query=up"
```

For unauthenticated local instances no setup is needed: when `VM_CURL_CONFIG` is unset, curl reads
`/dev/null` and sends no auth header.

For authenticated instances, create a config file readable only by you and point `VM_CURL_CONFIG` at it:

```bash
mkdir -p "$HOME/.config/victoriametrics"
touch "$HOME/.config/victoriametrics/curl.conf"
chmod 0600 "$HOME/.config/victoriametrics/curl.conf"
cat > "$HOME/.config/victoriametrics/curl.conf" <<'EOF'
header = "Authorization: Bearer <token>"
EOF
export VM_CURL_CONFIG="$HOME/.config/victoriametrics/curl.conf"
```

For Basic auth, use `user = "username:password"` instead of the `header` line.

### Migrating from VM_AUTH_HEADER

Earlier versions of these skills read the auth header from the `VM_AUTH_HEADER` environment variable
(`export VM_AUTH_HEADER="Authorization: Bearer <token>"`) and passed it to curl via `-H`. That exposed
the token in process listings, shell history, and agent transcripts, so skills now read it from a curl
config file instead. `VM_AUTH_HEADER` is no longer used by any skill.

To migrate:

1. Move the header line into a mode-0600 curl config file:

   ```bash
   mkdir -p "$HOME/.config/victoriametrics"
   touch "$HOME/.config/victoriametrics/curl.conf"
   chmod 0600 "$HOME/.config/victoriametrics/curl.conf"
   printf 'header = "%s"\n' "$VM_AUTH_HEADER" > "$HOME/.config/victoriametrics/curl.conf"
   ```

2. Replace `VM_AUTH_HEADER` with `VM_CURL_CONFIG` wherever you export it (shell profile, CI secrets,
   agent configuration):

   ```bash
   export VM_CURL_CONFIG="$HOME/.config/victoriametrics/curl.conf"
   unset VM_AUTH_HEADER
   ```

3. If you never set `VM_AUTH_HEADER` (unauthenticated local instances), no action is needed.

## Subagents and delegation

Some skills (`investigating-with-observability`, `victoriametrics-cardinality-analysis`) can run
discovery work in parallel. They describe the work as independent tasks and can use any supported
delegation mechanism:

- Claude Code: `Agent` tool calls
- OpenCode: `subagent` tool calls

If the current agent does not support delegation, or delegation is not permitted, the same steps
must be executed **sequentially** in the main agent. The skills include fallback instructions for
that case.

Each helper must be given the same context explicitly:

- task scope and limits,
- target environment, endpoint, and tenant,
- time range,
- available operations and transport configuration per backend (MCP tools or HTTP URL),
- output format,
- the relevant agent prompt file content.

## Safety notes

- **Read-only diagnostics and config generation are separate from mutations.** Do not apply configs, reload agents, create persistent alert rules, purge state, expire silences, or cancel/delete tasks without explicit approval. Obtain approval for the query scope, time range, and resource budget before creating autotune or detection tasks.
- **MCP access is not a substitute for permissions.** Agent-level permission rules (OpenCode `permissions`, Claude approval modes) still govern what tools can actually do.
- **`allowed-tools` is agent-specific.** Claude Code uses it to pre-approve matching tools during skill invocation, not as an exclusive allowlist. OpenCode ignores this field; configure actual agent permissions separately. Helpers have their own permissions, so a parent's access is not a grant to a child.
- **Metric cleanup is suggestive.** A metric that appears unused may still be needed by dashboards, recording rules, or seasonal reports. Cross-check before recommending deletion.

## Offline checks

Run `python3 tests/test_skills.py` to check skill headers, resource links, Python/JSON syntax, and the trace parser CLI. These checks do not verify agent behavior, live MCP connections, or end-to-end compatibility.
