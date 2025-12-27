"""Claude Code CLI runner."""

import json
from datetime import timezone

from agent_mesh.runners.base import run_subprocess
from agent_mesh.types import AgentResult, Artifacts, Usage


async def run_claude(prompt: str, cwd: str, timeout_s: int = 120) -> AgentResult:
    """Run Claude Code CLI in print mode with JSON output."""
    cmd = [
        "claude",
        "-p",
        prompt,
        "--output-format",
        "json",
    ]

    exit_code, stdout, stderr, started_at, ended_at = await run_subprocess(
        cmd, cwd, timeout_s
    )

    duration_ms = int((ended_at - started_at).total_seconds() * 1000)

    # Parse structured output if possible
    structured: dict = {}
    usage = Usage()

    if exit_code == 0 and stdout.strip():
        try:
            data = json.loads(stdout)
            structured = data
            # Extract usage if present
            if "usage" in data:
                usage = Usage(
                    input_tokens=data["usage"].get("input_tokens"),
                    output_tokens=data["usage"].get("output_tokens"),
                    cached_input_tokens=data["usage"].get("cache_read_input_tokens"),
                )
        except json.JSONDecodeError:
            structured = {"raw_output": stdout}

    return AgentResult(
        agent="claude",
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
