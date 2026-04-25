import pytest
from ccstatusline.data import StatusData


def test_model_name_from_dict():
    d = StatusData(model={"display_name": "claude-sonnet-4-5", "id": "cs4"})
    assert d.model_name == "claude-sonnet-4-5"


def test_model_name_from_string():
    d = StatusData(model="claude-opus-4")
    assert d.model_name == "claude-opus-4"


def test_model_name_empty():
    d = StatusData()
    assert d.model_name == ""


def test_tokens_used_sums_input_output():
    d = StatusData(context_window={
        "total_input_tokens": 10000,
        "total_output_tokens": 2500,
    })
    assert d.tokens_used == 12500


def test_tokens_used_when_missing():
    d = StatusData()
    assert d.tokens_used == 0


def test_context_used_pct():
    d = StatusData(context_window={"used_percentage": 42.5})
    assert d.context_used_pct == 42.5


def test_context_used_pct_when_missing():
    d = StatusData()
    assert d.context_used_pct == 0.0


def test_cost_usd():
    d = StatusData(cost={"total_cost_usd": 0.1234})
    assert d.cost_usd == pytest.approx(0.1234)


def test_cost_usd_when_missing():
    d = StatusData()
    assert d.cost_usd == 0.0


def test_session_duration_ms():
    d = StatusData(cost={"total_duration_ms": 90000})
    assert d.session_duration_ms == 90000


def test_unknown_fields_allowed():
    d = StatusData(future_field="hello")
    assert d.future_field == "hello"
