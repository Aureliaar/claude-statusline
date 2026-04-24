#!/usr/bin/env python3
"""Claude Code status line: context summary + session cost + real usage windows"""
import sys, json, os, time
import urllib.request, urllib.error

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


def get_usage_windows():
    """Fetch 5h/7d utilization % from Anthropic. Cached for 5 minutes."""
    cache_file = os.path.expanduser("~/.claude/statusline-usage-cache.json")
    now = time.time()

    if os.path.exists(cache_file):
        try:
            with open(cache_file) as f:
                cache = json.load(f)
            if now - cache.get("ts", 0) < 300:
                return cache.get("5h"), cache.get("7d")
        except Exception:
            pass

    creds_file = os.path.expanduser("~/.claude/.credentials.json")
    try:
        with open(creds_file) as f:
            token = json.load(f)["claudeAiOauth"]["accessToken"]
    except Exception:
        return None, None

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/api/oauth/usage",
            headers={
                "Authorization": f"Bearer {token}",
                "anthropic-beta": "oauth-2025-04-20",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        pct_5h = data["five_hour"]["utilization"]
        pct_7d = data["seven_day"]["utilization"]
        with open(cache_file, "w") as f:
            json.dump({"ts": now, "5h": pct_5h, "7d": pct_7d}, f)
        return pct_5h, pct_7d
    except Exception:
        return None, None


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

pct_5h, pct_7d = get_usage_windows()
usage_str = f" · 5h {pct_5h:.0f}% · 7d {pct_7d:.0f}%" if pct_5h is not None else ""

print(
    f"{color}{pct}%{reset} of {fmt(size)}"
    f" · last {fmt(last_call)} (sys ~{fmt(sys_est)})"
    f" · ${cost:.2f}"
    f"{usage_str}"
)
