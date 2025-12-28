"""MCP server exposing agent-mesh tools for stdio transport."""

import asyncio
import sys
from typing import Annotated, Literal

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
    timeout_s: Annotated[int, "Timeout in seconds (default 1800=30min for full agentic workflow with tool use)"] = 1800,
    model: Annotated[str | None, "Model ID (e.g., us.anthropic.claude-sonnet-4-5-20250929-v1:0)"] = None,
) -> str:
    """Run Claude Code CLI in headless mode. This executes a full agentic workflow (not a single LLM call), including tool use, retries, and I/O. Default 30min timeout. Uses Bedrock if CLAUDE_CODE_USE_BEDROCK=1."""
    from agent_mesh.runners.claude import run_claude

    result = await run_claude(prompt, cwd, timeout_s, auto_approve=True, model=model)
    return result.model_dump_json(indent=2)


@mcp.tool()
async def codex_exec(
    task: Annotated[str, "The task to execute"],
    cwd: Annotated[str, "Working directory"] = ".",
    timeout_s: Annotated[int, "Timeout in seconds (default 1800=30min for full agentic workflow with tool use)"] = 1800,
    reasoning_effort: Annotated[str, "Reasoning effort: none, low, medium, high, xhigh"] = "low",
) -> str:
    """Run Codex CLI (gpt-5.2) in headless mode. This executes a full agentic workflow (not a single LLM call), including tool use, retries, and I/O. Default 30min timeout. Use higher reasoning_effort for complex tasks."""
    from agent_mesh.runners.codex import run_codex

    result = await run_codex(
        task, cwd, timeout_s,
        json_events=True,
        reasoning_effort=reasoning_effort,  # type: ignore
    )
    return result.model_dump_json(indent=2)


@mcp.tool()
async def gemini_run(
    prompt: Annotated[str, "The prompt to send to Gemini"],
    cwd: Annotated[str, "Working directory"] = ".",
    timeout_s: Annotated[int, "Timeout in seconds (default 1800=30min for full agentic workflow with tool use)"] = 1800,
) -> str:
    """Run Gemini CLI in headless mode. This executes a full agentic workflow (not a single LLM call), including tool use, retries, and I/O. Default 30min timeout. Requires GEMINI_API_KEY."""
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
