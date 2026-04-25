from __future__ import annotations

import subprocess

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
