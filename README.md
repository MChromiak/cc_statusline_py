# ccstatusline_py

A Python/uv port of [ccstatusline](https://github.com/sirmalloc/ccstatusline) — customizable statusline for Claude Code CLI. No Node.js required.

## Installation

```bash
uvx ccstatusline
```

## Claude Code integration

Add to `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "uvx ccstatusline",
    "padding": 0
  }
}
```

## Configuration

Run interactively to configure:

```bash
uvx ccstatusline
```

Config is saved to `~/.config/ccstatusline_py/settings.toml`. If you already have a config from the original ccstatusline, it will be migrated automatically on first run.

## Requirements

- Python 3.11+
- uv
