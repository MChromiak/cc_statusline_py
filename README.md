# ccstatusline-py

A Python/uv port of [ccstatusline](https://github.com/sirmalloc/ccstatusline) — customizable statusline for Claude Code CLI. No Node.js required.

## Installation

Install from PyPI with uv (recommended) — puts a `ccstatusline` binary on your PATH:

```bash
uv tool install ccstatusline-py
```

Or run it ad-hoc without installing:

```bash
uvx --from ccstatusline-py ccstatusline
```

To install the latest unreleased version directly from GitHub:

```bash
uv tool install --python 3.11 git+https://github.com/MChromiak/cc_statusline_py.git
```

## Claude Code integration

Add to `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "ccstatusline",
    "padding": 0
  }
}
```

(If you didn't `uv tool install` and want to run on demand, use `"command": "uvx --from ccstatusline-py ccstatusline"` instead.)

## Configuration

Run interactively to configure visually:

```bash
ccstatusline
```

(If you didn't `uv tool install`, use `uvx --from ccstatusline-py ccstatusline` instead.)

Config is saved to `~/.config/ccstatusline-py/settings.toml`. Existing configs from the original ccstatusline (JSON) or from earlier `ccstatusline_py/` (underscore) installs are migrated automatically on first run.

## Examples

Each example below is a complete `~/.config/ccstatusline-py/settings.toml`. Available widget types include `model`, `cwd`, `git_branch`, `git_status`, `context_pct`, `context_bar`, `session_cost`, `session_duration`, `tokens_used`, `burn_rate`, `block_reset_timer`, `separator`, and more.

### 1. Minimal — model name and git branch

```toml
color_level = "none"
minimalist_mode = true

[powerline]
enabled = false

[[lines]]
widgets = [
  { type = "model", padding = 0 },
  { type = "separator", padding = 1 },
  { type = "git_branch", padding = 0 },
]
```

Renders as:

```
claude-sonnet-4-5  │  main
```

### 2. Powerline — model, branch, context bar, cost

```toml
color_level = "truecolor"

[powerline]
enabled = true
separator = ""
left_cap = ""
right_cap = ""

[[lines]]
widgets = [
  { type = "model",        fg = "#ffffff", bg = "#005f87", padding = 1 },
  { type = "git_branch",   fg = "#1e1e2e", bg = "#a6e3a1", padding = 1 },
  { type = "context_bar",  fg = "#1e1e2e", bg = "#f9e2af", padding = 1 },
  { type = "session_cost", fg = "#1e1e2e", bg = "#f5c2e7", padding = 1 },
]
```

Renders coloured powerline-style segments:

```
 claude-sonnet-4-5  main  ████░░░░░░  $0.0234
```

(With a Nerd Font, the segment caps are rendered as connected arrows.)

### 3. Two-line — overview line + project line

```toml
color_level = "256"

[powerline]
enabled = false

[[lines]]
widgets = [
  { type = "model",        fg = "#5fafff", padding = 0 },
  { type = "separator",    padding = 1 },
  { type = "context_pct",  fg = "#ffaf00", padding = 0 },
  { type = "separator",    padding = 1 },
  { type = "session_cost", fg = "#aaffaa", padding = 0 },
]

[[lines]]
widgets = [
  { type = "cwd",        fg = "#888888", padding = 0 },
  { type = "separator",  padding = 1 },
  { type = "git_branch", fg = "#ff87d7", padding = 0 },
  { type = "git_status", fg = "#ffaf00", padding = 1 },
]
```

Renders two lines:

```
claude-sonnet-4-5  │  42.5%  │  $0.0234
~/projects/myapp  │  main ✔
```

## Requirements

- Python 3.11+
- uv
