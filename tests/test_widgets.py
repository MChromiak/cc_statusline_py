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
