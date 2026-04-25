import pytest
from ccstatusline.data import StatusData
from ccstatusline.widgets.base import REGISTRY, CATEGORIES, Widget, WidgetConfig, register_widget


def test_register_widget_adds_to_registry():
    @register_widget("_test_widget")
    class MyWidget(Widget):
        category = "custom"
        def render(self, data, config):
            return "hello"

    assert "_test_widget" in REGISTRY
    assert REGISTRY["_test_widget"] is MyWidget


def test_register_widget_adds_to_categories():
    assert "_test_widget" in CATEGORIES.get("custom", [])


def test_widget_config_defaults():
    wc = WidgetConfig(type="model")
    assert wc.fg == "#ffffff"
    assert wc.bg == "#000000"
    assert wc.bold is False
    assert wc.padding == 1
    assert wc.options == {}


def test_widget_render_is_abstract():
    class IncompleteWidget(Widget):
        category = "custom"
        # render not implemented

    with pytest.raises(TypeError):
        IncompleteWidget()


import ccstatusline.widgets.core  # ensure widgets are registered
from ccstatusline.widgets.base import REGISTRY, WidgetConfig


def _wc(widget_type: str, **options) -> WidgetConfig:
    return WidgetConfig(type=widget_type, options=options)


def test_model_widget_display_name(sample_data):
    w = REGISTRY["model"]()
    assert w.render(sample_data, _wc("model")) == "claude-sonnet-4-5"


def test_model_widget_empty():
    from ccstatusline.data import StatusData
    w = REGISTRY["model"]()
    assert w.render(StatusData(), _wc("model")) == ""


def test_tokens_used_widget_formats_thousands(sample_data):
    w = REGISTRY["tokens_used"]()
    result = w.render(sample_data, _wc("tokens_used"))
    assert result == "18.0k"


def test_tokens_used_widget_formats_millions():
    from ccstatusline.data import StatusData
    d = StatusData(context_window={"total_input_tokens": 1_200_000, "total_output_tokens": 0})
    w = REGISTRY["tokens_used"]()
    assert w.render(d, _wc("tokens_used")) == "1.2M"


def test_tokens_used_widget_small():
    from ccstatusline.data import StatusData
    d = StatusData(context_window={"total_input_tokens": 500, "total_output_tokens": 0})
    w = REGISTRY["tokens_used"]()
    assert w.render(d, _wc("tokens_used")) == "500"


def test_context_pct_widget(sample_data):
    w = REGISTRY["context_pct"]()
    assert w.render(sample_data, _wc("context_pct")) == "9.0%"


def test_context_pct_widget_empty():
    from ccstatusline.data import StatusData
    w = REGISTRY["context_pct"]()
    assert w.render(StatusData(), _wc("context_pct")) == ""


def test_context_bar_widget_default_width(sample_data):
    w = REGISTRY["context_bar"]()
    result = w.render(sample_data, _wc("context_bar"))
    assert len(result) == 10
    assert result.startswith("█") or result.startswith("░")


def test_context_bar_widget_custom_width(sample_data):
    w = REGISTRY["context_bar"]()
    result = w.render(sample_data, _wc("context_bar", bar_width=5))
    assert len(result) == 5


def test_git_branch_from_worktree(sample_data):
    w = REGISTRY["git_branch"]()
    assert w.render(sample_data, _wc("git_branch")) == "feat/python-port"


def test_git_branch_empty_when_no_worktree():
    from ccstatusline.data import StatusData
    from unittest.mock import patch
    d = StatusData(cwd="/tmp/notarepo")
    w = REGISTRY["git_branch"]()
    with patch("subprocess.run", side_effect=Exception("no git")):
        assert w.render(d, _wc("git_branch")) == ""


def test_git_status_clean():
    from ccstatusline.data import StatusData
    from unittest.mock import MagicMock, patch
    d = StatusData(cwd="/tmp/repo")
    mock_result = MagicMock()
    mock_result.stdout = ""
    w = REGISTRY["git_status"]()
    with patch("subprocess.run", return_value=mock_result):
        assert w.render(d, _wc("git_status")) == "✔"


def test_git_status_dirty():
    from ccstatusline.data import StatusData
    from unittest.mock import MagicMock, patch
    d = StatusData(cwd="/tmp/repo")
    mock_result = MagicMock()
    mock_result.stdout = " M somefile.py\n"
    w = REGISTRY["git_status"]()
    with patch("subprocess.run", return_value=mock_result):
        assert w.render(d, _wc("git_status")) == "✎"


def test_git_status_error_returns_empty():
    from ccstatusline.data import StatusData
    from unittest.mock import patch
    d = StatusData()
    w = REGISTRY["git_status"]()
    with patch("subprocess.run", side_effect=Exception("no git")):
        assert w.render(d, _wc("git_status")) == ""


def test_session_duration_seconds(sample_data):
    from ccstatusline.data import StatusData
    d = StatusData(cost={"total_duration_ms": 45000})
    w = REGISTRY["session_duration"]()
    assert w.render(d, _wc("session_duration")) == "45s"


def test_session_duration_minutes():
    from ccstatusline.data import StatusData
    d = StatusData(cost={"total_duration_ms": 135000})
    w = REGISTRY["session_duration"]()
    assert w.render(d, _wc("session_duration")) == "2m15s"


def test_session_duration_hours():
    from ccstatusline.data import StatusData
    d = StatusData(cost={"total_duration_ms": 3_700_000})
    w = REGISTRY["session_duration"]()
    assert w.render(d, _wc("session_duration")) == "1h1m"


def test_session_duration_empty():
    from ccstatusline.data import StatusData
    w = REGISTRY["session_duration"]()
    assert w.render(StatusData(), _wc("session_duration")) == ""


def test_session_cost(sample_data):
    w = REGISTRY["session_cost"]()
    assert w.render(sample_data, _wc("session_cost")) == "$0.0234"


def test_session_cost_empty():
    from ccstatusline.data import StatusData
    w = REGISTRY["session_cost"]()
    assert w.render(StatusData(), _wc("session_cost")) == ""


def test_cwd_widget_basename(sample_data):
    w = REGISTRY["cwd"]()
    assert w.render(sample_data, _wc("cwd")) == "myproject"


def test_cwd_widget_full_path(sample_data):
    w = REGISTRY["cwd"]()
    assert w.render(sample_data, _wc("cwd", full_path=True)) == "/home/user/myproject"


def test_cwd_widget_empty():
    from ccstatusline.data import StatusData
    w = REGISTRY["cwd"]()
    assert w.render(StatusData(), _wc("cwd")) == ""


def test_custom_text_widget():
    from ccstatusline.data import StatusData
    w = REGISTRY["custom_text"]()
    assert w.render(StatusData(), _wc("custom_text", text="hello world")) == "hello world"


def test_custom_text_widget_empty():
    from ccstatusline.data import StatusData
    w = REGISTRY["custom_text"]()
    assert w.render(StatusData(), _wc("custom_text")) == ""


def test_separator_widget_default():
    from ccstatusline.data import StatusData
    w = REGISTRY["separator"]()
    assert w.render(StatusData(), _wc("separator")) == " │ "


def test_separator_widget_custom():
    from ccstatusline.data import StatusData
    w = REGISTRY["separator"]()
    assert w.render(StatusData(), _wc("separator", char=" | ")) == " | "


def test_claude_email_widget_no_file():
    from ccstatusline.data import StatusData
    from unittest.mock import patch
    from pathlib import Path
    w = REGISTRY["claude_email"]()
    with patch.object(Path, "exists", return_value=False):
        assert w.render(StatusData(), _wc("claude_email")) == ""


def _mock_run(stdout: str, returncode: int = 0):
    from unittest.mock import MagicMock
    m = MagicMock()
    m.stdout = stdout
    m.returncode = returncode
    return m


def test_git_sha_widget():
    from unittest.mock import patch
    d = StatusData(cwd="/tmp/repo")
    w = REGISTRY["git_sha"]()
    with patch("subprocess.run", return_value=_mock_run("a1b2c3d\n")):
        assert w.render(d, _wc("git_sha")) == "a1b2c3d"


def test_git_sha_widget_error_returns_empty():
    from unittest.mock import patch
    w = REGISTRY["git_sha"]()
    with patch("subprocess.run", side_effect=Exception("no git")):
        assert w.render(StatusData(), _wc("git_sha")) == ""


def test_git_sha_widget_nonzero_returncode_returns_empty():
    from unittest.mock import patch
    w = REGISTRY["git_sha"]()
    with patch("subprocess.run", return_value=_mock_run("", returncode=128)):
        assert w.render(StatusData(), _wc("git_sha")) == ""


def test_git_ahead_widget():
    from unittest.mock import patch
    d = StatusData(cwd="/tmp/repo")
    w = REGISTRY["git_ahead"]()
    with patch("subprocess.run", return_value=_mock_run("3\n")):
        assert w.render(d, _wc("git_ahead")) == "↑3"


def test_git_ahead_widget_zero_returns_empty():
    from unittest.mock import patch
    w = REGISTRY["git_ahead"]()
    with patch("subprocess.run", return_value=_mock_run("0\n")):
        assert w.render(StatusData(), _wc("git_ahead")) == ""


def test_git_ahead_widget_no_upstream_returns_empty():
    from unittest.mock import patch
    w = REGISTRY["git_ahead"]()
    with patch("subprocess.run", return_value=_mock_run("", returncode=128)):
        assert w.render(StatusData(), _wc("git_ahead")) == ""


def test_git_behind_widget():
    from unittest.mock import patch
    w = REGISTRY["git_behind"]()
    with patch("subprocess.run", return_value=_mock_run("2\n")):
        assert w.render(StatusData(), _wc("git_behind")) == "↓2"


def test_git_behind_widget_zero_returns_empty():
    from unittest.mock import patch
    w = REGISTRY["git_behind"]()
    with patch("subprocess.run", return_value=_mock_run("0\n")):
        assert w.render(StatusData(), _wc("git_behind")) == ""


def test_git_staged_widget():
    from unittest.mock import patch
    porcelain = "M  staged.py\nA  added.py\n M unstaged.py\n?? new.py\n"
    w = REGISTRY["git_staged"]()
    with patch("subprocess.run", return_value=_mock_run(porcelain)):
        assert w.render(StatusData(), _wc("git_staged")) == "●2"


def test_git_staged_widget_clean_returns_empty():
    from unittest.mock import patch
    w = REGISTRY["git_staged"]()
    with patch("subprocess.run", return_value=_mock_run("")):
        assert w.render(StatusData(), _wc("git_staged")) == ""


def test_git_unstaged_widget():
    from unittest.mock import patch
    porcelain = "M  staged.py\n M mod1.py\n D del1.py\n?? new.py\n"
    w = REGISTRY["git_unstaged"]()
    with patch("subprocess.run", return_value=_mock_run(porcelain)):
        assert w.render(StatusData(), _wc("git_unstaged")) == "✚2"


def test_git_unstaged_widget_clean_returns_empty():
    from unittest.mock import patch
    w = REGISTRY["git_unstaged"]()
    with patch("subprocess.run", return_value=_mock_run("")):
        assert w.render(StatusData(), _wc("git_unstaged")) == ""


def test_git_untracked_widget():
    from unittest.mock import patch
    porcelain = "M  staged.py\n M mod.py\n?? new1.py\n?? new2.py\n?? new3.py\n"
    w = REGISTRY["git_untracked"]()
    with patch("subprocess.run", return_value=_mock_run(porcelain)):
        assert w.render(StatusData(), _wc("git_untracked")) == "…3"


def test_git_untracked_widget_clean_returns_empty():
    from unittest.mock import patch
    w = REGISTRY["git_untracked"]()
    with patch("subprocess.run", return_value=_mock_run("")):
        assert w.render(StatusData(), _wc("git_untracked")) == ""


def test_session_name_widget_default_length():
    d = StatusData(session_id="abcdef1234567890")
    w = REGISTRY["session_name"]()
    assert w.render(d, _wc("session_name")) == "abcdef12"


def test_session_name_widget_custom_length():
    d = StatusData(session_id="abcdef1234567890")
    w = REGISTRY["session_name"]()
    assert w.render(d, _wc("session_name", length=4)) == "abcd"


def test_session_name_widget_empty():
    w = REGISTRY["session_name"]()
    assert w.render(StatusData(), _wc("session_name")) == ""


def test_thinking_effort_widget_top_level():
    d = StatusData.model_validate({"thinking_effort": "high"})
    w = REGISTRY["thinking_effort"]()
    assert w.render(d, _wc("thinking_effort")) == "high"


def test_thinking_effort_widget_inside_model():
    d = StatusData(model={"id": "x", "thinking_effort": "medium"})
    w = REGISTRY["thinking_effort"]()
    assert w.render(d, _wc("thinking_effort")) == "medium"


def test_thinking_effort_widget_empty():
    w = REGISTRY["thinking_effort"]()
    assert w.render(StatusData(), _wc("thinking_effort")) == ""


def test_block_reset_timer_widget_seconds():
    d = StatusData(rate_limits={"reset_seconds": 125})
    w = REGISTRY["block_reset_timer"]()
    assert w.render(d, _wc("block_reset_timer")) == "2m5s"


def test_block_reset_timer_widget_hours():
    d = StatusData(rate_limits={"reset_seconds": 3700})
    w = REGISTRY["block_reset_timer"]()
    assert w.render(d, _wc("block_reset_timer")) == "1h1m"


def test_block_reset_timer_widget_just_seconds():
    d = StatusData(rate_limits={"reset_seconds": 45})
    w = REGISTRY["block_reset_timer"]()
    assert w.render(d, _wc("block_reset_timer")) == "45s"


def test_block_reset_timer_widget_unix_timestamp():
    import time
    d = StatusData(rate_limits={"reset_at_unix": time.time() + 90})
    w = REGISTRY["block_reset_timer"]()
    result = w.render(d, _wc("block_reset_timer"))
    assert result.endswith("s") or result.endswith("m")


def test_block_reset_timer_widget_iso8601():
    from datetime import datetime, timezone, timedelta
    target = datetime.now(timezone.utc) + timedelta(minutes=5)
    d = StatusData(rate_limits={"reset_at": target.isoformat()})
    w = REGISTRY["block_reset_timer"]()
    result = w.render(d, _wc("block_reset_timer"))
    assert "m" in result


def test_block_reset_timer_widget_no_data_returns_empty():
    w = REGISTRY["block_reset_timer"]()
    assert w.render(StatusData(), _wc("block_reset_timer")) == ""


def test_block_reset_timer_widget_already_elapsed_returns_empty():
    d = StatusData(rate_limits={"reset_seconds": -10})
    w = REGISTRY["block_reset_timer"]()
    assert w.render(d, _wc("block_reset_timer")) == ""


def test_vim_mode_widget():
    d = StatusData(vim={"mode": "INSERT"})
    w = REGISTRY["vim_mode"]()
    assert w.render(d, _wc("vim_mode")) == "INSERT"


def test_vim_mode_widget_alt_key():
    d = StatusData(vim={"current_mode": "NORMAL"})
    w = REGISTRY["vim_mode"]()
    assert w.render(d, _wc("vim_mode")) == "NORMAL"


def test_vim_mode_widget_empty():
    w = REGISTRY["vim_mode"]()
    assert w.render(StatusData(), _wc("vim_mode")) == ""


def test_burn_rate_long_session_per_hour():
    d = StatusData(cost={"total_cost_usd": 0.50, "total_duration_ms": 3_600_000})
    w = REGISTRY["burn_rate"]()
    assert w.render(d, _wc("burn_rate")) == "$0.50/h"


def test_burn_rate_short_session_per_minute():
    d = StatusData(cost={"total_cost_usd": 0.01, "total_duration_ms": 300_000})
    w = REGISTRY["burn_rate"]()
    assert w.render(d, _wc("burn_rate")) == "$0.002/min"


def test_burn_rate_exactly_10_min_uses_per_hour():
    d = StatusData(cost={"total_cost_usd": 0.05, "total_duration_ms": 600_000})
    w = REGISTRY["burn_rate"]()
    assert w.render(d, _wc("burn_rate")) == "$0.30/h"


def test_burn_rate_zero_cost_returns_empty():
    d = StatusData(cost={"total_cost_usd": 0.0, "total_duration_ms": 60_000})
    w = REGISTRY["burn_rate"]()
    assert w.render(d, _wc("burn_rate")) == ""


def test_burn_rate_zero_duration_returns_empty():
    d = StatusData(cost={"total_cost_usd": 0.10, "total_duration_ms": 0})
    w = REGISTRY["burn_rate"]()
    assert w.render(d, _wc("burn_rate")) == ""


def test_burn_rate_missing_cost_returns_empty():
    w = REGISTRY["burn_rate"]()
    assert w.render(StatusData(), _wc("burn_rate")) == ""
