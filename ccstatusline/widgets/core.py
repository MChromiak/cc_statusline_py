from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ccstatusline.data import StatusData
from ccstatusline.widgets.base import Widget, WidgetConfig, register_widget


@register_widget("model")
class ModelWidget(Widget):
    category = "session"
    default_prefix = " Model: "

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        return data.model_name


@register_widget("tokens_used")
class TokensUsedWidget(Widget):
    category = "tokens"
    default_prefix = " Tokens: "

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        t = data.tokens_used
        if t >= 1_000_000:
            return f"{t / 1_000_000:.1f}M"
        if t >= 1_000:
            return f"{t / 1_000:.1f}k"
        return str(t) if t else ""


@register_widget("context_pct")
class ContextPctWidget(Widget):
    category = "tokens"
    default_prefix = " Ctx: "

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        pct = data.context_used_pct
        return f"{pct:.1f}%" if pct else ""


@register_widget("context_bar")
class ContextBarWidget(Widget):
    category = "tokens"
    default_prefix = " Ctx "

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        if not data.context_window:
            return ""
        width = int(config.options.get("bar_width", 10))
        pct_value = data.context_used_pct
        pct = pct_value / 100.0
        filled = round(width * pct)
        filled_chars = "█" * filled
        unfilled_chars = "░" * (width - filled)

        if color_level == "none":
            return filled_chars + unfilled_chars

        warning = float(config.options.get("warning_threshold", 50.0))
        critical = float(config.options.get("critical_threshold", 80.0))
        if pct_value >= critical:
            threshold_hex = "#ff0000"
        elif pct_value >= warning:
            threshold_hex = "#ffff00"
        else:
            threshold_hex = "#00ff00"

        from ccstatusline.renderer import ansi_fg
        threshold_fg = ansi_fg(threshold_hex, color_level)
        restore_fg = ansi_fg(config.fg, color_level)
        return f"{threshold_fg}{filled_chars}{restore_fg}{unfilled_chars}"


@register_widget("git_branch")
class GitBranchWidget(Widget):
    category = "git"
    default_prefix = " Branch: "

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
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
    default_prefix = " Status: "

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=2,
                cwd=data.cwd or None,
            )
            if result.returncode != 0:
                return ""
            return "✎" if result.stdout.strip() else "✔"
        except Exception:
            return ""


@register_widget("git_sha")
class GitShaWidget(Widget):
    category = "git"
    default_prefix = " SHA: "

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                timeout=2,
                cwd=data.cwd or None,
            )
            if result.returncode != 0:
                return ""
            return result.stdout.strip()
        except Exception:
            return ""


def _git_count(args: list[str], cwd: str | None) -> int:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=2,
            cwd=cwd,
        )
        if result.returncode != 0:
            return 0
        return int(result.stdout.strip() or 0)
    except Exception:
        return 0


@register_widget("git_ahead")
class GitAheadWidget(Widget):
    category = "git"

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        n = _git_count(
            ["git", "rev-list", "--count", "@{upstream}..HEAD"],
            data.cwd or None,
        )
        return f"↑{n}" if n else ""


@register_widget("git_behind")
class GitBehindWidget(Widget):
    category = "git"

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        n = _git_count(
            ["git", "rev-list", "--count", "HEAD..@{upstream}"],
            data.cwd or None,
        )
        return f"↓{n}" if n else ""


def _porcelain_lines(cwd: str | None) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=cwd,
        )
        if result.returncode != 0:
            return []
        return [line for line in result.stdout.splitlines() if line]
    except Exception:
        return []


@register_widget("git_staged")
class GitStagedWidget(Widget):
    category = "git"

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        lines = _porcelain_lines(data.cwd or None)
        n = sum(1 for line in lines if len(line) >= 2 and line[0] in "MADRC")
        return f"●{n}" if n else ""


@register_widget("git_unstaged")
class GitUnstagedWidget(Widget):
    category = "git"

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        lines = _porcelain_lines(data.cwd or None)
        n = sum(1 for line in lines if len(line) >= 2 and line[1] in "MD")
        return f"✚{n}" if n else ""


@register_widget("git_untracked")
class GitUntrackedWidget(Widget):
    category = "git"

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        lines = _porcelain_lines(data.cwd or None)
        n = sum(1 for line in lines if line.startswith("??"))
        return f"…{n}" if n else ""


@register_widget("session_duration")
class SessionDurationWidget(Widget):
    category = "session"
    default_prefix = " Time: "

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
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
    default_prefix = " Cost: "

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        cost = data.cost_usd
        return f"${cost:.4f}" if cost else ""


@register_widget("burn_rate")
class BurnRateWidget(Widget):
    category = "session"
    default_prefix = " Rate: "

    def render(
        self,
        data: StatusData,
        config: WidgetConfig,
        color_level: str = "truecolor",
    ) -> str:
        cost = data.cost_usd
        duration_ms = data.session_duration_ms
        if not cost or not duration_ms:
            return ""
        if duration_ms < 600_000:
            rate_per_min = cost / (duration_ms / 60_000)
            return f"${rate_per_min:.3f}/min"
        rate_per_hour = cost / (duration_ms / 3_600_000)
        return f"${rate_per_hour:.2f}/h"


@register_widget("session_name")
class SessionNameWidget(Widget):
    category = "session"
    default_prefix = " Session: "

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        if not data.session_id:
            return ""
        length = int(config.options.get("length", 8))
        return data.session_id[:length]


@register_widget("thinking_effort")
class ThinkingEffortWidget(Widget):
    category = "session"
    default_prefix = " Effort: "

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        if isinstance(data.effort, dict) and data.effort.get("level"):
            return str(data.effort["level"])
        return ""


@register_widget("block_reset_timer")
class BlockResetTimerWidget(Widget):
    category = "tokens"
    default_prefix = " Reset: "

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        if not data.rate_limits:
            return ""
        window = config.options.get("window", "five_hour")
        bucket = data.rate_limits.get(window)
        if not isinstance(bucket, dict):
            return ""
        resets_at = bucket.get("resets_at")
        if not resets_at:
            return ""
        seconds = self._seconds_until(resets_at)
        if seconds is None or seconds <= 0:
            return ""
        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)
        if hours:
            return f"{hours}h{mins}m"
        if mins:
            return f"{mins}m{secs}s"
        return f"{secs}s"

    @staticmethod
    def _seconds_until(resets_at) -> float | None:
        from datetime import datetime, timezone
        if isinstance(resets_at, (int, float)):
            return float(resets_at) - datetime.now(timezone.utc).timestamp()
        try:
            ts = str(resets_at).replace("Z", "+00:00")
            target = datetime.fromisoformat(ts)
            if target.tzinfo is None:
                target = target.replace(tzinfo=timezone.utc)
            return (target - datetime.now(timezone.utc)).total_seconds()
        except Exception:
            return None


@register_widget("vim_mode")
class VimModeWidget(Widget):
    category = "system"
    default_prefix = " Vim: "

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        if not data.vim:
            return ""
        for key in ("mode", "current_mode", "name"):
            value = data.vim.get(key)
            if value:
                return str(value)
        return ""


@register_widget("cwd")
class CwdWidget(Widget):
    category = "system"
    default_prefix = " Dir: "

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        path = data.cwd or ""
        if not path:
            return ""
        if config.options.get("full_path"):
            return path
        return Path(path).name


@register_widget("claude_email")
class ClaudeEmailWidget(Widget):
    category = "system"
    default_prefix = " "

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
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

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        return config.options.get("text", "")


@register_widget("separator")
class SeparatorWidget(Widget):
    category = "custom"

    def render(self, data: StatusData, config: WidgetConfig, color_level: str = "truecolor") -> str:
        return config.options.get("char", " │ ")
