import json
import tomllib
from pathlib import Path
from unittest.mock import patch

import pytest
from ccstatusline.config import LEGACY_JSON_PATH, LEGACY_TOML_PATH, TOML_PATH, Config, LineConfig, PowerlineConfig, _migrate_from_json
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


def test_config_save_and_load(tmp_path):
    toml_file = tmp_path / "settings.toml"
    wc = WidgetConfig(type="model", fg="#a6e3a1", bg="#1e1e2e", bold=True)
    original = Config(
        color_level="256",
        lines=[LineConfig(widgets=[wc])],
    )

    with patch("ccstatusline.config.TOML_PATH", toml_file):
        original.save()
        loaded = Config.load()

    assert loaded.color_level == "256"
    assert loaded.lines[0].widgets[0].type == "model"
    assert loaded.lines[0].widgets[0].fg == "#a6e3a1"
    assert loaded.lines[0].widgets[0].bold is True


def test_config_save_writes_valid_toml(tmp_path):
    toml_file = tmp_path / "settings.toml"
    c = Config(color_level="basic")
    with patch("ccstatusline.config.TOML_PATH", toml_file):
        c.save()
    data = tomllib.loads(toml_file.read_text())
    assert data["color_level"] == "basic"


def test_config_load_returns_default_when_no_file(tmp_path):
    missing = tmp_path / "nonexistent.toml"
    missing_legacy_toml = tmp_path / "nonexistent_legacy.toml"
    missing_json = tmp_path / "nonexistent.json"
    with patch("ccstatusline.config.TOML_PATH", missing), \
         patch("ccstatusline.config.LEGACY_TOML_PATH", missing_legacy_toml), \
         patch("ccstatusline.config.LEGACY_JSON_PATH", missing_json):
        c = Config.load()
    assert c.color_level == "truecolor"
    assert c.lines == []


def test_config_load_migrates_legacy_underscore_toml(tmp_path):
    import tomli_w

    new_path = tmp_path / "new" / "settings.toml"
    legacy_path = tmp_path / "legacy" / "settings.toml"
    missing_json = tmp_path / "nonexistent.json"

    legacy_path.parent.mkdir(parents=True)
    legacy = Config(color_level="basic", lines=[LineConfig(widgets=[WidgetConfig(type="model")])])
    legacy_path.write_bytes(tomli_w.dumps(legacy.model_dump()).encode())

    with patch("ccstatusline.config.TOML_PATH", new_path), \
         patch("ccstatusline.config.LEGACY_TOML_PATH", legacy_path), \
         patch("ccstatusline.config.LEGACY_JSON_PATH", missing_json):
        loaded = Config.load()

    assert loaded.color_level == "basic"
    assert loaded.lines[0].widgets[0].type == "model"
    assert new_path.exists(), "migration should write the config to the new path"


def test_migrate_from_json(tmp_path):
    json_data = {
        "colorLevel": 2,
        "minimalistMode": False,
        "powerline": {
            "enabled": True,
            "separator": "",
            "thinSeparator": "",
            "leftCap": "",
            "rightCap": "",
        },
        "lines": [
            [
                {"type": "Model", "styling": {"fg": "#a6e3a1", "bg": "#1e1e2e", "bold": True}},
                {"type": "GitBranch", "styling": {"fg": "#cba6f7", "bg": "#1e1e2e"}},
            ]
        ],
    }
    json_file = tmp_path / "settings.json"
    json_file.write_text(json.dumps(json_data))
    result = _migrate_from_json(json_file)

    assert result.color_level == "256"
    assert result.powerline.enabled is True
    assert len(result.lines) == 1
    assert result.lines[0].widgets[0].type == "model"
    assert result.lines[0].widgets[0].fg == "#a6e3a1"
    assert result.lines[0].widgets[0].bold is True
    assert result.lines[0].widgets[1].type == "git_branch"


def test_migrate_skips_unknown_widget(tmp_path, capsys):
    json_data = {
        "colorLevel": 3,
        "lines": [[{"type": "UnknownWidget123", "styling": {}}]],
    }
    json_file = tmp_path / "settings.json"
    json_file.write_text(json.dumps(json_data))
    result = _migrate_from_json(json_file)
    assert result.lines[0].widgets == []
    captured = capsys.readouterr()
    assert "UnknownWidget123" in captured.err


def test_migrate_burn_rate_widget(tmp_path):
    json_data = {
        "colorLevel": 3,
        "lines": [[{"type": "BurnRate", "styling": {"fg": "#fff", "bg": "#000"}}]],
    }
    json_file = tmp_path / "settings.json"
    json_file.write_text(json.dumps(json_data))
    result = _migrate_from_json(json_file)

    assert result.lines[0].widgets[0].type == "burn_rate"
