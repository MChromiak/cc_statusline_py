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
