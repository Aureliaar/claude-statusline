# claude-statusline

A minimal Claude Code status line that shows context window usage, per-turn token counts, and cumulative session cost.

## What it displays

```
42% of 200.0k · last 18.3k (sys ~12.1k) · $1.06
```

| Field | Meaning |
|-------|---------|
| `42%` | Context window used (green < 50%, yellow < 80%, red ≥ 80%) |
| `200.0k` | Total context window size for this session |
| `last 18.3k` | Tokens consumed this turn (input + output + cache read + cache creation) |
| `sys ~12.1k` | Estimated system prompt size — captured from the first call of the session |
| `$1.06` | Cumulative estimated cost of the whole session so far |

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

## Persistent state

The script maintains one data file under `~/.claude/`:

- `statusline-baselines/<session_id>` — first-turn token count for each session, used as the system prompt size estimate

## How it works

Claude Code's `statusLine` hook fires after each assistant turn and pipes a JSON payload to the configured command via stdin. The relevant payload shape:

```json
{
  "session_id": "abc123",
  "context_window": {
    "used_percentage": 42,
    "context_window_size": 204800,
    "current_usage": {
      "input_tokens": 5000,
      "output_tokens": 1200,
      "cache_read_input_tokens": 10000,
      "cache_creation_input_tokens": 2100
    }
  },
  "cost": {
    "total_cost_usd": 1.06
  }
}
```

The script:
1. Sums all four token fields → `last`
2. Records the first-call total as a system prompt proxy → `sys`
3. Reads `cost.total_cost_usd` directly → session cost (already cumulative in the payload)

## Requirements

- Python 3.7+ (`sys.stdout.reconfigure`, f-strings)
- Claude Code CLI with status line support
- `bash` on PATH (macOS/Linux native; Windows: use WSL or Git Bash)
