import pytest
from ccstatusline.data import StatusData


@pytest.fixture
def sample_data():
    return StatusData(
        model={"display_name": "claude-sonnet-4-5", "id": "claude-sonnet-4-5"},
        session_id="test-session",
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
