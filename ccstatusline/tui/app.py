from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Label, Tab, Tabs

from ccstatusline.config import Config, LineConfig
from ccstatusline.tui.screens import (
    GlobalSettingsScreen,
    LayoutEditor,
    Preview,
    WidgetLibrary,
)


class CCStatuslineApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    Tabs {
        height: 3;
    }
    #main {
        layout: horizontal;
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("ctrl+s", "save_and_exit", "Save & Exit", show=True),
        Binding("escape", "quit_prompt", "Exit", show=True),
        Binding("delete,backspace", "remove_selected", "Remove", show=True),
        Binding("ctrl+n", "add_line", "Add Line", show=True),
        Binding("ctrl+g", "global_settings", "Settings", show=True),
    ]

    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config
        self._active_line_idx = 0
        if not self._config.lines:
            self._config.lines.append(LineConfig())

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        line_tabs = [
            Tab(f"Line {i + 1}", id=f"line-{i}")
            for i in range(len(self._config.lines))
        ]
        yield Tabs(*line_tabs, Tab("+", id="add-line"))
        with Horizontal(id="main"):
            yield WidgetLibrary(id="widget-library")
            yield LayoutEditor(self._active_line_config(), id="layout-editor")
        yield Preview(self._config, id="preview")
        yield Footer()

    def _active_line_config(self) -> LineConfig:
        idx = min(self._active_line_idx, len(self._config.lines) - 1)
        return self._config.lines[idx]

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        if event.tab.id == "add-line":
            self.call_after_refresh(self.action_add_line)
            return
        if event.tab.id and event.tab.id.startswith("line-"):
            self._active_line_idx = int(event.tab.id.split("-")[1])
            self._refresh_editor()

    def _refresh_editor(self) -> None:
        self.query_one(LayoutEditor).set_line(self._active_line_config())
        self.query_one(Preview).refresh_preview()

    def action_add_line(self) -> None:
        self._config.lines.append(LineConfig())
        new_idx = len(self._config.lines) - 1
        self._active_line_idx = new_idx
        tabs = self.query_one(Tabs)
        add_tab = tabs.query_one("#add-line", Tab)
        tabs.add_tab(Tab(f"Line {new_idx + 1}", id=f"line-{new_idx}"), before=add_tab)
        tabs.active = f"line-{new_idx}"
        self._refresh_editor()

    def action_remove_selected(self) -> None:
        self.query_one(LayoutEditor).remove_selected()
        self.query_one(Preview).refresh_preview()

    def action_save_and_exit(self) -> None:
        self._config.save()
        self.exit()

    async def action_quit_prompt(self) -> None:
        class ConfirmQuit(ModalScreen):
            BINDINGS = [
                ("y", "yes", "Yes"),
                ("n", "no", "No"),
                ("escape", "no", "No"),
            ]

            def compose(self) -> ComposeResult:
                yield Label("Discard changes and exit? [y/n]", id="confirm-label")

            DEFAULT_CSS = """
            ConfirmQuit {
                align: center middle;
            }
            #confirm-label {
                border: solid $accent;
                padding: 1 3;
                background: $surface;
            }
            """

            def action_yes(self) -> None:
                self.dismiss(True)

            def action_no(self) -> None:
                self.dismiss(False)

        result = await self.push_screen_wait(ConfirmQuit())
        if result:
            self.exit()

    async def action_global_settings(self) -> None:
        result = await self.push_screen_wait(GlobalSettingsScreen(self._config))
        if result is not None:
            self._config.color_level = result.color_level
            self._config.minimalist_mode = result.minimalist_mode
            self._config.powerline = result.powerline
            self.query_one(Preview).refresh_preview()

    def on_widget_library_widget_selected(
        self, event: WidgetLibrary.WidgetSelected
    ) -> None:
        self.query_one(LayoutEditor).add_widget(event.widget_type)
        self.query_one(Preview).refresh_preview()

    def on_layout_editor_widget_added(self, _: LayoutEditor.WidgetAdded) -> None:
        self.query_one(Preview).refresh_preview()

    def on_layout_editor_widget_removed(self, _: LayoutEditor.WidgetRemoved) -> None:
        self.query_one(Preview).refresh_preview()

    def on_layout_editor_widget_reordered(self, _: LayoutEditor.WidgetReordered) -> None:
        self.query_one(Preview).refresh_preview()
