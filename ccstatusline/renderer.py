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
