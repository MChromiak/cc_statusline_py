# ccstatusline Python — Design Spec

**Date:** 2026-04-22  
**Goal:** Rewrite [ccstatusline](https://github.com/sirmalloc/ccstatusline) as a pure Python/uv project, eliminating the Node.js/npx dependency. Invoked via `uvx ccstatusline`, published to PyPI.

---

## 1. Overview

`ccstatusline` is a customizable statusline formatter for Claude Code CLI. Claude Code calls it as a subprocess, pipes metrics JSON to stdin, and displays the formatted ANSI text it receives on stdout. Users configure it by running `uvx ccstatusline` interactively via a Textual TUI.

**Two operational modes**, detected at startup by checking `sys.stdin.isatty()`:

- **Piped mode** — stdin is piped (Claude Code is calling us). Read JSON → render → write ANSI to stdout. Fast path.
- **Interactive mode** — no piped stdin. Launch the Textual TUI for configuration.

**Claude Code integration** (same as the original):
```json
{
  "statusLine": {
    "type": "command",
    "command": "uvx ccstatusline",
    "padding": 0
  }
}
```

---

## 2. Package Structure

```
ccstatusline/
  __main__.py        # Entry point: mode detection, dispatch
  renderer.py        # ANSI + powerline rendering pipeline
  config.py          # Pydantic config models, TOML load/save, JSON migration
  data.py            # StatusData Pydantic model (maps Claude Code's stdin JSON)
  widgets/
    base.py          # Widget ABC + @register_widget decorator + registry dict
    core.py          # All built-in widgets (imports decorated classes)
  tui/
    app.py           # Textual Application subclass
    screens.py       # Panels: WidgetLibrary, LayoutEditor, Preview, GlobalSettings
pyproject.toml
```

**Dependencies:**
- `textual` — TUI framework
- `rich` — ANSI rendering utilities
- `pydantic` — config + data validation
- `tomli-w` — TOML serialization (write)
- `tomllib` — TOML parsing (stdlib, Python 3.11+)

**Python version requirement:** 3.11+

**Entry point** in `pyproject.toml`:
```toml
[project.scripts]
ccstatusline = "ccstatusline.__main__:main"
```

---

## 3. Widget System

### Base class & registry

```python
# widgets/base.py
REGISTRY: dict[str, type[Widget]] = {}

def register_widget(name: str):
    def decorator(cls: type[Widget]) -> type[Widget]:
        REGISTRY[name] = cls
        return cls
    return decorator

class Widget(ABC):
    @abstractmethod
    def render(self, data: StatusData, config: WidgetConfig) -> str:
        ...
```

Each widget is a class decorated with `@register_widget("name")`. Adding a new widget is: add a class to `core.py` (or a new file imported there), decorate it, done. No other registration needed.

`WidgetConfig` carries per-widget settings: `fg`, `bg`, `bold`, `padding`, and an `options: dict` for widget-specific knobs (e.g. `context_bar` has `bar_width`).

Each `Widget` subclass declares a `category: str` class attribute (e.g. `"tokens"`, `"git"`, `"session"`, `"system"`, `"custom"`). The TUI uses this to group the Widget Library list. The `@register_widget` decorator reads this attribute at registration time.

### StatusData

A Pydantic model mapping the JSON Claude Code pipes in, matching the original's `StatusJSONSchema` (Zod). All fields are optional to handle future schema additions gracefully.

```python
class StatusData(BaseModel):
    hook_event_name: str | None = None
    session_id: str | None = None
    transcript_path: str | None = None
    cwd: str | None = None
    model: str | dict | None = None       # string or {"id": ..., "display_name": ...}
    version: str | None = None
    output_style: str | None = None
    workspace: dict | None = None         # {"current_dir": ..., "project_dir": ...}
    cost: dict | None = None              # {"total_cost_usd": ..., "total_duration_ms": ..., ...}
    context_window: dict | None = None    # {"context_window_size": ..., "total_input_tokens": ...,
                                          #  "total_output_tokens": ..., "current_usage": ...,
                                          #  "used_percentage": ..., "remaining_percentage": ...}
    vim: dict | None = None               # {"mode": ...}
    worktree: dict | None = None          # {"name": ..., "path": ..., "branch": ..., ...}
    rate_limits: dict | None = None       # {"five_hour": {...}, "seven_day": {...}}

    model_config = ConfigDict(extra="allow")  # pass-through unknown fields
```

Widgets access fields via helper properties on `StatusData` (e.g. `data.model_name`, `data.tokens_used`, `data.cost_usd`) that safely extract values from the nested dicts.

### Core widgets (initial release)

| Widget ID | Description |
|---|---|
| `model` | Claude model name |
| `git_branch` | Current git branch |
| `git_status` | Dirty/clean indicator (symbol) |
| `tokens_used` | Input + output token count |
| `context_pct` | Context window % used |
| `context_bar` | ASCII fill bar of context usage |
| `session_duration` | Elapsed time since session start |
| `session_cost` | Estimated session cost (USD) |
| `cwd` | Current working directory (basename or full) |
| `claude_email` | Logged-in Claude account email |
| `custom_text` | Static user-defined string |
| `separator` | Visual spacer / divider |

---

## 4. Config System

### Storage

- **Python version config:** `~/.config/ccstatusline_py/settings.toml`
- **Migration source (read-only):** `~/.config/ccstatusline/settings.json` (original ccstatusline)

### Migration

On first run, if no TOML config exists but the original JSON config does:
1. Read `~/.config/ccstatusline/settings.json`
2. Map known fields to the TOML schema (widgets that exist in the Python version are mapped; unknown ones are dropped with a stderr warning)
3. Save migrated config to TOML
4. Leave the original JSON untouched

### TOML schema

```toml
color_level = "truecolor"   # "none" | "basic" | "256" | "truecolor"
minimalist_mode = false

[powerline]
enabled = true
separator = ""             # Nerd Font right-arrow glyph (U+E0B0)
thin_separator = ""        # U+E0B1
left_cap = ""              # U+E0B2
right_cap = ""             # U+E0B0

[[lines]]
[[lines.widgets]]
type = "model"
fg = "#a6e3a1"
bg = "#1e1e2e"
bold = true

[[lines.widgets]]
type = "git_branch"
fg = "#cba6f7"
bg = "#1e1e2e"
```

Multiple `[[lines]]` entries produce multiple statusline rows (same as the original's multi-line support).

### Config class

```python
class Config(BaseModel):
    color_level: Literal["none", "basic", "256", "truecolor"] = "truecolor"
    minimalist_mode: bool = False
    powerline: PowerlineConfig = PowerlineConfig()
    lines: list[LineConfig] = []

    @classmethod
    def load(cls) -> "Config": ...   # TOML → Pydantic, with JSON migration fallback
    def save(self) -> None: ...      # Pydantic → TOML via tomli-w
```

---

## 5. Renderer

The renderer takes `Config` + `StatusData` and produces the final ANSI string.

### Pipeline

1. For each configured line:
   a. Instantiate each widget from the registry by `type` key
   b. Call `widget.render(data, widget_config)` → raw string segment
   c. If a segment is empty string, skip it (widget has nothing to show)
2. Wrap each segment in ANSI color escapes (fg + bg), respecting `color_level`
3. If powerline enabled: insert the separator glyph between adjacent segments, with the left segment's bg color as the separator's fg — matching the original's color-inheritance logic
4. Prepend left cap / append right cap if configured
5. Pad line to terminal width if `minimalist_mode` is false (using `shutil.get_terminal_size()`)
6. Join lines with `\n`, write to stdout

### Color handling

The original stores color level as an integer (0–3) in its JSON config. The Python version uses descriptive strings in TOML for readability — the mapping is:

| TOML string | Original int | Behavior |
|---|---|---|
| `"none"` | 0 | No color output |
| `"basic"` | 1 | Map hex to nearest ANSI 16-color via Euclidean distance |
| `"256"` | 2 | Map hex to nearest xterm-256 palette index |
| `"truecolor"` | 3 | Emit `\x1b[38;2;R;G;Bm` / `\x1b[48;2;R;G;Bm` directly |

The JSON migration step maps the original integer to the corresponding string.

### Powerline glyphs

Written as Unicode code points directly into the output string. The renderer has no font awareness — it trusts the terminal has Nerd Fonts installed.

### Width calculation

Strip ANSI escapes (regex `\x1b\[[0-9;]*m`) from each segment to get visible character width. Use this to calculate padding for flex alignment.

---

## 6. TUI (Textual App)

Launched when `sys.stdin.isatty()` is True. Structured as a single Textual `App` with a persistent layout:

### Panels

**Left — Widget Library**
- Scrollable list of all widgets from the registry, grouped by category
- Click a widget to append it to the active line

**Center — Layout Editor**
- Shows widgets in the active line as reorderable items
- Arrow keys or drag to reorder; Delete/Backspace to remove
- Click a widget to open a detail panel: fg/bg color pickers, bold toggle, padding, widget-specific options

**Bottom — Live Preview**
- Read-only render of the full statusline using current config + hardcoded sample data (representative values for each `StatusData` field)
- Updates live on every config change

**Top bar**
- Tab row: Line 1, Line 2, … + "+" to add a line
- "Settings" button opens global settings overlay (color level, powerline on/off, minimalist mode)

### Keybindings

| Key | Action |
|---|---|
| `Ctrl+S` | Save config to TOML and exit |
| `Escape` | Prompt to discard changes and exit |
| `Tab` / `Shift+Tab` | Switch between lines |
| `Delete` | Remove selected widget |

---

## 7. Error Handling

- **Piped mode:** If stdin JSON fails Pydantic validation, write an empty string to stdout (don't crash Claude Code's statusline). Log the error to stderr for debugging.
- **Missing widget type in registry:** Skip the widget silently in piped mode; show a warning label in the TUI.
- **Config load failure:** Fall back to an empty default config and warn on stderr.
- **TUI crash:** Let Textual handle it with its built-in crash screen — don't suppress exceptions in interactive mode.

---

## 8. Testing Strategy

- **Unit tests** for each widget's `render()` with mock `StatusData`
- **Unit tests** for the renderer's ANSI output (strip escapes, check visible text)
- **Unit tests** for config load/save round-trip and JSON migration
- **No TUI tests** in the initial release (Textual has its own testing utilities but adds complexity; add later)

Test runner: `pytest` via `uv run pytest`.
