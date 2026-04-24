#!/usr/bin/env python3
"""Claude Code status line: context summary + rolling usage windows"""
import sys, json, os, time

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

# Rolling usage log — append this turn, then compute windows
usage_log = os.path.expanduser("~/.claude/statusline-usage.jsonl")
now = time.time()
with open(usage_log, "a") as f:
    f.write(json.dumps({"t": now, "tokens": last_call}) + "\n")

W5H = 5 * 3600
W7D = 7 * 24 * 3600
cutoff_5h = now - W5H
cutoff_7d = now - W7D

tokens_5h = 0
tokens_7d = 0
kept = []

with open(usage_log) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            t, tok = rec["t"], rec["tokens"]
            if t >= cutoff_7d:
                kept.append(line)
                tokens_7d += tok
                if t >= cutoff_5h:
                    tokens_5h += tok
        except Exception:
            pass

# Trim log to 7-day window
with open(usage_log, "w") as f:
    f.write("\n".join(kept) + ("\n" if kept else ""))


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
    f" · 5h {fmt(tokens_5h)} · 7d {fmt(tokens_7d)}"
)
