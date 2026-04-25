from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
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

    class WidgetSelected(Message):
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

    class WidgetAdded(Message):
        pass

    class WidgetRemoved(Message):
        pass

    class WidgetReordered(Message):
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
