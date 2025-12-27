"""MCP server exposing agent-mesh tools for stdio transport."""

import asyncio
import sys
from typing import Annotated

from mcp.server.fastmcp import FastMCP

# Create MCP server
mcp = FastMCP(
    name="agent-mesh",
    instructions="Agent mesh for headless CLI coordination between Claude, Codex, and Gemini.",
)


@mcp.tool()
async def claude_run(
    prompt: Annotated[str, "The prompt to send to Claude"],
    cwd: Annotated[str, "Working directory"] = ".",
    timeout_s: Annotated[int, "Timeout in seconds"] = 120,
    auto_approve: Annotated[bool, "Auto-approve file writes"] = False,
) -> str:
    """Run Claude Code CLI in headless mode and return structured JSON result."""
    from agent_mesh.runners.claude import run_claude

    result = await run_claude(prompt, cwd, timeout_s, auto_approve)
    return result.model_dump_json(indent=2)


@mcp.tool()
async def codex_exec(
    task: Annotated[str, "The task to execute"],
    cwd: Annotated[str, "Working directory"] = ".",
    timeout_s: Annotated[int, "Timeout in seconds"] = 120,
    json_events: Annotated[bool, "Return JSONL events"] = True,
) -> str:
    """Run Codex CLI exec in headless mode and return structured JSON result."""
    from agent_mesh.runners.codex import run_codex

    result = await run_codex(task, cwd, timeout_s, json_events)
    return result.model_dump_json(indent=2)


@mcp.tool()
async def gemini_run(
    prompt: Annotated[str, "The prompt to send to Gemini"],
    cwd: Annotated[str, "Working directory"] = ".",
    timeout_s: Annotated[int, "Timeout in seconds"] = 120,
) -> str:
    """Run Gemini CLI in headless mode and return structured JSON result."""
    from agent_mesh.runners.gemini import run_gemini

    result = await run_gemini(prompt, cwd, timeout_s)
    return result.model_dump_json(indent=2)


def main():
    """Run the MCP server on stdio."""
    # Redirect logs to stderr to keep stdout clean for MCP protocol
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
