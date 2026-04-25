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
