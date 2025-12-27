"""Tests for agent_mesh.types."""

import json
from datetime import datetime, timezone

import pytest

from agent_mesh.types import AgentResult, Artifacts, RunConfig, Usage


def test_agent_result_serialization():
    """Test that AgentResult serializes to JSON and back."""
    now = datetime.now(timezone.utc)
    result = AgentResult(
        agent="claude",
        cwd="/tmp/test",
        ok=True,
        exit_code=0,
        started_at=now,
        ended_at=now,
        duration_ms=1000,
        stdout="Hello world",
        stderr="",
        structured={"response": "test"},
        artifacts=Artifacts(files_written=["test.py"], git_diff="diff"),
        usage=Usage(input_tokens=100, output_tokens=50),
    )

    # Serialize to JSON
    json_str = result.model_dump_json()
    assert json_str

    # Parse back
    data = json.loads(json_str)
    assert data["agent"] == "claude"
    assert data["ok"] is True
    assert data["exit_code"] == 0
    assert data["duration_ms"] == 1000
    assert data["artifacts"]["files_written"] == ["test.py"]
    assert data["usage"]["input_tokens"] == 100


def test_agent_result_defaults():
    """Test AgentResult default values."""
    now = datetime.now(timezone.utc)
    result = AgentResult(
        agent="codex",
        cwd="/tmp",
        ok=False,
        exit_code=1,
        started_at=now,
        ended_at=now,
        duration_ms=0,
        stdout="",
        stderr="error",
    )

    assert result.mode == "headless"
    assert result.structured == {}
    assert result.artifacts.files_written == []
    assert result.artifacts.git_diff is None
    assert result.usage.input_tokens is None


def test_run_config_defaults():
    """Test RunConfig default values."""
    config = RunConfig(prompt="test")
    assert config.cwd == "."
    assert config.timeout_s == 120
    assert config.output_format == "json"
    assert config.env == {}


def test_run_config_validation():
    """Test RunConfig validation."""
    # Valid config
    config = RunConfig(prompt="test", timeout_s=60)
    assert config.timeout_s == 60

    # Invalid timeout (too low)
    with pytest.raises(ValueError):
        RunConfig(prompt="test", timeout_s=0)

    # Invalid timeout (too high)
    with pytest.raises(ValueError):
        RunConfig(prompt="test", timeout_s=10000)


def test_usage_model():
    """Test Usage model."""
    usage = Usage()
    assert usage.input_tokens is None
    assert usage.output_tokens is None
    assert usage.cached_input_tokens is None

    usage = Usage(input_tokens=100, output_tokens=50, cached_input_tokens=25)
    assert usage.input_tokens == 100
    assert usage.output_tokens == 50
    assert usage.cached_input_tokens == 25


def test_artifacts_model():
    """Test Artifacts model."""
    artifacts = Artifacts()
    assert artifacts.files_written == []
    assert artifacts.git_diff is None

    artifacts = Artifacts(files_written=["a.py", "b.py"], git_diff="diff here")
    assert len(artifacts.files_written) == 2
    assert artifacts.git_diff == "diff here"
