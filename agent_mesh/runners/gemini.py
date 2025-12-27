"""Gemini CLI runner."""

import json

from agent_mesh.runners.base import run_subprocess
from agent_mesh.types import AgentResult, Usage


async def run_gemini(prompt: str, cwd: str, timeout_s: int = 120) -> AgentResult:
    """Run Gemini CLI in headless mode."""
    # Gemini CLI uses positional prompt and --output-format for JSON
    cmd = [
        "gemini",
        "--output-format",
        "json",
        prompt,
    ]

    exit_code, stdout, stderr, started_at, ended_at = await run_subprocess(
        cmd, cwd, timeout_s
    )

    duration_ms = int((ended_at - started_at).total_seconds() * 1000)

    # Gemini outputs JSON in headless mode
    structured: dict = {}
    usage = Usage()

    if exit_code == 0 and stdout.strip():
        try:
            data = json.loads(stdout)
            structured = data
            # Extract usage stats if present
            if "stats" in data:
                usage = Usage(
                    input_tokens=data["stats"].get("inputTokens"),
                    output_tokens=data["stats"].get("outputTokens"),
                )
        except json.JSONDecodeError:
            # Gemini might output plain text in some modes
            structured = {"response": stdout.strip()}

    return AgentResult(
        agent="gemini",
        cwd=cwd,
        ok=exit_code == 0,
        exit_code=exit_code,
        started_at=started_at,
        ended_at=ended_at,
        duration_ms=duration_ms,
        stdout=stdout,
        stderr=stderr,
        structured=structured,
        usage=usage,
    )
