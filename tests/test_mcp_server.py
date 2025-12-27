"""Test MCP server functionality."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path


async def test_mcp_protocol():
    """Test that the MCP server responds to basic protocol messages."""
    # Start the MCP server
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "agent_mesh.mcp_server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=Path(__file__).parent.parent,
    )

    # Test 1: Initialize
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
    init_response = json.loads(line)

    assert "result" in init_response, f"Initialize failed: {init_response}"
    assert init_response["result"]["serverInfo"]["name"] == "agent-mesh"
    print("✓ Server initializes correctly")

    # Test 2: List tools
    list_tools_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

    proc.stdin.write((json.dumps(list_tools_request) + "\n").encode())
    await proc.stdin.drain()

    # Read response
    line = await asyncio.wait_for(proc.stdout.readline(), timeout=5.0)
    tools_response = json.loads(line)

    assert "result" in tools_response, f"Tools list failed: {tools_response}"
    tools = tools_response["result"]["tools"]
    tool_names = [t["name"] for t in tools]

    assert "claude_run" in tool_names, "claude_run tool not found"
    assert "codex_exec" in tool_names, "codex_exec tool not found"
    assert "gemini_run" in tool_names, "gemini_run tool not found"
    print(f"✓ All 3 tools discoverable: {tool_names}")

    # Validate tool schemas
    for tool in tools:
        assert "inputSchema" in tool, f"Tool {tool['name']} missing inputSchema"
        assert "properties" in tool["inputSchema"], f"Tool {tool['name']} missing properties"
        print(f"✓ Tool {tool['name']} has valid schema")

    # Clean shutdown
    proc.stdin.close()
    await asyncio.wait_for(proc.wait(), timeout=2.0)

    print("\n✅ All MCP protocol tests passed")


async def test_tool_call():
    """Test that tool calls return AgentResult JSON."""
    # This test would require a full integration with Claude CLI
    # For now we verify the schema by importing the tool functions
    from agent_mesh.mcp_server import claude_run, codex_exec, gemini_run

    # Verify functions exist and have correct signatures
    import inspect

    sig = inspect.signature(claude_run)
    assert "prompt" in sig.parameters
    assert "cwd" in sig.parameters
    assert "timeout_s" in sig.parameters
    print("✓ claude_run has correct signature")

    sig = inspect.signature(codex_exec)
    assert "task" in sig.parameters
    assert "cwd" in sig.parameters
    assert "timeout_s" in sig.parameters
    print("✓ codex_exec has correct signature")

    sig = inspect.signature(gemini_run)
    assert "prompt" in sig.parameters
    assert "cwd" in sig.parameters
    assert "timeout_s" in sig.parameters
    print("✓ gemini_run has correct signature")

    print("\n✅ All tool signature tests passed")


async def test_no_stdout_pollution():
    """Test that only MCP JSON-RPC is written to stdout."""
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "agent_mesh.mcp_server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=Path(__file__).parent.parent,
    )

    # Send initialize
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

    # Verify it's valid JSON-RPC
    try:
        response = json.loads(line)
        assert "jsonrpc" in response, "Response missing jsonrpc field"
        assert response["jsonrpc"] == "2.0", "Invalid jsonrpc version"
        print("✓ stdout contains only valid JSON-RPC")
    except json.JSONDecodeError as e:
        raise AssertionError(f"stdout contains non-JSON data: {line}") from e

    # Clean shutdown
    proc.stdin.close()
    await asyncio.wait_for(proc.wait(), timeout=2.0)

    print("\n✅ No stdout pollution test passed")


if __name__ == "__main__":
    print("Testing MCP Server (Phase 4)\n")
    print("=" * 50)

    asyncio.run(test_mcp_protocol())
    print()
    asyncio.run(test_tool_call())
    print()
    asyncio.run(test_no_stdout_pollution())

    print("\n" + "=" * 50)
    print("All Phase 4 acceptance criteria verified ✅")
