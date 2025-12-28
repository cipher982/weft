"""Codex CLI runner."""

import json
import os
from typing import Literal

from agent_mesh.runners.base import run_subprocess
from agent_mesh.types import AgentResult, Usage

ReasoningEffort = Literal["none", "low", "medium", "high", "xhigh"]


async def run_codex(
    task: str,
    cwd: str,
    timeout_s: int = 120,
    json_events: bool = True,
    model: str = "gpt-5.2",
    reasoning_effort: ReasoningEffort = "low",
    web_search: bool = True,
) -> AgentResult:
    """Run Codex CLI exec in headless mode.

    Args:
        task: The task to execute
        cwd: Working directory
        timeout_s: Timeout in seconds
        json_events: If True, output JSONL events
        model: Model to use (default: gpt-5.2)
        reasoning_effort: Reasoning effort level (none/low/medium/high/xhigh)
        web_search: Enable web search capability

    Environment variables respected:
        OPENAI_API_KEY: Required for Codex API access
    """
    cmd = [
        "codex",
        "-m", model,
        "-c", f"model_reasoning_effort={reasoning_effort}",
        "--dangerously-bypass-approvals-and-sandbox",
    ]

    if web_search:
        cmd.extend(["--enable", "web_search_request"])

    cmd.append("exec")

    if json_events:
        cmd.append("--json")

    cmd.append(task)

    exit_code, stdout, stderr, started_at, ended_at = await run_subprocess(
        cmd, cwd, timeout_s
    )

    duration_ms = int((ended_at - started_at).total_seconds() * 1000)

    # Parse JSONL events if json mode
    structured: dict = {}
    events: list = []

    if json_events and stdout.strip():
        for line in stdout.strip().split("\n"):
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        structured = {"events": events}

        # Extract final message if present
        for event in reversed(events):
            if event.get("type") == "message" and event.get("message"):
                structured["response"] = event["message"]
                break

    return AgentResult(
        agent="codex",
        cwd=cwd,
        ok=exit_code == 0,
        exit_code=exit_code,
        started_at=started_at,
        ended_at=ended_at,
        duration_ms=duration_ms,
        stdout=stdout,
        stderr=stderr,
        structured=structured,
    )
