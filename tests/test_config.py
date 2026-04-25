import pytest
from ccstatusline.config import Config, LineConfig, PowerlineConfig
from ccstatusline.widgets.base import WidgetConfig


def test_powerline_config_defaults():
    pl = PowerlineConfig()
    assert pl.enabled is True
    assert pl.separator == ""
    assert pl.thin_separator == ""
    assert pl.left_cap == ""
    assert pl.right_cap == ""


def test_config_defaults():
    c = Config()
    assert c.color_level == "truecolor"
    assert c.minimalist_mode is False
    assert c.lines == []


def test_config_with_widgets():
    wc = WidgetConfig(type="model", fg="#ff0000", bg="#000000")
    line = LineConfig(widgets=[wc])
    c = Config(lines=[line])
    assert len(c.lines) == 1
    assert c.lines[0].widgets[0].type == "model"
    assert c.lines[0].widgets[0].fg == "#ff0000"


def test_config_color_level_valid():
    for level in ("none", "basic", "256", "truecolor"):
        c = Config(color_level=level)
        assert c.color_level == level


def test_config_color_level_invalid():
    with pytest.raises(Exception):
        Config(color_level="fancy")
