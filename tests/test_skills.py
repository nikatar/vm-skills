"""Offline packaging and trace CLI smoke checks: python3 tests/test_skills.py.

These checks do not validate agent behavior, live MCP access, or full YAML syntax.
"""

import ast
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
TOOLS = {
    "investigating-with-observability": "Bash(curl:*), Bash(jq:*), Bash(date:*), Agent, Read",
    "stream-aggregation-helper": "Bash(curl:*), Bash(jq:*)",
    "victoriametrics-cardinality-analysis": "Bash(curl:*), Bash(jq:*), Bash(date:*)",
    "victoriametrics-unused-metrics-analysis": "Bash(curl:*), Bash(jq:*)",
    "vm-trace-analyzer": "Bash(python3:*), Read",
    "victoriametrics-docs": "Bash(python3:*), Read",
    "alertmanager-query": "Bash(curl:*), Bash(jq:*), Bash(date:*)",
    "victorialogs-query": "Bash(curl:*), Bash(jq:*), Bash(date:*)",
    "victoriametrics-query": "Bash(curl:*), Bash(jq:*), Bash(head:*)",
    "victoriatraces-query": "Bash(curl:*), Bash(jq:*), Bash(date:*)",
    "vmanomaly-config": "Bash(curl:*), Bash(jq:*), Read",
    "vmanomaly-query": "Bash(curl:*), Bash(jq:*)",
    "vmanomaly-review": "Bash(curl:*), Bash(jq:*), Read",
}


def main():
    skills = list((ROOT / "plugins").rglob("SKILL.md"))
    assert {p.parent.name for p in skills} == set(TOOLS)
    assert len(skills) == len(TOOLS)
    for path in skills:
        _, header, body = path.read_text().split("---", 2)
        assert f"name: {path.parent.name}\n" in header, path
        assert "description:" in header and body.strip(), path
        assert f"allowed-tools: {TOOLS[path.parent.name]}\n" in header, path
        if path.parent.name == "vm-trace-analyzer":
            assert "argument-hint: trace.json\n" in header
            assert "disable-model-invocation: true\n" in header
            assert "metadata:\n  opencode/autoinvoke: true\n" in header
    for path in (ROOT / "plugins").rglob("*.md"):
        for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if not link.startswith(("http:", "https:", "#")):
                assert (path.parent / link.split("#", 1)[0]).exists(), (path, link)
    for path in ROOT.rglob("*.py"):
        ast.parse(path.read_text(), filename=str(path))
    for path in ROOT.glob("**/.claude-plugin/*.json"):
        json.loads(path.read_text())

    parser = ROOT / "plugins/diagnostics/skills/vm-trace-analyzer/scripts/parse_trace.py"
    with tempfile.TemporaryDirectory(prefix="vm-skills-check-") as directory:
        fixture = Path(directory) / "trace.json"
        for prefix, endpoint, mode in (
            ("vmselect-v1.130.0: /select/0/prometheus", "query_range", "cluster"),
            ("victoria-metrics-v1.130.0: ", "query", "single-node"),
        ):
            fixture.write_text(json.dumps({
                "message": f'{prefix}/api/v1/{endpoint}: query="up" series=1',
                "duration_msec": 2,
                "children": [{"message": "fetch matching series", "duration_msec": 1}],
            }))
            for args, expected in (([], mode), (["tree", "--depth", "1"], "[2.0ms]"),
                                   (["nodes", "--pattern", "fetch matching"], "fetch matching series")):
                result = subprocess.run([sys.executable, str(parser), str(fixture), *args],
                                        check=True, capture_output=True, text=True)
                assert expected in result.stdout, result.stdout
    print(f"OK: {len(skills)} skill headers/resources, Python/JSON syntax, trace CLI modes")


if __name__ == "__main__":
    main()
