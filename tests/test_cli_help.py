"""CLI smoke tests that don't make API calls."""

from typer.testing import CliRunner

from agent_mesh.cli import app


def test_doctor_help() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["doctor", "--help"])
    assert result.exit_code == 0


def test_smoke_help() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["smoke", "--help"])
    assert result.exit_code == 0

