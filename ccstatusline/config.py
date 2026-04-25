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
    "GitSha": "git_sha",
    "GitAhead": "git_ahead",
    "GitBehind": "git_behind",
    "GitStaged": "git_staged",
    "GitUnstaged": "git_unstaged",
    "GitUntracked": "git_untracked",
    "TokensInput": "tokens_used",
    "TokensUsed": "tokens_used",
    "ContextPercentage": "context_pct",
    "ContextBar": "context_bar",
    "BlockResetTimer": "block_reset_timer",
    "BurnRate": "burn_rate",
    "SessionDuration": "session_duration",
    "SessionClock": "session_duration",
    "SessionCost": "session_cost",
    "SessionName": "session_name",
    "ThinkingEffort": "thinking_effort",
    "VimMode": "vim_mode",
    "CurrentWorkingDir": "cwd",
    "ClaudeAccountEmail": "claude_email",
    "CustomText": "custom_text",
    "Separator": "separator",
}


class PowerlineConfig(BaseModel):
    enabled: bool = True
    separator: str = ""
    thin_separator: str = ""
    left_cap: str = ""
    right_cap: str = ""


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
        separator=pl_raw.get("separator") or "",
        thin_separator=pl_raw.get("thinSeparator") or "",
        left_cap=pl_raw.get("leftCap") or "",
        right_cap=pl_raw.get("rightCap") or "",
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
