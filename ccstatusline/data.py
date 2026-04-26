from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StatusData(BaseModel):
    model_config = ConfigDict(extra="allow")

    hook_event_name: str | None = None
    session_id: str | None = None
    transcript_path: str | None = None
    cwd: str | None = None
    model: str | dict | None = None
    version: str | None = None
    output_style: str | dict | None = None
    effort: dict | None = None
    workspace: dict | None = None
    cost: dict | None = None
    context_window: dict | None = None
    vim: dict | None = None
    worktree: dict | None = None
    rate_limits: dict | None = None

    @property
    def model_name(self) -> str:
        if isinstance(self.model, dict):
            return self.model.get("display_name") or self.model.get("id") or ""
        if isinstance(self.model, str):
            return self.model
        return ""

    @property
    def tokens_used(self) -> int:
        if not self.context_window:
            return 0
        inp = self.context_window.get("total_input_tokens") or 0
        out = self.context_window.get("total_output_tokens") or 0
        return inp + out

    @property
    def context_window_size(self) -> int:
        if not self.context_window:
            return 0
        return self.context_window.get("context_window_size") or 0

    @property
    def context_used_pct(self) -> float:
        if not self.context_window:
            return 0.0
        return float(self.context_window.get("used_percentage") or 0)

    @property
    def cost_usd(self) -> float:
        if not self.cost:
            return 0.0
        return float(self.cost.get("total_cost_usd") or 0)

    @property
    def session_duration_ms(self) -> int:
        if not self.cost:
            return 0
        return int(self.cost.get("total_duration_ms") or 0)
