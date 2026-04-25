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
