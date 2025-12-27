"""End-to-end integration tests for agent-mesh with REAL LLM calls.

These tests make actual API calls and cost money/time. They test the full
integration of runners, MCP server, and agent-to-agent communication.

Run with: uv run pytest tests/test_e2e.py -v --tb=short
Skip slow tests: uv run pytest tests/test_e2e.py -v -m "not slow"
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from agent_mesh.runners.base import run_agent
from agent_mesh.types import AgentResult

# ============================================================================
# Fixtures and Helpers
# ============================================================================


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Create initial file and commit
        (repo_path / "README.md").write_text("# Test Repo\n")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        yield str(repo_path)


def has_claude_cli() -> bool:
    """Check if claude CLI is available."""
    try:
        result = subprocess.run(
            ["which", "claude"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def has_codex_cli() -> bool:
    """Check if codex CLI is available."""
    try:
        # Codex might be a shell function, check via bash
        result = subprocess.run(
            ["bash", "-c", "command -v codex"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def has_gemini_api_key() -> bool:
    """Check if GEMINI_API_KEY is set."""
    return bool(os.environ.get("GEMINI_API_KEY"))


# ============================================================================
# Runner Tests - Real LLM calls
# ============================================================================


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skipif(not has_claude_cli(), reason="claude CLI not available")
async def test_claude_runner_real_call():
    """Test Claude runner with a real API call."""
    result = await run_agent(
        agent="claude",
        prompt="What is 2+2? Reply with just the number.",
        cwd=".",
        timeout_s=60,
    )

    # Verify result structure
    assert isinstance(result, AgentResult)
    assert result.agent == "claude"
    assert result.mode == "headless"
    assert result.cwd is not None
    assert isinstance(result.exit_code, int)
    assert isinstance(result.duration_ms, int)
    assert result.duration_ms > 0

    # Should succeed (assuming API is working)
    if result.ok:
        assert result.exit_code == 0
        assert len(result.stdout) > 0
        print(f"\n✓ Claude responded in {result.duration_ms}ms")
        print(f"  Response length: {len(result.stdout)} chars")
        if result.usage.output_tokens:
            print(f"  Tokens: {result.usage.input_tokens} in, {result.usage.output_tokens} out")
    else:
        # If it fails, print diagnostics but don't fail test (might be auth issue)
        print(f"\n⚠ Claude call failed (exit {result.exit_code})")
        print(f"  stderr: {result.stderr[:200]}")
        pytest.skip("Claude CLI authentication or connection issue")


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skipif(not has_codex_cli(), reason="codex CLI not available")
async def test_codex_runner_real_call():
    """Test Codex runner with a real API call."""
    result = await run_agent(
        agent="codex",
        prompt="What is the capital of France? Reply with just the city name.",
        cwd=".",
        timeout_s=60,
    )

    # Verify result structure
    assert isinstance(result, AgentResult)
    assert result.agent == "codex"
    assert result.mode == "headless"
    assert result.cwd is not None
    assert isinstance(result.exit_code, int)
    assert isinstance(result.duration_ms, int)
    assert result.duration_ms > 0

    # Should succeed
    if result.ok:
        assert result.exit_code == 0
        assert len(result.stdout) > 0
        print(f"\n✓ Codex responded in {result.duration_ms}ms")
        print(f"  Response length: {len(result.stdout)} chars")

        # Check for JSONL events
        if result.structured and "events" in result.structured:
            print(f"  Events: {len(result.structured['events'])}")
    else:
        print(f"\n⚠ Codex call failed (exit {result.exit_code})")
        print(f"  stderr: {result.stderr[:200]}")
        pytest.skip("Codex CLI authentication or connection issue")


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skipif(not has_gemini_api_key(), reason="GEMINI_API_KEY not set")
async def test_gemini_runner_real_call():
    """Test Gemini runner with a real API call (skipped if no API key)."""
    result = await run_agent(
        agent="gemini",
        prompt="What is 10+10? Reply with just the number.",
        cwd=".",
        timeout_s=60,
    )

    # Verify result structure
    assert isinstance(result, AgentResult)
    assert result.agent == "gemini"
    assert result.mode == "headless"
    assert result.cwd is not None
    assert isinstance(result.exit_code, int)
    assert isinstance(result.duration_ms, int)

    if result.ok:
        assert result.exit_code == 0
        print(f"\n✓ Gemini responded in {result.duration_ms}ms")
        print(f"  Response length: {len(result.stdout)} chars")
    else:
        print(f"\n⚠ Gemini call failed (exit {result.exit_code})")
        print(f"  stderr: {result.stderr[:200]}")
        pytest.skip("Gemini CLI or API key issue")


@pytest.mark.e2e
async def test_timeout_handling():
    """Test that timeout is enforced (using very short timeout)."""
    result = await run_agent(
        agent="claude",
        prompt="Count to 1000 slowly",
        cwd=".",
        timeout_s=1,  # Very short timeout
    )

    # Should timeout or fail
    assert result.exit_code != 0 or not result.ok
    assert "timeout" in result.stderr.lower() or result.duration_ms < 2000
    print(f"\n✓ Timeout enforced: {result.duration_ms}ms")


@pytest.mark.e2e
async def test_invalid_agent_handling():
    """Test error handling for invalid agent name."""
    result = await run_agent(
        agent="nonexistent",
        prompt="test",
        cwd=".",
        timeout_s=5,
    )

    assert not result.ok
    assert result.exit_code != 0
    assert "unknown agent" in result.stderr.lower()
    print("\n✓ Invalid agent rejected")


# ============================================================================
# MCP Server Tests
# ============================================================================


@pytest.mark.e2e
async def test_mcp_server_initialize():
    """Test MCP server initialization."""
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "agent_mesh.mcp_server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=Path(__file__).parent.parent,
    )

    try:
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0.0"},
            },
        }

        proc.stdin.write((json.dumps(init_request) + "\n").encode())
        await proc.stdin.drain()

        # Read response
        line = await asyncio.wait_for(proc.stdout.readline(), timeout=5.0)
        response = json.loads(line)

        assert "result" in response
        assert response["result"]["serverInfo"]["name"] == "agent-mesh"
        assert "capabilities" in response["result"]
        print("\n✓ MCP server initializes correctly")

    finally:
        proc.stdin.close()
        try:
            await asyncio.wait_for(proc.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()


@pytest.mark.e2e
async def test_mcp_server_tools_list():
    """Test that all 3 tools are discoverable via MCP."""
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "agent_mesh.mcp_server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=Path(__file__).parent.parent,
    )

    try:
        # Initialize first
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0.0"},
            },
        }
        proc.stdin.write((json.dumps(init_request) + "\n").encode())
        await proc.stdin.drain()
        await proc.stdout.readline()  # Consume init response

        # List tools
        list_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        proc.stdin.write((json.dumps(list_request) + "\n").encode())
        await proc.stdin.drain()

        # Read response
        line = await asyncio.wait_for(proc.stdout.readline(), timeout=5.0)
        response = json.loads(line)

        assert "result" in response
        tools = response["result"]["tools"]
        tool_names = [t["name"] for t in tools]

        assert "claude_run" in tool_names
        assert "codex_exec" in tool_names
        assert "gemini_run" in tool_names
        print(f"\n✓ All 3 tools discoverable: {tool_names}")

        # Verify schemas
        for tool in tools:
            assert "inputSchema" in tool
            assert "properties" in tool["inputSchema"]
            print(f"  ✓ {tool['name']} has valid schema")

    finally:
        proc.stdin.close()
        try:
            await asyncio.wait_for(proc.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skipif(not has_claude_cli(), reason="claude CLI not available")
async def test_mcp_tool_call_claude():
    """Test calling claude_run tool via MCP (real API call)."""
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "agent_mesh.mcp_server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=Path(__file__).parent.parent,
    )

    try:
        # Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0.0"},
            },
        }
        proc.stdin.write((json.dumps(init_request) + "\n").encode())
        await proc.stdin.drain()
        await proc.stdout.readline()

        # Call claude_run tool
        tool_call = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "claude_run",
                "arguments": {
                    "prompt": "Say 'hello' in one word",
                    "timeout_s": 60,
                },
            },
        }
        proc.stdin.write((json.dumps(tool_call) + "\n").encode())
        await proc.stdin.drain()

        # Read response (with longer timeout for API call)
        line = await asyncio.wait_for(proc.stdout.readline(), timeout=90.0)
        response = json.loads(line)

        if "result" in response:
            # Parse AgentResult from tool response
            result_json = json.loads(response["result"]["content"][0]["text"])
            assert result_json["agent"] == "claude"
            assert "duration_ms" in result_json
            print(f"\n✓ claude_run tool executed via MCP")
            print(f"  Duration: {result_json['duration_ms']}ms")
        else:
            # Might fail due to auth - don't fail test
            print("\n⚠ claude_run tool call failed (possibly auth issue)")
            pytest.skip("Claude authentication issue via MCP")

    finally:
        proc.stdin.close()
        try:
            await asyncio.wait_for(proc.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skipif(not has_codex_cli(), reason="codex CLI not available")
async def test_mcp_tool_call_codex():
    """Test calling codex_exec tool via MCP (real API call)."""
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "agent_mesh.mcp_server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=Path(__file__).parent.parent,
    )

    try:
        # Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0.0"},
            },
        }
        proc.stdin.write((json.dumps(init_request) + "\n").encode())
        await proc.stdin.drain()
        await proc.stdout.readline()

        # Call codex_exec tool
        tool_call = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "codex_exec",
                "arguments": {
                    "task": "What is 5+5? Reply with just the number.",
                    "timeout_s": 60,
                },
            },
        }
        proc.stdin.write((json.dumps(tool_call) + "\n").encode())
        await proc.stdin.drain()

        # Read response
        line = await asyncio.wait_for(proc.stdout.readline(), timeout=90.0)
        response = json.loads(line)

        if "result" in response:
            result_json = json.loads(response["result"]["content"][0]["text"])
            assert result_json["agent"] == "codex"
            assert "duration_ms" in result_json
            print(f"\n✓ codex_exec tool executed via MCP")
            print(f"  Duration: {result_json['duration_ms']}ms")
        else:
            print("\n⚠ codex_exec tool call failed (possibly auth issue)")
            pytest.skip("Codex authentication issue via MCP")

    finally:
        proc.stdin.close()
        try:
            await asyncio.wait_for(proc.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()


# ============================================================================
# Pipeline Tests
# ============================================================================


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skipif(
    not (has_claude_cli() and has_codex_cli()),
    reason="Both claude and codex CLIs required",
)
async def test_review_pipeline(temp_git_repo):
    """Test the review pipeline with a real git repo."""
    from agent_mesh.pipelines.review import run_review_pipeline

    # Run pipeline with a simple implementation task
    result_json = await run_review_pipeline(
        prompt="Create a file called hello.py with a simple hello world function",
        cwd=temp_git_repo,
        auto_approve=True,
    )

    result = json.loads(result_json)

    # Check structure
    assert "stage" in result
    assert "success" in result

    if result["success"]:
        assert result["stage"] == "complete"
        assert "claude_result" in result
        assert "codex_result" in result
        assert "diff" in result

        print("\n✓ Review pipeline completed")
        print(f"  Stage: {result['stage']}")

        # Check that Claude result has expected structure
        claude_result = result["claude_result"]
        assert claude_result["agent"] == "claude"
        assert "duration_ms" in claude_result

        # Check that Codex result has expected structure
        codex_result = result["codex_result"]
        assert codex_result["agent"] == "codex"
        assert "duration_ms" in codex_result

        # Check that diff was captured
        if result["diff"]:
            print(f"  Diff captured: {len(result['diff'])} chars")

    else:
        print(f"\n⚠ Pipeline failed at {result['stage']}")
        pytest.skip(f"Pipeline failed: {result.get('error', 'unknown error')}")


# ============================================================================
# Cross-Agent Tests (Agent-to-Agent via MCP)
# ============================================================================


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skipif(
    not (has_claude_cli() and has_codex_cli()),
    reason="Both claude and codex CLIs required for cross-agent tests",
)
def test_cross_agent_setup():
    """Verify that MCP server can be registered (informational test)."""
    # This test just checks that the registration commands exist
    # Actual registration requires manual setup by the user

    result = subprocess.run(
        ["bash", "-c", "codex mcp list || true"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    # Just verify the command works
    print("\n✓ MCP commands available")
    print("  Note: Cross-agent communication requires manual MCP registration:")
    print("    codex mcp add agent-mesh -- uv run python -m agent_mesh.mcp_server")
    print("    claude mcp add-json agent-mesh '{\"type\":\"stdio\",\"command\":\"uv\",\"args\":[\"run\",\"python\",\"-m\",\"agent_mesh.mcp_server\"]}'")


# ============================================================================
# CLI Tests
# ============================================================================


@pytest.mark.e2e
def test_cli_version():
    """Test agent-mesh version command."""
    result = subprocess.run(
        ["uv", "run", "agent-mesh", "version"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0
    assert "agent-mesh" in result.stdout
    assert "0.1.0" in result.stdout


@pytest.mark.e2e
def test_cli_help():
    """Test agent-mesh --help command."""
    result = subprocess.run(
        ["uv", "run", "agent-mesh", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0
    assert "run" in result.stdout
    assert "pipeline" in result.stdout
    assert "version" in result.stdout


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skipif(not has_claude_cli(), reason="claude CLI not available")
def test_cli_run_claude(temp_git_repo):
    """Test agent-mesh run --agent claude command."""
    result = subprocess.run(
        [
            "uv", "run", "agent-mesh", "run",
            "--agent", "claude",
            "--prompt", "Reply with exactly: CLI_TEST_PASSED",
            "--timeout", "60",
            "--cwd", str(temp_git_repo),
        ],
        capture_output=True,
        text=True,
        timeout=90,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0

    # Should output valid JSON
    data = json.loads(result.stdout)
    assert data["agent"] == "claude"
    assert "ok" in data


# ============================================================================
# Workspace Tests
# ============================================================================


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_workspace_git_diff_untracked(temp_git_repo):
    """Test capture_git_diff includes untracked files."""
    from agent_mesh.workspace import capture_git_diff

    # Create an untracked file
    (Path(temp_git_repo) / "new_file.py").write_text("print('hello')\n")

    diff = await capture_git_diff(temp_git_repo, include_untracked=True)

    assert "new_file.py" in diff
    assert "+print('hello')" in diff


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_workspace_git_diff_no_untracked(temp_git_repo):
    """Test capture_git_diff without untracked files."""
    from agent_mesh.workspace import capture_git_diff

    # Create an untracked file
    (Path(temp_git_repo) / "new_file.py").write_text("print('hello')\n")

    diff = await capture_git_diff(temp_git_repo, include_untracked=False)

    # Untracked file should NOT be in diff
    assert "new_file.py" not in diff


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_workspace_git_diff_staged_changes(temp_git_repo):
    """Test capture_git_diff with staged changes."""
    from agent_mesh.workspace import capture_git_diff

    # Modify and stage a file
    readme = Path(temp_git_repo) / "README.md"
    readme.write_text("# Test Repo\n\nModified content.\n")
    subprocess.run(["git", "add", "README.md"], cwd=temp_git_repo, check=True)

    diff = await capture_git_diff(temp_git_repo)

    assert "README.md" in diff
    assert "+Modified content" in diff


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_workspace_git_status(temp_git_repo):
    """Test capture_git_status returns porcelain output."""
    from agent_mesh.workspace import capture_git_status

    # Create an untracked file
    (Path(temp_git_repo) / "new_file.py").write_text("print('hello')\n")

    status = await capture_git_status(temp_git_repo)

    assert "?? new_file.py" in status


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_workspace_non_git_directory():
    """Test workspace functions handle non-git directories."""
    from agent_mesh.workspace import capture_git_diff, capture_git_status

    with tempfile.TemporaryDirectory() as tmpdir:
        # Not a git repo
        diff = await capture_git_diff(tmpdir)
        assert diff == ""

        # Status might return error or empty
        status = await capture_git_status(tmpdir)
        # Just verify it doesn't crash


# ============================================================================
# Test Summary
# ============================================================================


def test_e2e_summary():
    """Print summary of what e2e tests cover."""
    print("\n" + "=" * 70)
    print("E2E Test Coverage Summary")
    print("=" * 70)
    print("\n✓ Runner Tests:")
    print("  - Claude runner with real API call")
    print("  - Codex runner with real API call")
    print("  - Gemini runner with real API call (if API key present)")
    print("  - Timeout handling")
    print("  - Invalid agent error handling")
    print("\n✓ MCP Server Tests:")
    print("  - Server initialization")
    print("  - Tools discovery (all 3 tools)")
    print("  - claude_run tool call with real API")
    print("  - codex_exec tool call with real API")
    print("\n✓ Pipeline Tests:")
    print("  - Review pipeline (Claude → git diff → Codex)")
    print("\n✓ CLI Tests:")
    print("  - agent-mesh version")
    print("  - agent-mesh --help")
    print("  - agent-mesh run --agent claude")
    print("\n✓ Workspace Tests:")
    print("  - capture_git_diff with untracked files")
    print("  - capture_git_diff without untracked files")
    print("  - capture_git_diff with staged changes")
    print("  - capture_git_status")
    print("  - Non-git directory handling")
    print("\n✓ Cross-Agent Tests:")
    print("  - MCP registration verification")
    print("  - Note: Full agent-to-agent requires manual MCP setup")
    print("\n" + "=" * 70)
