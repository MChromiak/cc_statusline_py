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
