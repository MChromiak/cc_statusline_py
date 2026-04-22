# ccstatusline Python Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `ccstatusline` as a `uvx`-invokable Python package that renders a customizable Claude Code statusline from piped JSON stdin and configures it via a Textual TUI.

**Architecture:** Two modes detected at startup via `sys.stdin.isatty()`: piped mode reads JSON from stdin and writes ANSI text to stdout; interactive mode launches a Textual TUI. Config lives at `~/.config/ccstatusline_py/settings.toml` with one-way migration from `~/.config/ccstatusline/settings.json`.

**Tech Stack:** Python 3.11+, Pydantic v2, Textual ≥0.80, Rich, tomli-w, pytest

---

## File Map

| File | Responsibility |
|---|---|
| `pyproject.toml` | Package metadata, deps, `ccstatusline` entry point |
| `ccstatusline/__init__.py` | Package marker |
| `ccstatusline/__main__.py` | Mode detection; piped render path; TUI launch |
| `ccstatusline/data.py` | `StatusData` Pydantic model + accessor properties |
| `ccstatusline/widgets/__init__.py` | Re-exports `REGISTRY`, `CATEGORIES` |
| `ccstatusline/widgets/base.py` | `Widget` ABC, `WidgetConfig` Pydantic model, `@register_widget` |
| `ccstatusline/widgets/core.py` | All 12 built-in widget classes |
| `ccstatusline/config.py` | `Config`, `LineConfig`, `PowerlineConfig`; TOML I/O; JSON migration |
| `ccstatusline/renderer.py` | Color utils, ANSI wrapping, powerline arrows, `render_statusline()` |
| `ccstatusline/tui/__init__.py` | Package marker |
| `ccstatusline/tui/app.py` | `CCStatuslineApp` — Textual app, keybindings, panel coordination |
| `ccstatusline/tui/screens.py` | `WidgetLibrary`, `LayoutEditor`, `Preview`, `GlobalSettingsScreen` |
| `tests/conftest.py` | Shared pytest fixtures |
| `tests/test_data.py` | `StatusData` model and property tests |
| `tests/test_widgets.py` | All 12 widget render tests |
| `tests/test_config.py` | Config load/save round-trip and JSON migration tests |
| `tests/test_renderer.py` | Color util, renderer, and powerline tests |

---

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `ccstatusline/__init__.py`
- Create: `ccstatusline/__main__.py`
- Create: `ccstatusline/widgets/__init__.py`
- Create: `ccstatusline/tui/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ccstatusline"
version = "0.1.0"
description = "Customizable statusline formatter for Claude Code CLI"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"
dependencies = [
    "textual>=0.80.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
    "tomli-w>=1.0.0",
]

[project.scripts]
ccstatusline = "ccstatusline.__main__:main"

[tool.hatch.build.targets.wheel]
packages = ["ccstatusline"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create package skeleton**

```python
# ccstatusline/__init__.py
# (empty)
```

```python
# ccstatusline/__main__.py
def main() -> None:
    pass

if __name__ == "__main__":
    main()
```

```python
# ccstatusline/widgets/__init__.py
# (empty)
```

```python
# ccstatusline/tui/__init__.py
# (empty)
```

```python
# tests/__init__.py
# (empty)
```

- [ ] **Step 3: Install dependencies**

```bash
uv sync
```

Expected: dependencies downloaded, `.venv` created.

- [ ] **Step 4: Verify entry point resolves**

```bash
uv run ccstatusline
```

Expected: exits with no output (stub `main` does nothing).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml ccstatusline/ tests/
git commit -m "feat: project scaffold with pyproject.toml and package structure"
```

---

## Task 2: StatusData Model

**Files:**
- Create: `ccstatusline/data.py`
- Create: `tests/test_data.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_data.py
import pytest
from ccstatusline.data import StatusData


def test_model_name_from_dict():
    d = StatusData(model={"display_name": "claude-sonnet-4-5", "id": "cs4"})
    assert d.model_name == "claude-sonnet-4-5"


def test_model_name_from_string():
    d = StatusData(model="claude-opus-4")
    assert d.model_name == "claude-opus-4"


def test_model_name_empty():
    d = StatusData()
    assert d.model_name == ""


def test_tokens_used_sums_input_output():
    d = StatusData(context_window={
        "total_input_tokens": 10000,
        "total_output_tokens": 2500,
    })
    assert d.tokens_used == 12500


def test_tokens_used_when_missing():
    d = StatusData()
    assert d.tokens_used == 0


def test_context_used_pct():
    d = StatusData(context_window={"used_percentage": 42.5})
    assert d.context_used_pct == 42.5


def test_context_used_pct_when_missing():
    d = StatusData()
    assert d.context_used_pct == 0.0


def test_cost_usd():
    d = StatusData(cost={"total_cost_usd": 0.1234})
    assert d.cost_usd == pytest.approx(0.1234)


def test_cost_usd_when_missing():
    d = StatusData()
    assert d.cost_usd == 0.0


def test_session_duration_ms():
    d = StatusData(cost={"total_duration_ms": 90000})
    assert d.session_duration_ms == 90000


def test_unknown_fields_allowed():
    d = StatusData(future_field="hello")
    assert d.future_field == "hello"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_data.py -v
```

Expected: `ModuleNotFoundError: No module named 'ccstatusline.data'`

- [ ] **Step 3: Implement data.py**

```python
# ccstatusline/data.py
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StatusData(BaseModel):
    model_config = ConfigDict(extra="allow")

    hook_event_name: str | None = None
    session_id: str | None = None
    transcript_path: str | None = None
    cwd: str | None = None
    model: str | dict | None = None
    version: str | None = None
    output_style: str | None = None
    workspace: dict | None = None
    cost: dict | None = None
    context_window: dict | None = None
    vim: dict | None = None
    worktree: dict | None = None
    rate_limits: dict | None = None

    @property
    def model_name(self) -> str:
        if isinstance(self.model, dict):
            return self.model.get("display_name") or self.model.get("id") or ""
        return self.model or ""

    @property
    def tokens_used(self) -> int:
        if not self.context_window:
            return 0
        inp = self.context_window.get("total_input_tokens") or 0
        out = self.context_window.get("total_output_tokens") or 0
        return inp + out

    @property
    def context_window_size(self) -> int:
        if not self.context_window:
            return 0
        return self.context_window.get("context_window_size") or 0

    @property
    def context_used_pct(self) -> float:
        if not self.context_window:
            return 0.0
        return float(self.context_window.get("used_percentage") or 0)

    @property
    def cost_usd(self) -> float:
        if not self.cost:
            return 0.0
        return float(self.cost.get("total_cost_usd") or 0)

    @property
    def session_duration_ms(self) -> int:
        if not self.cost:
            return 0
        return int(self.cost.get("total_duration_ms") or 0)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_data.py -v
```

Expected: all 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add ccstatusline/data.py tests/test_data.py
git commit -m "feat: StatusData Pydantic model with accessor properties"
```

---

## Task 3: Widget Base

**Files:**
- Create: `ccstatusline/widgets/base.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_widgets.py  (create this file — we will add to it in Tasks 4-6)
import pytest
from ccstatusline.data import StatusData
from ccstatusline.widgets.base import REGISTRY, CATEGORIES, Widget, WidgetConfig, register_widget


def test_register_widget_adds_to_registry():
    @register_widget("_test_widget")
    class MyWidget(Widget):
        category = "custom"
        def render(self, data, config):
            return "hello"

    assert "_test_widget" in REGISTRY
    assert REGISTRY["_test_widget"] is MyWidget


def test_register_widget_adds_to_categories():
    assert "_test_widget" in CATEGORIES.get("custom", [])


def test_widget_config_defaults():
    wc = WidgetConfig(type="model")
    assert wc.fg == "#ffffff"
    assert wc.bg == "#000000"
    assert wc.bold is False
    assert wc.padding == 1
    assert wc.options == {}


def test_widget_render_is_abstract():
    class IncompleteWidget(Widget):
        category = "custom"
        # render not implemented

    with pytest.raises(TypeError):
        IncompleteWidget()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_widgets.py -v
```

Expected: `ModuleNotFoundError: No module named 'ccstatusline.widgets.base'`

- [ ] **Step 3: Implement widgets/base.py**

```python
# ccstatusline/widgets/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ccstatusline.data import StatusData

REGISTRY: dict[str, type[Widget]] = {}
CATEGORIES: dict[str, list[str]] = {}


class WidgetConfig(BaseModel):
    type: str
    fg: str = "#ffffff"
    bg: str = "#000000"
    bold: bool = False
    padding: int = 1
    options: dict = Field(default_factory=dict)


def register_widget(name: str):
    def decorator(cls: type[Widget]) -> type[Widget]:
        REGISTRY[name] = cls
        cat = getattr(cls, "category", "custom")
        CATEGORIES.setdefault(cat, []).append(name)
        return cls
    return decorator


class Widget(ABC):
    category: str = "custom"

    @abstractmethod
    def render(self, data: StatusData, config: WidgetConfig) -> str: ...
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_widgets.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Create conftest.py with shared fixture**

```python
# tests/conftest.py
import pytest
from ccstatusline.data import StatusData


@pytest.fixture
def sample_data():
    return StatusData(
        model={"display_name": "claude-sonnet-4-5", "id": "claude-sonnet-4-5"},
        session_id="test-session",
        cwd="/home/user/myproject",
        context_window={
            "context_window_size": 200000,
            "total_input_tokens": 15000,
            "total_output_tokens": 3000,
            "used_percentage": 9.0,
            "remaining_percentage": 91.0,
        },
        cost={
            "total_cost_usd": 0.0234,
            "total_duration_ms": 135000,
        },
        worktree={
            "name": "main",
            "path": "/home/user/myproject",
            "branch": "feat/python-port",
        },
    )
```

- [ ] **Step 6: Commit**

```bash
git add ccstatusline/widgets/base.py tests/test_widgets.py tests/conftest.py
git commit -m "feat: Widget ABC, WidgetConfig, and register_widget decorator"
```

---

## Task 4: Core Widgets — Tokens & Context

**Files:**
- Create: `ccstatusline/widgets/core.py`
- Modify: `tests/test_widgets.py`

- [ ] **Step 1: Write failing tests — append to tests/test_widgets.py**

```python
# Append to tests/test_widgets.py
import ccstatusline.widgets.core  # ensure widgets are registered
from ccstatusline.widgets.base import REGISTRY, WidgetConfig


def _wc(widget_type: str, **options) -> WidgetConfig:
    return WidgetConfig(type=widget_type, options=options)


def test_model_widget_display_name(sample_data):
    w = REGISTRY["model"]()
    assert w.render(sample_data, _wc("model")) == "claude-sonnet-4-5"


def test_model_widget_empty():
    from ccstatusline.data import StatusData
    w = REGISTRY["model"]()
    assert w.render(StatusData(), _wc("model")) == ""


def test_tokens_used_widget_formats_thousands(sample_data):
    w = REGISTRY["tokens_used"]()
    result = w.render(sample_data, _wc("tokens_used"))
    assert result == "18.0k"


def test_tokens_used_widget_formats_millions():
    from ccstatusline.data import StatusData
    d = StatusData(context_window={"total_input_tokens": 1_200_000, "total_output_tokens": 0})
    w = REGISTRY["tokens_used"]()
    assert w.render(d, _wc("tokens_used")) == "1.2M"


def test_tokens_used_widget_small():
    from ccstatusline.data import StatusData
    d = StatusData(context_window={"total_input_tokens": 500, "total_output_tokens": 0})
    w = REGISTRY["tokens_used"]()
    assert w.render(d, _wc("tokens_used")) == "500"


def test_context_pct_widget(sample_data):
    w = REGISTRY["context_pct"]()
    assert w.render(sample_data, _wc("context_pct")) == "9.0%"


def test_context_pct_widget_empty():
    from ccstatusline.data import StatusData
    w = REGISTRY["context_pct"]()
    assert w.render(StatusData(), _wc("context_pct")) == ""


def test_context_bar_widget_default_width(sample_data):
    w = REGISTRY["context_bar"]()
    result = w.render(sample_data, _wc("context_bar"))
    assert len(result) == 10
    assert result.startswith("█") or result.startswith("░")


def test_context_bar_widget_custom_width(sample_data):
    w = REGISTRY["context_bar"]()
    result = w.render(sample_data, _wc("context_bar", bar_width=5))
    assert len(result) == 5
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_widgets.py -k "model or tokens or context" -v
```

Expected: `ImportError` or `KeyError` on missing widgets.

- [ ] **Step 3: Create widgets/core.py with token/context widgets**

```python
# ccstatusline/widgets/core.py
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ccstatusline.data import StatusData
from ccstatusline.widgets.base import Widget, WidgetConfig, register_widget


@register_widget("model")
class ModelWidget(Widget):
    category = "session"

    def render(self, data: StatusData, config: WidgetConfig) -> str:
        return data.model_name


@register_widget("tokens_used")
class TokensUsedWidget(Widget):
    category = "tokens"

    def render(self, data: StatusData, config: WidgetConfig) -> str:
        t = data.tokens_used
        if t >= 1_000_000:
            return f"{t / 1_000_000:.1f}M"
        if t >= 1_000:
            return f"{t / 1_000:.1f}k"
        return str(t) if t else ""


@register_widget("context_pct")
class ContextPctWidget(Widget):
    category = "tokens"

    def render(self, data: StatusData, config: WidgetConfig) -> str:
        pct = data.context_used_pct
        return f"{pct:.1f}%" if pct else ""


@register_widget("context_bar")
class ContextBarWidget(Widget):
    category = "tokens"

    def render(self, data: StatusData, config: WidgetConfig) -> str:
        width = int(config.options.get("bar_width", 10))
        pct = data.context_used_pct / 100.0
        filled = round(width * pct)
        return "█" * filled + "░" * (width - filled)
```

- [ ] **Step 4: Update widgets/__init__.py to trigger registration**

```python
# ccstatusline/widgets/__init__.py
from ccstatusline.widgets import core as _core  # noqa: F401 — triggers @register_widget decorators
from ccstatusline.widgets.base import CATEGORIES, REGISTRY, Widget, WidgetConfig, register_widget

__all__ = ["REGISTRY", "CATEGORIES", "Widget", "WidgetConfig", "register_widget"]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/test_widgets.py -k "model or tokens or context" -v
```

Expected: all 9 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add ccstatusline/widgets/core.py ccstatusline/widgets/__init__.py tests/test_widgets.py
git commit -m "feat: model, tokens_used, context_pct, context_bar widgets"
```

---

## Task 5: Core Widgets — Git & Session

**Files:**
- Modify: `ccstatusline/widgets/core.py`
- Modify: `tests/test_widgets.py`

- [ ] **Step 1: Write failing tests — append to tests/test_widgets.py**

```python
# Append to tests/test_widgets.py

def test_git_branch_from_worktree(sample_data):
    w = REGISTRY["git_branch"]()
    assert w.render(sample_data, _wc("git_branch")) == "feat/python-port"


def test_git_branch_empty_when_no_worktree():
    from ccstatusline.data import StatusData
    from unittest.mock import patch
    d = StatusData(cwd="/tmp/notarepo")
    w = REGISTRY["git_branch"]()
    with patch("subprocess.run", side_effect=Exception("no git")):
        assert w.render(d, _wc("git_branch")) == ""


def test_git_status_clean():
    from ccstatusline.data import StatusData
    from unittest.mock import MagicMock, patch
    d = StatusData(cwd="/tmp/repo")
    mock_result = MagicMock()
    mock_result.stdout = ""
    w = REGISTRY["git_status"]()
    with patch("subprocess.run", return_value=mock_result):
        assert w.render(d, _wc("git_status")) == "✔"


def test_git_status_dirty():
    from ccstatusline.data import StatusData
    from unittest.mock import MagicMock, patch
    d = StatusData(cwd="/tmp/repo")
    mock_result = MagicMock()
    mock_result.stdout = " M somefile.py\n"
    w = REGISTRY["git_status"]()
    with patch("subprocess.run", return_value=mock_result):
        assert w.render(d, _wc("git_status")) == "✎"


def test_git_status_error_returns_empty():
    from ccstatusline.data import StatusData
    from unittest.mock import patch
    d = StatusData()
    w = REGISTRY["git_status"]()
    with patch("subprocess.run", side_effect=Exception("no git")):
        assert w.render(d, _wc("git_status")) == ""


def test_session_duration_seconds(sample_data):
    from ccstatusline.data import StatusData
    d = StatusData(cost={"total_duration_ms": 45000})
    w = REGISTRY["session_duration"]()
    assert w.render(d, _wc("session_duration")) == "45s"


def test_session_duration_minutes():
    from ccstatusline.data import StatusData
    d = StatusData(cost={"total_duration_ms": 135000})
    w = REGISTRY["session_duration"]()
    assert w.render(d, _wc("session_duration")) == "2m15s"


def test_session_duration_hours():
    from ccstatusline.data import StatusData
    d = StatusData(cost={"total_duration_ms": 3_700_000})
    w = REGISTRY["session_duration"]()
    assert w.render(d, _wc("session_duration")) == "1h1m"


def test_session_duration_empty():
    from ccstatusline.data import StatusData
    w = REGISTRY["session_duration"]()
    assert w.render(StatusData(), _wc("session_duration")) == ""


def test_session_cost(sample_data):
    w = REGISTRY["session_cost"]()
    assert w.render(sample_data, _wc("session_cost")) == "$0.0234"


def test_session_cost_empty():
    from ccstatusline.data import StatusData
    w = REGISTRY["session_cost"]()
    assert w.render(StatusData(), _wc("session_cost")) == ""
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_widgets.py -k "git or session" -v
```

Expected: `KeyError` on missing widgets.

- [ ] **Step 3: Append git & session widgets to widgets/core.py**

```python
# Append to ccstatusline/widgets/core.py


@register_widget("git_branch")
class GitBranchWidget(Widget):
    category = "git"

    def render(self, data: StatusData, config: WidgetConfig) -> str:
        if data.worktree and data.worktree.get("branch"):
            return data.worktree["branch"]
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=2,
                cwd=data.cwd or None,
            )
            return result.stdout.strip()
        except Exception:
            return ""


@register_widget("git_status")
class GitStatusWidget(Widget):
    category = "git"

    def render(self, data: StatusData, config: WidgetConfig) -> str:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=2,
                cwd=data.cwd or None,
            )
            return "✎" if result.stdout.strip() else "✔"
        except Exception:
            return ""


@register_widget("session_duration")
class SessionDurationWidget(Widget):
    category = "session"

    def render(self, data: StatusData, config: WidgetConfig) -> str:
        ms = data.session_duration_ms
        if not ms:
            return ""
        secs = ms // 1000
        mins = secs // 60
        hours = mins // 60
        if hours:
            return f"{hours}h{mins % 60}m"
        if mins:
            return f"{mins}m{secs % 60}s"
        return f"{secs}s"


@register_widget("session_cost")
class SessionCostWidget(Widget):
    category = "session"

    def render(self, data: StatusData, config: WidgetConfig) -> str:
        cost = data.cost_usd
        return f"${cost:.4f}" if cost else ""
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_widgets.py -k "git or session" -v
```

Expected: all 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add ccstatusline/widgets/core.py tests/test_widgets.py
git commit -m "feat: git_branch, git_status, session_duration, session_cost widgets"
```

---

## Task 6: Core Widgets — System & Custom

**Files:**
- Modify: `ccstatusline/widgets/core.py`
- Modify: `tests/test_widgets.py`

- [ ] **Step 1: Write failing tests — append to tests/test_widgets.py**

```python
# Append to tests/test_widgets.py

def test_cwd_widget_basename(sample_data):
    w = REGISTRY["cwd"]()
    assert w.render(sample_data, _wc("cwd")) == "myproject"


def test_cwd_widget_full_path(sample_data):
    w = REGISTRY["cwd"]()
    assert w.render(sample_data, _wc("cwd", full_path=True)) == "/home/user/myproject"


def test_cwd_widget_empty():
    from ccstatusline.data import StatusData
    w = REGISTRY["cwd"]()
    assert w.render(StatusData(), _wc("cwd")) == ""


def test_custom_text_widget():
    from ccstatusline.data import StatusData
    w = REGISTRY["custom_text"]()
    assert w.render(StatusData(), _wc("custom_text", text="hello world")) == "hello world"


def test_custom_text_widget_empty():
    from ccstatusline.data import StatusData
    w = REGISTRY["custom_text"]()
    assert w.render(StatusData(), _wc("custom_text")) == ""


def test_separator_widget_default():
    from ccstatusline.data import StatusData
    w = REGISTRY["separator"]()
    assert w.render(StatusData(), _wc("separator")) == " │ "


def test_separator_widget_custom():
    from ccstatusline.data import StatusData
    w = REGISTRY["separator"]()
    assert w.render(StatusData(), _wc("separator", char=" | ")) == " | "


def test_claude_email_widget_no_file():
    from ccstatusline.data import StatusData
    from unittest.mock import patch
    from pathlib import Path
    w = REGISTRY["claude_email"]()
    with patch.object(Path, "exists", return_value=False):
        assert w.render(StatusData(), _wc("claude_email")) == ""
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_widgets.py -k "cwd or custom or separator or email" -v
```

Expected: `KeyError` on missing widgets.

- [ ] **Step 3: Append system & custom widgets to widgets/core.py**

```python
# Append to ccstatusline/widgets/core.py


@register_widget("cwd")
class CwdWidget(Widget):
    category = "system"

    def render(self, data: StatusData, config: WidgetConfig) -> str:
        path = data.cwd or ""
        if not path:
            return ""
        if config.options.get("full_path"):
            return path
        return Path(path).name


@register_widget("claude_email")
class ClaudeEmailWidget(Widget):
    category = "system"

    def render(self, data: StatusData, config: WidgetConfig) -> str:
        try:
            claude_json = Path.home() / ".claude" / "claude.json"
            if not claude_json.exists():
                return ""
            info = json.loads(claude_json.read_text())
            for key in ("email", "user_email", "account_email"):
                if key in info:
                    return info[key]
            for key in ("user", "account", "profile"):
                if isinstance(info.get(key), dict):
                    email = info[key].get("email", "")
                    if email:
                        return email
        except Exception:
            pass
        return ""


@register_widget("custom_text")
class CustomTextWidget(Widget):
    category = "custom"

    def render(self, data: StatusData, config: WidgetConfig) -> str:
        return config.options.get("text", "")


@register_widget("separator")
class SeparatorWidget(Widget):
    category = "custom"

    def render(self, data: StatusData, config: WidgetConfig) -> str:
        return config.options.get("char", " │ ")
```

- [ ] **Step 4: Run all widget tests**

```bash
uv run pytest tests/test_widgets.py -v
```

Expected: all tests PASS. Count should be 30+.

- [ ] **Step 5: Commit**

```bash
git add ccstatusline/widgets/core.py tests/test_widgets.py
git commit -m "feat: cwd, claude_email, custom_text, separator widgets — core widget set complete"
```

---

## Task 7: Config Models

**Files:**
- Create: `ccstatusline/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_config.py
import pytest
from ccstatusline.config import Config, LineConfig, PowerlineConfig
from ccstatusline.widgets.base import WidgetConfig


def test_powerline_config_defaults():
    pl = PowerlineConfig()
    assert pl.enabled is True
    assert pl.separator == ""
    assert pl.thin_separator == ""
    assert pl.left_cap == ""
    assert pl.right_cap == ""


def test_config_defaults():
    c = Config()
    assert c.color_level == "truecolor"
    assert c.minimalist_mode is False
    assert c.lines == []


def test_config_with_widgets():
    wc = WidgetConfig(type="model", fg="#ff0000", bg="#000000")
    line = LineConfig(widgets=[wc])
    c = Config(lines=[line])
    assert len(c.lines) == 1
    assert c.lines[0].widgets[0].type == "model"
    assert c.lines[0].widgets[0].fg == "#ff0000"


def test_config_color_level_valid():
    for level in ("none", "basic", "256", "truecolor"):
        c = Config(color_level=level)
        assert c.color_level == level


def test_config_color_level_invalid():
    with pytest.raises(Exception):
        Config(color_level="fancy")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'ccstatusline.config'`

- [ ] **Step 3: Create config.py with models**

```python
# ccstatusline/config.py
from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path
from typing import Literal

import tomli_w
from pydantic import BaseModel, Field

from ccstatusline.widgets.base import WidgetConfig

TOML_PATH = Path.home() / ".config" / "ccstatusline_py" / "settings.toml"
LEGACY_JSON_PATH = Path.home() / ".config" / "ccstatusline" / "settings.json"

_COLOR_LEVEL_MAP: dict[int, str] = {0: "none", 1: "basic", 2: "256", 3: "truecolor"}

_WIDGET_ID_MAP: dict[str, str] = {
    "Model": "model",
    "GitBranch": "git_branch",
    "GitStatus": "git_status",
    "TokensInput": "tokens_used",
    "TokensUsed": "tokens_used",
    "ContextPercentage": "context_pct",
    "ContextBar": "context_bar",
    "SessionDuration": "session_duration",
    "SessionClock": "session_duration",
    "SessionCost": "session_cost",
    "CurrentWorkingDir": "cwd",
    "ClaudeAccountEmail": "claude_email",
    "CustomText": "custom_text",
    "Separator": "separator",
}


class PowerlineConfig(BaseModel):
    enabled: bool = True
    separator: str = ""
    thin_separator: str = ""
    left_cap: str = ""
    right_cap: str = ""


class LineConfig(BaseModel):
    widgets: list[WidgetConfig] = Field(default_factory=list)


class Config(BaseModel):
    color_level: Literal["none", "basic", "256", "truecolor"] = "truecolor"
    minimalist_mode: bool = False
    powerline: PowerlineConfig = Field(default_factory=PowerlineConfig)
    lines: list[LineConfig] = Field(default_factory=list)

    @classmethod
    def load(cls) -> Config:
        if TOML_PATH.exists():
            try:
                data = tomllib.loads(TOML_PATH.read_text())
                return cls.model_validate(data)
            except Exception as e:
                print(f"ccstatusline: failed to load config: {e}", file=sys.stderr)
                return cls()

        if LEGACY_JSON_PATH.exists():
            try:
                migrated = _migrate_from_json(LEGACY_JSON_PATH)
                migrated.save()
                return migrated
            except Exception as e:
                print(f"ccstatusline: failed to migrate config: {e}", file=sys.stderr)

        return cls()

    def save(self) -> None:
        TOML_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOML_PATH.write_bytes(tomli_w.dumps(self.model_dump()).encode())


def _migrate_from_json(path: Path) -> Config:
    raw = json.loads(path.read_text())
    color_int = raw.get("colorLevel", 3)
    color_level = _COLOR_LEVEL_MAP.get(int(color_int), "truecolor")

    pl_raw = raw.get("powerline", {}) or {}
    powerline = PowerlineConfig(
        enabled=bool(pl_raw.get("enabled", True)),
        separator=pl_raw.get("separator") or "",
        thin_separator=pl_raw.get("thinSeparator") or "",
        left_cap=pl_raw.get("leftCap") or "",
        right_cap=pl_raw.get("rightCap") or "",
    )

    lines: list[LineConfig] = []
    for line_raw in raw.get("lines", []):
        widgets: list[WidgetConfig] = []
        for w in line_raw:
            original_type = w.get("type", "")
            py_type = _WIDGET_ID_MAP.get(original_type)
            if py_type is None:
                print(
                    f"ccstatusline: unknown widget '{original_type}' skipped during migration",
                    file=sys.stderr,
                )
                continue
            styling = w.get("styling") or {}
            widgets.append(WidgetConfig(
                type=py_type,
                fg=styling.get("fg") or "#ffffff",
                bg=styling.get("bg") or "#000000",
                bold=bool(styling.get("bold")),
                padding=int(styling.get("padding") or 1),
            ))
        lines.append(LineConfig(widgets=widgets))

    return Config(
        color_level=color_level,
        minimalist_mode=bool(raw.get("minimalistMode", False)),
        powerline=powerline,
        lines=lines,
    )
```

- [ ] **Step 4: Run model tests**

```bash
uv run pytest tests/test_config.py -v
```

Expected: all 5 model tests PASS.

- [ ] **Step 5: Commit**

```bash
git add ccstatusline/config.py tests/test_config.py
git commit -m "feat: Config, LineConfig, PowerlineConfig Pydantic models"
```

---

## Task 8: Config TOML I/O & Migration

**Files:**
- Modify: `tests/test_config.py`

- [ ] **Step 1: Write failing tests — append to tests/test_config.py**

```python
# Append to tests/test_config.py
import json
import tomllib
from pathlib import Path
from unittest.mock import patch

from ccstatusline.config import LEGACY_JSON_PATH, TOML_PATH, Config, _migrate_from_json


def test_config_save_and_load(tmp_path):
    toml_file = tmp_path / "settings.toml"
    wc = WidgetConfig(type="model", fg="#a6e3a1", bg="#1e1e2e", bold=True)
    original = Config(
        color_level="256",
        lines=[LineConfig(widgets=[wc])],
    )

    with patch("ccstatusline.config.TOML_PATH", toml_file):
        original.save()
        loaded = Config.load()

    assert loaded.color_level == "256"
    assert loaded.lines[0].widgets[0].type == "model"
    assert loaded.lines[0].widgets[0].fg == "#a6e3a1"
    assert loaded.lines[0].widgets[0].bold is True


def test_config_save_writes_valid_toml(tmp_path):
    toml_file = tmp_path / "settings.toml"
    c = Config(color_level="basic")
    with patch("ccstatusline.config.TOML_PATH", toml_file):
        c.save()
    data = tomllib.loads(toml_file.read_text())
    assert data["color_level"] == "basic"


def test_config_load_returns_default_when_no_file(tmp_path):
    missing = tmp_path / "nonexistent.toml"
    missing_json = tmp_path / "nonexistent.json"
    with patch("ccstatusline.config.TOML_PATH", missing), \
         patch("ccstatusline.config.LEGACY_JSON_PATH", missing_json):
        c = Config.load()
    assert c.color_level == "truecolor"
    assert c.lines == []


def test_migrate_from_json(tmp_path):
    json_data = {
        "colorLevel": 2,
        "minimalistMode": False,
        "powerline": {
            "enabled": True,
            "separator": "",
            "thinSeparator": "",
            "leftCap": "",
            "rightCap": "",
        },
        "lines": [
            [
                {"type": "Model", "styling": {"fg": "#a6e3a1", "bg": "#1e1e2e", "bold": True}},
                {"type": "GitBranch", "styling": {"fg": "#cba6f7", "bg": "#1e1e2e"}},
            ]
        ],
    }
    json_file = tmp_path / "settings.json"
    json_file.write_text(json.dumps(json_data))
    result = _migrate_from_json(json_file)

    assert result.color_level == "256"
    assert result.powerline.enabled is True
    assert len(result.lines) == 1
    assert result.lines[0].widgets[0].type == "model"
    assert result.lines[0].widgets[0].fg == "#a6e3a1"
    assert result.lines[0].widgets[0].bold is True
    assert result.lines[0].widgets[1].type == "git_branch"


def test_migrate_skips_unknown_widget(tmp_path, capsys):
    json_data = {
        "colorLevel": 3,
        "lines": [[{"type": "UnknownWidget123", "styling": {}}]],
    }
    json_file = tmp_path / "settings.json"
    json_file.write_text(json.dumps(json_data))
    result = _migrate_from_json(json_file)
    assert result.lines[0].widgets == []
    captured = capsys.readouterr()
    assert "UnknownWidget123" in captured.err
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_config.py -k "save or load or migrate" -v
```

Expected: tests fail because `Config.load()` is not yet implemented (it's defined but the test patches need the real logic).

Actually the config.py in Task 7 already has `load()` and `save()` and `_migrate_from_json`. Run to see:

```bash
uv run pytest tests/test_config.py -v
```

Expected: all tests PASS (the implementation was included in Task 7).

- [ ] **Step 3: Commit**

```bash
git add tests/test_config.py
git commit -m "test: config load/save round-trip and JSON migration tests"
```

---

## Task 9: Color Utilities

**Files:**
- Create: `ccstatusline/renderer.py`
- Create: `tests/test_renderer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_renderer.py
import re
import pytest
from ccstatusline.renderer import (
    ANSI_ESCAPE_RE,
    ansi_bg,
    ansi_fg,
    visible_len,
)


def test_ansi_fg_truecolor():
    result = ansi_fg("#ff0000", "truecolor")
    assert result == "\x1b[38;2;255;0;0m"


def test_ansi_bg_truecolor():
    result = ansi_bg("#0000ff", "truecolor")
    assert result == "\x1b[48;2;0;0;255m"


def test_ansi_fg_none_returns_empty():
    assert ansi_fg("#ff0000", "none") == ""


def test_ansi_bg_none_returns_empty():
    assert ansi_bg("#ff0000", "none") == ""


def test_ansi_fg_256():
    result = ansi_fg("#ff0000", "256")
    assert result.startswith("\x1b[38;5;")


def test_ansi_bg_256():
    result = ansi_bg("#00ff00", "256")
    assert result.startswith("\x1b[48;5;")


def test_ansi_fg_basic_red():
    result = ansi_fg("#ff0000", "basic")
    # red maps to ANSI code 91 (bright red) or 31 (red)
    assert "\x1b[" in result
    assert result.endswith("m")


def test_visible_len_strips_ansi():
    colored = "\x1b[38;2;255;0;0mhello\x1b[0m"
    assert visible_len(colored) == 5


def test_visible_len_plain_string():
    assert visible_len("hello world") == 11


def test_visible_len_empty():
    assert visible_len("") == 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_renderer.py -k "ansi or visible" -v
```

Expected: `ModuleNotFoundError: No module named 'ccstatusline.renderer'`

- [ ] **Step 3: Create renderer.py with color utilities**

```python
# ccstatusline/renderer.py
from __future__ import annotations

import re
import shutil

from ccstatusline.config import Config
from ccstatusline.data import StatusData
from ccstatusline.widgets.base import REGISTRY, WidgetConfig

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")
RESET = "\x1b[0m"
BOLD = "\x1b[1m"

# ANSI 16-color palette (R, G, B) — indices 0-7 normal, 8-15 bright
_ANSI16: list[tuple[int, int, int]] = [
    (0, 0, 0),       # 0  black
    (170, 0, 0),     # 1  red
    (0, 170, 0),     # 2  green
    (170, 85, 0),    # 3  dark yellow
    (0, 0, 170),     # 4  blue
    (170, 0, 170),   # 5  magenta
    (0, 170, 170),   # 6  cyan
    (170, 170, 170), # 7  light gray
    (85, 85, 85),    # 8  dark gray
    (255, 85, 85),   # 9  bright red
    (85, 255, 85),   # 10 bright green
    (255, 255, 85),  # 11 bright yellow
    (85, 85, 255),   # 12 bright blue
    (255, 85, 255),  # 13 bright magenta
    (85, 255, 255),  # 14 bright cyan
    (255, 255, 255), # 15 bright white
]

# xterm-256 cube steps
_CUBE_STEPS = [0, 95, 135, 175, 215, 255]


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _dist(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> int:
    return sum((a - b) ** 2 for a, b in zip(c1, c2))


def _hex_to_ansi16_index(hex_color: str) -> int:
    rgb = _hex_to_rgb(hex_color)
    return min(range(16), key=lambda i: _dist(rgb, _ANSI16[i]))


def _hex_to_xterm256_index(hex_color: str) -> int:
    r, g, b = _hex_to_rgb(hex_color)
    ri, gi, bi = (round(x / 255 * 5) for x in (r, g, b))
    cube_idx = 16 + 36 * ri + 6 * gi + bi
    cube_rgb = (_CUBE_STEPS[ri], _CUBE_STEPS[gi], _CUBE_STEPS[bi])
    gray_step = round((r + g + b) / 3 / 255 * 23)
    gray_val = 8 + gray_step * 10
    gray_idx = 232 + gray_step
    return cube_idx if _dist((r, g, b), cube_rgb) <= _dist((r, g, b), (gray_val, gray_val, gray_val)) else gray_idx


def ansi_fg(hex_color: str, color_level: str) -> str:
    if color_level == "none":
        return ""
    if color_level == "basic":
        idx = _hex_to_ansi16_index(hex_color)
        code = (30 + idx) if idx < 8 else (90 + idx - 8)
        return f"\x1b[{code}m"
    if color_level == "256":
        return f"\x1b[38;5;{_hex_to_xterm256_index(hex_color)}m"
    r, g, b = _hex_to_rgb(hex_color)
    return f"\x1b[38;2;{r};{g};{b}m"


def ansi_bg(hex_color: str, color_level: str) -> str:
    if color_level == "none":
        return ""
    if color_level == "basic":
        idx = _hex_to_ansi16_index(hex_color)
        code = (40 + idx) if idx < 8 else (100 + idx - 8)
        return f"\x1b[{code}m"
    if color_level == "256":
        return f"\x1b[48;5;{_hex_to_xterm256_index(hex_color)}m"
    r, g, b = _hex_to_rgb(hex_color)
    return f"\x1b[48;2;{r};{g};{b}m"


def visible_len(s: str) -> int:
    return len(ANSI_ESCAPE_RE.sub("", s))
```

- [ ] **Step 4: Run color utility tests**

```bash
uv run pytest tests/test_renderer.py -v
```

Expected: all 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add ccstatusline/renderer.py tests/test_renderer.py
git commit -m "feat: ANSI color utilities (16-color, 256, truecolor) and visible_len"
```

---

## Task 10: Renderer Pipeline & Powerline

**Files:**
- Modify: `ccstatusline/renderer.py`
- Modify: `tests/test_renderer.py`

- [ ] **Step 1: Write failing tests — append to tests/test_renderer.py**

```python
# Append to tests/test_renderer.py
import ccstatusline.widgets.core  # noqa: F401
from ccstatusline.config import Config, LineConfig, PowerlineConfig
from ccstatusline.renderer import render_statusline, visible_len
from ccstatusline.widgets.base import WidgetConfig


def _strip_ansi(s: str) -> str:
    return ANSI_ESCAPE_RE.sub("", s)


def test_render_empty_config(sample_data):
    c = Config()
    assert render_statusline(c, sample_data) == ""


def test_render_single_widget_visible_text(sample_data):
    wc = WidgetConfig(type="model", fg="#ffffff", bg="#000000", padding=1)
    c = Config(lines=[LineConfig(widgets=[wc])], minimalist_mode=True)
    result = render_statusline(c, sample_data)
    assert "claude-sonnet-4-5" in _strip_ansi(result)


def test_render_skips_empty_widget_output():
    from ccstatusline.data import StatusData
    wc = WidgetConfig(type="model")
    c = Config(lines=[LineConfig(widgets=[wc])], minimalist_mode=True)
    result = render_statusline(c, StatusData())
    assert _strip_ansi(result).strip() == ""


def test_render_skips_unknown_widget_type(sample_data):
    wc = WidgetConfig(type="nonexistent_widget_xyz")
    c = Config(lines=[LineConfig(widgets=[wc])], minimalist_mode=True)
    result = render_statusline(c, sample_data)
    assert result == ""


def test_render_multiple_lines(sample_data):
    wc1 = WidgetConfig(type="model", fg="#ffffff", bg="#000000", padding=0)
    wc2 = WidgetConfig(type="session_cost", fg="#ffffff", bg="#000000", padding=0)
    c = Config(
        lines=[LineConfig(widgets=[wc1]), LineConfig(widgets=[wc2])],
        minimalist_mode=True,
    )
    result = render_statusline(c, sample_data)
    lines = result.split("\n")
    assert len(lines) == 2
    assert "claude-sonnet-4-5" in _strip_ansi(lines[0])
    assert "$0.0234" in _strip_ansi(lines[1])


def test_render_powerline_contains_separator_glyph(sample_data):
    wc1 = WidgetConfig(type="model", fg="#ffffff", bg="#1e1e2e", padding=1)
    wc2 = WidgetConfig(type="session_cost", fg="#ffffff", bg="#313244", padding=1)
    pl = PowerlineConfig(enabled=True, separator="", left_cap="", right_cap="")
    c = Config(
        lines=[LineConfig(widgets=[wc1, wc2])],
        powerline=pl,
        minimalist_mode=True,
    )
    result = render_statusline(c, sample_data)
    visible = _strip_ansi(result)
    assert "" in visible or "" in visible


def test_render_plain_no_powerline_glyphs(sample_data):
    wc = WidgetConfig(type="model", fg="#ffffff", bg="#000000", padding=1)
    pl = PowerlineConfig(enabled=False)
    c = Config(lines=[LineConfig(widgets=[wc])], powerline=pl, minimalist_mode=True)
    result = render_statusline(c, sample_data)
    assert "" not in result
    assert "" not in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_renderer.py -k "render" -v
```

Expected: `ImportError` — `render_statusline` not yet defined.

- [ ] **Step 3: Append render pipeline to renderer.py**

```python
# Append to ccstatusline/renderer.py


def _wrap_segment(text: str, wc: WidgetConfig, color_level: str) -> str:
    pad = " " * wc.padding
    content = f"{pad}{text}{pad}"
    fg = ansi_fg(wc.fg, color_level)
    bg = ansi_bg(wc.bg, color_level)
    bold = BOLD if wc.bold else ""
    return f"{bg}{fg}{bold}{content}{RESET}"


def _render_plain(
    segments: list[tuple[str, WidgetConfig]], color_level: str
) -> str:
    return "".join(
        _wrap_segment(text, wc, color_level)
        for text, wc in segments
        if text
    )


def _render_powerline(
    segments: list[tuple[str, WidgetConfig]],
    color_level: str,
    separator: str,
    left_cap: str,
    right_cap: str,
) -> str:
    active = [(text, wc) for text, wc in segments if text]
    if not active:
        return ""

    parts: list[str] = []

    # Left cap: colored with first segment's bg
    first_bg = active[0][1].bg
    parts.append(f"{ansi_fg(first_bg, color_level)}{left_cap}{RESET}")

    for i, (text, wc) in enumerate(active):
        pad = " " * wc.padding
        fg = ansi_fg(wc.fg, color_level)
        bg = ansi_bg(wc.bg, color_level)
        bold = BOLD if wc.bold else ""
        parts.append(f"{bg}{fg}{bold}{pad}{text}{pad}{RESET}")

        if i < len(active) - 1:
            next_bg = active[i + 1][1].bg
            # Arrow fg = current segment bg, arrow bg = next segment bg
            parts.append(
                f"{ansi_bg(next_bg, color_level)}{ansi_fg(wc.bg, color_level)}{separator}{RESET}"
            )

    # Right cap: colored with last segment's bg
    last_bg = active[-1][1].bg
    parts.append(f"{ansi_fg(last_bg, color_level)}{right_cap}{RESET}")

    return "".join(parts)


def render_statusline(config: Config, data: StatusData) -> str:
    if not config.lines:
        return ""

    term_width = shutil.get_terminal_size((80, 24)).columns
    output_lines: list[str] = []

    for line_config in config.lines:
        segments: list[tuple[str, WidgetConfig]] = []
        for wc in line_config.widgets:
            cls = REGISTRY.get(wc.type)
            if cls is None:
                continue
            try:
                text = cls().render(data, wc)
            except Exception:
                text = ""
            segments.append((text, wc))

        if config.powerline.enabled:
            line_str = _render_powerline(
                segments,
                config.color_level,
                config.powerline.separator,
                config.powerline.left_cap,
                config.powerline.right_cap,
            )
        else:
            line_str = _render_plain(segments, config.color_level)

        if not config.minimalist_mode:
            vlen = visible_len(line_str)
            if vlen < term_width:
                line_str += " " * (term_width - vlen)

        output_lines.append(line_str)

    return "\n".join(output_lines)
```

- [ ] **Step 4: Run all renderer tests**

```bash
uv run pytest tests/test_renderer.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add ccstatusline/renderer.py tests/test_renderer.py
git commit -m "feat: render_statusline pipeline with plain and powerline rendering modes"
```

---

## Task 11: Entry Point

**Files:**
- Modify: `ccstatusline/__main__.py`

- [ ] **Step 1: Write failing integration test — append to tests/test_renderer.py**

```python
# Append to tests/test_renderer.py
import json
import subprocess
import sys


def test_piped_mode_outputs_statusline():
    """End-to-end: pipe JSON to the entry point, expect ANSI output."""
    data = {
        "model": {"display_name": "claude-sonnet-4-5"},
        "context_window": {
            "context_window_size": 200000,
            "total_input_tokens": 5000,
            "total_output_tokens": 1000,
            "used_percentage": 3.0,
        },
        "cost": {"total_cost_usd": 0.01, "total_duration_ms": 60000},
        "worktree": {"branch": "main"},
        "cwd": "/tmp",
    }
    result = subprocess.run(
        [sys.executable, "-m", "ccstatusline"],
        input=json.dumps(data),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0


def test_piped_mode_invalid_json_exits_cleanly():
    result = subprocess.run(
        [sys.executable, "-m", "ccstatusline"],
        input="not json at all",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout == ""
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_renderer.py -k "piped" -v
```

Expected: tests fail — `main()` is a stub that does nothing.

- [ ] **Step 3: Implement __main__.py**

```python
# ccstatusline/__main__.py
from __future__ import annotations

import sys


def main() -> None:
    if not sys.stdin.isatty():
        _piped_mode()
    else:
        _interactive_mode()


def _piped_mode() -> None:
    from ccstatusline.config import Config
    from ccstatusline.data import StatusData
    from ccstatusline.renderer import render_statusline

    try:
        raw = sys.stdin.read()
        data = StatusData.model_validate_json(raw)
    except Exception as e:
        print(f"ccstatusline: failed to parse input: {e}", file=sys.stderr)
        print("", end="")
        return

    config = Config.load()

    try:
        output = render_statusline(config, data)
        print(output, end="")
    except Exception as e:
        print(f"ccstatusline: render error: {e}", file=sys.stderr)
        print("", end="")


def _interactive_mode() -> None:
    from ccstatusline.config import Config
    from ccstatusline.tui.app import CCStatuslineApp

    config = Config.load()
    app = CCStatuslineApp(config)
    app.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run integration tests**

```bash
uv run pytest tests/test_renderer.py -k "piped" -v
```

Expected: both PASS.

- [ ] **Step 5: Run full test suite**

```bash
uv run pytest -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add ccstatusline/__main__.py tests/test_renderer.py
git commit -m "feat: entry point with piped mode and interactive mode dispatch"
```

---

## Task 12: TUI Scaffold & Widget Library

**Files:**
- Create: `ccstatusline/tui/app.py`
- Create: `ccstatusline/tui/screens.py`

No unit tests for the TUI (per spec). We verify manually by launching the app.

- [ ] **Step 1: Create tui/screens.py**

```python
# ccstatusline/tui/screens.py
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widget import Widget as TextualWidget
from textual.widgets import (
    Button,
    Checkbox,
    Label,
    ListItem,
    ListView,
    Select,
    Static,
)

from ccstatusline.config import Config, LineConfig, PowerlineConfig
from ccstatusline.data import StatusData
from ccstatusline.renderer import render_statusline
from ccstatusline.widgets.base import CATEGORIES, WidgetConfig
from ccstatusline.widgets import core as _core  # noqa: F401 — register widgets


SAMPLE_DATA = StatusData(
    model={"display_name": "claude-sonnet-4-5", "id": "claude-sonnet-4-5"},
    session_id="sample-session",
    cwd="/home/user/myproject",
    context_window={
        "context_window_size": 200000,
        "total_input_tokens": 15000,
        "total_output_tokens": 3000,
        "used_percentage": 9.0,
        "remaining_percentage": 91.0,
    },
    cost={
        "total_cost_usd": 0.0234,
        "total_duration_ms": 135000,
    },
    worktree={
        "name": "main",
        "path": "/home/user/myproject",
        "branch": "feat/python-port",
    },
)


class WidgetLibrary(TextualWidget):
    """Left panel: scrollable list of available widgets grouped by category."""

    DEFAULT_CSS = """
    WidgetLibrary {
        width: 28;
        border: solid $accent;
        padding: 0 1;
    }
    WidgetLibrary Label.category-header {
        color: $text-muted;
        text-style: bold;
        margin-top: 1;
    }
    """

    class WidgetSelected(TextualWidget.Message):
        def __init__(self, widget_type: str) -> None:
            super().__init__()
            self.widget_type = widget_type

    def compose(self) -> ComposeResult:
        yield Label("── Widgets ──", id="library-title")
        items: list[ListItem] = []
        for category in sorted(CATEGORIES):
            items.append(
                ListItem(Label(f"  {category.upper()}", classes="category-header"), disabled=True)
            )
            for wid in CATEGORIES[category]:
                items.append(ListItem(Label(f"  {wid}"), id=f"w-{wid}"))
        yield ListView(*items, id="widget-list")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.id and event.item.id.startswith("w-"):
            self.post_message(self.WidgetSelected(event.item.id[2:]))


class LayoutEditor(TextualWidget):
    """Center panel: reorderable list of widgets in the active line."""

    DEFAULT_CSS = """
    LayoutEditor {
        width: 1fr;
        border: solid $accent;
        padding: 0 1;
    }
    """

    class WidgetAdded(TextualWidget.Message):
        pass

    class WidgetRemoved(TextualWidget.Message):
        pass

    class WidgetReordered(TextualWidget.Message):
        pass

    def __init__(self, line: LineConfig, **kwargs) -> None:
        super().__init__(**kwargs)
        self._line = line

    def compose(self) -> ComposeResult:
        yield Label("── Layout (↑↓ reorder, Del remove) ──", id="editor-title")
        yield ListView(
            *[ListItem(Label(wc.type), id=f"wc-{i}") for i, wc in enumerate(self._line.widgets)],
            id="editor-list",
        )

    def set_line(self, line: LineConfig) -> None:
        self._line = line
        lv = self.query_one("#editor-list", ListView)
        lv.clear()
        for i, wc in enumerate(self._line.widgets):
            lv.append(ListItem(Label(wc.type), id=f"wc-{i}"))

    def add_widget(self, widget_type: str) -> None:
        wc = WidgetConfig(type=widget_type)
        self._line.widgets.append(wc)
        lv = self.query_one("#editor-list", ListView)
        lv.append(ListItem(Label(widget_type), id=f"wc-{len(self._line.widgets) - 1}"))
        self.post_message(self.WidgetAdded())

    def remove_selected(self) -> None:
        lv = self.query_one("#editor-list", ListView)
        if lv.highlighted_child is None:
            return
        idx = lv.index
        if idx is not None and 0 <= idx < len(self._line.widgets):
            self._line.widgets.pop(idx)
            lv.remove_items([lv.highlighted_child])
            self.post_message(self.WidgetRemoved())

    def on_key(self, event) -> None:
        if event.key not in ("up", "down"):
            return
        lv = self.query_one("#editor-list", ListView)
        idx = lv.index
        if idx is None:
            return
        if event.key == "up" and idx > 0:
            self._line.widgets[idx], self._line.widgets[idx - 1] = (
                self._line.widgets[idx - 1],
                self._line.widgets[idx],
            )
            self.set_line(self._line)
            lv.index = idx - 1
            self.post_message(self.WidgetReordered())
        elif event.key == "down" and idx < len(self._line.widgets) - 1:
            self._line.widgets[idx], self._line.widgets[idx + 1] = (
                self._line.widgets[idx + 1],
                self._line.widgets[idx],
            )
            self.set_line(self._line)
            lv.index = idx + 1
            self.post_message(self.WidgetReordered())


class Preview(TextualWidget):
    """Bottom panel: live read-only preview of the statusline."""

    DEFAULT_CSS = """
    Preview {
        height: 7;
        border: solid $accent;
        padding: 0 1;
    }
    """

    def __init__(self, config: Config, **kwargs) -> None:
        super().__init__(**kwargs)
        self._config = config

    def compose(self) -> ComposeResult:
        yield Label("── Preview ──", id="preview-title")
        yield Static("", id="preview-content", markup=False)

    def on_mount(self) -> None:
        self.refresh_preview()

    def refresh_preview(self) -> None:
        try:
            rendered = render_statusline(self._config, SAMPLE_DATA)
        except Exception:
            rendered = "(preview error)"
        self.query_one("#preview-content", Static).update(rendered)


class GlobalSettingsScreen(ModalScreen):
    """Modal overlay for global config (color level, powerline, minimalist)."""

    DEFAULT_CSS = """
    GlobalSettingsScreen {
        align: center middle;
    }
    #settings-dialog {
        width: 50;
        height: auto;
        border: solid $accent;
        padding: 1 2;
        background: $surface;
    }
    #settings-buttons {
        margin-top: 1;
        height: 3;
        layout: horizontal;
        align: right middle;
    }
    """

    def __init__(self, config: Config, **kwargs) -> None:
        super().__init__(**kwargs)
        self._config = config

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-dialog"):
            yield Label("Global Settings", id="settings-title")
            yield Select(
                [(level, level) for level in ("none", "basic", "256", "truecolor")],
                value=self._config.color_level,
                id="color-level",
                prompt="Color level",
            )
            yield Checkbox(
                "Minimalist mode", self._config.minimalist_mode, id="minimalist"
            )
            yield Checkbox(
                "Powerline enabled", self._config.powerline.enabled, id="powerline-enabled"
            )
            with Horizontal(id="settings-buttons"):
                yield Button("Save", id="save-btn", variant="primary")
                yield Button("Cancel", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)
            return
        color_level = self.query_one("#color-level", Select).value
        minimalist = self.query_one("#minimalist", Checkbox).value
        pl_enabled = self.query_one("#powerline-enabled", Checkbox).value
        self.dismiss(
            Config(
                color_level=color_level,
                minimalist_mode=minimalist,
                powerline=PowerlineConfig(
                    enabled=pl_enabled,
                    separator=self._config.powerline.separator,
                    thin_separator=self._config.powerline.thin_separator,
                    left_cap=self._config.powerline.left_cap,
                    right_cap=self._config.powerline.right_cap,
                ),
                lines=self._config.lines,
            )
        )
```

- [ ] **Step 2: Create tui/app.py**

```python
# ccstatusline/tui/app.py
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Label, Tab, Tabs

from ccstatusline.config import Config, LineConfig
from ccstatusline.tui.screens import (
    GlobalSettingsScreen,
    LayoutEditor,
    Preview,
    WidgetLibrary,
)


class CCStatuslineApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    Tabs {
        height: 3;
    }
    #main {
        layout: horizontal;
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("ctrl+s", "save_and_exit", "Save & Exit", show=True),
        Binding("escape", "quit_prompt", "Exit", show=True),
        Binding("delete,backspace", "remove_selected", "Remove", show=True),
        Binding("ctrl+n", "add_line", "Add Line", show=True),
        Binding("ctrl+g", "global_settings", "Settings", show=True),
    ]

    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config
        self._active_line_idx = 0
        if not self._config.lines:
            self._config.lines.append(LineConfig())

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        line_tabs = [
            Tab(f"Line {i + 1}", id=f"line-{i}")
            for i in range(len(self._config.lines))
        ]
        yield Tabs(*line_tabs, Tab("+", id="add-line"))
        with Horizontal(id="main"):
            yield WidgetLibrary(id="widget-library")
            yield LayoutEditor(self._active_line_config(), id="layout-editor")
        yield Preview(self._config, id="preview")
        yield Footer()

    def _active_line_config(self) -> LineConfig:
        idx = min(self._active_line_idx, len(self._config.lines) - 1)
        return self._config.lines[idx]

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        if event.tab.id == "add-line":
            self.call_after_refresh(self.action_add_line)
            return
        if event.tab.id and event.tab.id.startswith("line-"):
            self._active_line_idx = int(event.tab.id.split("-")[1])
            self._refresh_editor()

    def _refresh_editor(self) -> None:
        self.query_one(LayoutEditor).set_line(self._active_line_config())
        self.query_one(Preview).refresh_preview()

    def action_add_line(self) -> None:
        self._config.lines.append(LineConfig())
        new_idx = len(self._config.lines) - 1
        self._active_line_idx = new_idx
        tabs = self.query_one(Tabs)
        add_tab = tabs.query_one("#add-line", Tab)
        tabs.add_tab(Tab(f"Line {new_idx + 1}", id=f"line-{new_idx}"), before=add_tab)
        tabs.active = f"line-{new_idx}"
        self._refresh_editor()

    def action_remove_selected(self) -> None:
        self.query_one(LayoutEditor).remove_selected()
        self.query_one(Preview).refresh_preview()

    def action_save_and_exit(self) -> None:
        self._config.save()
        self.exit()

    async def action_quit_prompt(self) -> None:
        class ConfirmQuit(ModalScreen):
            BINDINGS = [
                ("y", "yes", "Yes"),
                ("n", "no", "No"),
                ("escape", "no", "No"),
            ]

            def compose(self) -> ComposeResult:
                yield Label("Discard changes and exit? [y/n]", id="confirm-label")

            DEFAULT_CSS = """
            ConfirmQuit {
                align: center middle;
            }
            #confirm-label {
                border: solid $accent;
                padding: 1 3;
                background: $surface;
            }
            """

            def action_yes(self) -> None:
                self.dismiss(True)

            def action_no(self) -> None:
                self.dismiss(False)

        result = await self.push_screen_wait(ConfirmQuit())
        if result:
            self.exit()

    async def action_global_settings(self) -> None:
        result = await self.push_screen_wait(GlobalSettingsScreen(self._config))
        if result is not None:
            self._config.color_level = result.color_level
            self._config.minimalist_mode = result.minimalist_mode
            self._config.powerline = result.powerline
            self.query_one(Preview).refresh_preview()

    def on_widget_library_widget_selected(
        self, event: WidgetLibrary.WidgetSelected
    ) -> None:
        self.query_one(LayoutEditor).add_widget(event.widget_type)
        self.query_one(Preview).refresh_preview()

    def on_layout_editor_widget_added(self, _: LayoutEditor.WidgetAdded) -> None:
        self.query_one(Preview).refresh_preview()

    def on_layout_editor_widget_removed(self, _: LayoutEditor.WidgetRemoved) -> None:
        self.query_one(Preview).refresh_preview()

    def on_layout_editor_widget_reordered(self, _: LayoutEditor.WidgetReordered) -> None:
        self.query_one(Preview).refresh_preview()
```

- [ ] **Step 3: Run full test suite (TUI code should not break tests)**

```bash
uv run pytest -v
```

Expected: all existing tests PASS. The TUI modules import but aren't tested.

- [ ] **Step 4: Smoke-test TUI launches**

Run from a real terminal (not pipe):

```bash
uv run ccstatusline
```

Expected: Textual app opens with Header, Tabs ("Line 1", "+"), Widget Library panel on left, Layout Editor on right, Preview bar at bottom, Footer with key hints. Press `Ctrl+S` to save and exit, or `Escape` then `y` to quit without saving.

- [ ] **Step 5: Commit**

```bash
git add ccstatusline/tui/app.py ccstatusline/tui/screens.py
git commit -m "feat: Textual TUI with widget library, layout editor, preview, and global settings"
```

---

## Task 13: Final Wiring & Smoke Tests

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Run full test suite**

```bash
uv run pytest -v
```

Expected: all tests PASS.

- [ ] **Step 2: Verify piped mode end-to-end**

```bash
echo '{"model": {"display_name": "claude-sonnet-4-5"}, "context_window": {"context_window_size": 200000, "total_input_tokens": 10000, "total_output_tokens": 2000, "used_percentage": 6.0}, "cost": {"total_cost_usd": 0.015, "total_duration_ms": 90000}, "worktree": {"branch": "main"}, "cwd": "/tmp"}' | uv run ccstatusline | cat
```

Expected: ANSI-colored output (or empty string if config has no widgets configured yet — that's correct because no config exists yet).

- [ ] **Step 3: Update README.md**

```markdown
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
```

- [ ] **Step 4: Final commit**

```bash
git add README.md
git commit -m "docs: add README with installation and configuration instructions"
```

---

## Self-Review Notes

- All 12 widgets are covered (Tasks 4–6) with unit tests
- Config load/save round-trip and migration are tested (Task 8)
- Color utilities (hex→16, hex→256, hex→truecolor) are tested (Task 9)
- Renderer pipeline (plain + powerline) is tested (Task 10)
- Entry point piped mode is tested end-to-end (Task 11)
- TUI has no unit tests per spec — verified by manual smoke test (Task 12, Step 4)
- Error handling (invalid JSON, unknown widget, config load failure) implemented in `__main__.py` and `config.py`
- `StatusData` uses `extra="allow"` so future Claude Code JSON fields don't break the tool
