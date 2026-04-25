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
    def render(
        self,
        data: StatusData,
        config: WidgetConfig,
        color_level: str = "truecolor",
    ) -> str: ...
