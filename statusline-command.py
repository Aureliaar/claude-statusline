#!/usr/bin/env python3
"""Claude Code status line: context summary + session cost"""
import sys, json, os

sys.stdout.reconfigure(encoding="utf-8")

d = json.loads(sys.stdin.read())

cw = d.get("context_window", {})
cu = cw.get("current_usage", {})
sid = d.get("session_id", "unknown")

pct = cw.get("used_percentage", 0)
size = cw.get("context_window_size", 0)
last_call = (
    cu.get("cache_read_input_tokens", 0)
    + cu.get("cache_creation_input_tokens", 0)
    + cu.get("input_tokens", 0)
    + cu.get("output_tokens", 0)
)
cost = d.get("cost", {}).get("total_cost_usd", 0.0)

# Baseline (sys estimate from first call of session)
base_dir = os.path.expanduser("~/.claude/statusline-baselines")
os.makedirs(base_dir, exist_ok=True)
base_file = os.path.join(base_dir, sid)

if os.path.exists(base_file):
    with open(base_file) as f:
        try:
            sys_est = int(f.read().strip())
        except Exception:
            sys_est = last_call
else:
    sys_est = last_call
    with open(base_file, "w") as f:
        f.write(str(sys_est))


def fmt(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}k"
    return str(n)


if pct >= 80:
    color = "\033[0;31m"
elif pct >= 50:
    color = "\033[0;33m"
else:
    color = "\033[0;32m"
reset = "\033[0m"

print(
    f"{color}{pct}%{reset} of {fmt(size)}"
    f" · last {fmt(last_call)} (sys ~{fmt(sys_est)})"
    f" · ${cost:.2f}"
)
