# claude-statusline

A Claude Code status line showing context window usage, per-turn token counts, session cost, and real 5h/7d usage percentages pulled from the Anthropic API.

## What it displays

```
11% of 1.0M · last 36.5k (sys ~12.1k) · $1.06 · 5h 11% · 7d 4%
```

| Field | Meaning |
|-------|---------|
| `11%` | Context window used (green < 50%, yellow < 80%, red ≥ 80%) |
| `1.0M` | Total context window size for this session |
| `last 36.5k` | Tokens consumed this turn (input + output + cache read + cache creation) |
| `sys ~12.1k` | Estimated system prompt size — captured from the first call of the session |
| `$1.06` | Cumulative estimated cost of the whole session so far |
| `5h 11%` | Real 5-hour usage window % (same as claude.ai/settings/usage) |
| `7d 4%` | Real 7-day usage window % (same as claude.ai/settings/usage) |

The 5h/7d values are fetched from `https://api.anthropic.com/api/oauth/usage` using the OAuth token Claude Code already stores locally. Results are cached for 5 minutes so the API isn't hit on every turn.

## Files

| File | Purpose |
|------|---------|
| `statusline-command.py` | Main script — reads JSON from stdin, writes one ANSI-colored line to stdout |
| `statusline-command.sh` | Thin shell wrapper invoked by the Claude Code hook |
| `settings-snippet.json` | The `statusLine` block to merge into `~/.claude/settings.json` |

## Installation

1. Copy scripts to `~/.claude/`:

```bash
cp statusline-command.py ~/.claude/statusline-command.py
cp statusline-command.sh ~/.claude/statusline-command.sh
chmod +x ~/.claude/statusline-command.sh
```

2. Merge the `statusLine` key into `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash \"$HOME/.claude/statusline-command.sh\""
  }
}
```

3. Start a new Claude Code session. The status line appears below the input prompt after every turn.

## How it works

Claude Code's `statusLine` hook fires after each assistant turn and pipes a JSON payload to the configured command via stdin:

```json
{
  "session_id": "abc123",
  "context_window": {
    "used_percentage": 11,
    "context_window_size": 1000000,
    "current_usage": {
      "input_tokens": 5000,
      "output_tokens": 1200,
      "cache_read_input_tokens": 10000,
      "cache_creation_input_tokens": 2100
    }
  },
  "cost": { "total_cost_usd": 1.06 }
}
```

For usage windows, the script calls `GET https://api.anthropic.com/api/oauth/usage` with the OAuth token from `~/.claude/.credentials.json` (written by Claude Code at login). The response:

```json
{
  "five_hour":  { "utilization": 11.0, "resets_at": "..." },
  "seven_day":  { "utilization":  4.0, "resets_at": "..." }
}
```

Results are cached to `~/.claude/statusline-usage-cache.json` for 5 minutes. If the fetch fails for any reason (offline, token expired), the `5h`/`7d` fields are silently omitted.

## Persistent state

| File | Contents |
|------|----------|
| `~/.claude/statusline-baselines/<session_id>` | First-turn token count used as system prompt size estimate |
| `~/.claude/statusline-usage-cache.json` | Cached 5h/7d utilization with timestamp (5 min TTL) |

## Requirements

- Python 3.7+ (`sys.stdout.reconfigure`, f-strings)
- Claude Code CLI with status line support (logged in with a Max plan account)
- `bash` on PATH (macOS/Linux native; Windows: use WSL or Git Bash)
