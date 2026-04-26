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


import ccstatusline.widgets.core  # noqa: F401
from ccstatusline.config import Config, LineConfig, PowerlineConfig
from ccstatusline.renderer import render_statusline, visible_len, ANSI_ESCAPE_RE
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


def test_render_drops_separator_between_empty_widgets():
    from ccstatusline.config import Config, LineConfig
    from ccstatusline.data import StatusData
    from ccstatusline.renderer import render_statusline
    # model has data, session_cost has none, separator between them, then git_branch
    # session_cost returns empty → its surrounding separators should also drop
    widgets = [
        WidgetConfig(type="model", fg="#fff", bg="#000", padding=1),
        WidgetConfig(type="separator", fg="#fff", bg="#000", padding=0),
        WidgetConfig(type="session_cost", fg="#fff", bg="#000", padding=1),
        WidgetConfig(type="separator", fg="#fff", bg="#000", padding=0),
        WidgetConfig(type="separator", fg="#fff", bg="#000", padding=0),
    ]
    c = Config(lines=[LineConfig(widgets=widgets)], minimalist_mode=True)
    # session_cost empty (no cost in StatusData), so model + 2 trailing separators
    # all trailing separators must be dropped
    d = StatusData(model={"display_name": "X"})
    result = _strip_ansi(render_statusline(c, d))
    # Should NOT end with separator glyphs
    assert "│" not in result, f"expected no leftover separators, got: {result!r}"


def test_render_collapses_consecutive_separators():
    from ccstatusline.config import Config, LineConfig
    from ccstatusline.data import StatusData
    from ccstatusline.renderer import render_statusline
    widgets = [
        WidgetConfig(type="model", fg="#fff", bg="#000", padding=0),
        WidgetConfig(type="separator", fg="#fff", bg="#000", padding=0),
        WidgetConfig(type="separator", fg="#fff", bg="#000", padding=0),
        WidgetConfig(type="separator", fg="#fff", bg="#000", padding=0),
        WidgetConfig(type="session_cost", fg="#fff", bg="#000", padding=0),
    ]
    c = Config(lines=[LineConfig(widgets=widgets)], minimalist_mode=True)
    d = StatusData(model={"display_name": "X"}, cost={"total_cost_usd": 0.5})
    result = _strip_ansi(render_statusline(c, d))
    # 3 consecutive separators must collapse to exactly 1
    assert result.count("│") == 1, f"expected 1 separator, got: {result!r}"


def test_render_drops_leading_separator():
    from ccstatusline.config import Config, LineConfig
    from ccstatusline.data import StatusData
    from ccstatusline.renderer import render_statusline
    widgets = [
        WidgetConfig(type="separator", fg="#fff", bg="#000", padding=0),
        WidgetConfig(type="model", fg="#fff", bg="#000", padding=0),
    ]
    c = Config(lines=[LineConfig(widgets=widgets)], minimalist_mode=True)
    d = StatusData(model={"display_name": "X"})
    result = _strip_ansi(render_statusline(c, d))
    assert "│" not in result, f"expected no leading separator, got: {result!r}"


def test_render_powerline_contains_separator_glyph(sample_data):
    wc1 = WidgetConfig(type="model", fg="#ffffff", bg="#1e1e2e", padding=1)
    wc2 = WidgetConfig(type="session_cost", fg="#ffffff", bg="#313244", padding=1)
    pl = PowerlineConfig(enabled=True, separator="", left_cap="", right_cap="")
    c = Config(
        lines=[LineConfig(widgets=[wc1, wc2])],
        powerline=pl,
        minimalist_mode=True,
    )
    result = render_statusline(c, sample_data)
    visible = _strip_ansi(result)
    assert "" in visible or "" in visible


def test_render_plain_no_powerline_glyphs(sample_data):
    wc = WidgetConfig(type="model", fg="#ffffff", bg="#000000", padding=1)
    pl = PowerlineConfig(enabled=False)
    c = Config(lines=[LineConfig(widgets=[wc])], powerline=pl, minimalist_mode=True)
    result = render_statusline(c, sample_data)
    assert "" not in result
    assert "" not in result

import json
import subprocess
import sys


def test_piped_mode_outputs_statusline():
    """End-to-end: pipe JSON to the entry point, expect successful exit."""
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


def test_render_survives_invalid_color_in_config(sample_data):
    """A bad fg/bg must not raise — statusline should still render the widget text."""
    wc = WidgetConfig(type="model", fg="not-a-color", bg="also-bad", padding=0)
    c = Config(
        lines=[LineConfig(widgets=[wc])],
        powerline=PowerlineConfig(enabled=False),
        minimalist_mode=True,
    )
    result = render_statusline(c, sample_data)
    assert "claude-sonnet-4-5" in _strip_ansi(result)
