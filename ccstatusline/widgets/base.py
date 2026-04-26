from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from ccstatusline.data import StatusData

REGISTRY: dict[str, type[Widget]] = {}
CATEGORIES: dict[str, list[str]] = {}

_HEX_COLOR_RE = re.compile(r"^#?(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


class WidgetConfig(BaseModel):
    type: str
    fg: str = "#ffffff"
    bg: str = "#000000"
    bold: bool = False
    padding: int = 1
    options: dict = Field(default_factory=dict)

    @field_validator("fg", "bg")
    @classmethod
    def _validate_hex_color(cls, v: str, info) -> str:
        if isinstance(v, str) and _HEX_COLOR_RE.match(v):
            return v
        return "#ffffff" if info.field_name == "fg" else "#000000"


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
    def render(
        self,
        data: StatusData,
        config: WidgetConfig,
        color_level: str = "truecolor",
    ) -> str: ...
