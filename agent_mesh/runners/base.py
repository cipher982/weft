"""Base runner utilities and dispatcher."""

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from agent_mesh.types import AgentResult, Artifacts, Usage


async def run_subprocess(
    cmd: list[str],
    cwd: str,
    timeout_s: int,
    env: dict[str, str] | None = None,
) -> tuple[int, str, str, datetime, datetime]:
    """Run a subprocess with timeout and capture output.

    Always returns a tuple, even on errors (FileNotFoundError, permission errors, etc).
    """
    import os

    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    started_at = datetime.now(timezone.utc)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdin=asyncio.subprocess.DEVNULL,  # Close stdin to avoid MCP stdio conflicts
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=full_env,
        )
    except FileNotFoundError as e:
        ended_at = datetime.now(timezone.utc)
        return 127, "", f"Command not found: {cmd[0]} ({e})", started_at, ended_at
    except PermissionError as e:
        ended_at = datetime.now(timezone.utc)
        return 126, "", f"Permission denied: {e}", started_at, ended_at
    except NotADirectoryError as e:
        ended_at = datetime.now(timezone.utc)
        return 1, "", f"Invalid working directory: {cwd} ({e})", started_at, ended_at
    except Exception as e:
        ended_at = datetime.now(timezone.utc)
        return 1, "", f"Failed to start subprocess: {e}", started_at, ended_at

    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout_s,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        ended_at = datetime.now(timezone.utc)
        return -1, "", f"Timeout after {timeout_s}s", started_at, ended_at

    ended_at = datetime.now(timezone.utc)
    return (
        proc.returncode or 0,
        stdout_bytes.decode("utf-8", errors="replace"),
        stderr_bytes.decode("utf-8", errors="replace"),
        started_at,
        ended_at,
    )


async def run_agent(agent: str, prompt: str, cwd: str = ".", timeout_s: int = 120) -> AgentResult:
    """Dispatch to the appropriate agent runner."""
    # Resolve cwd to absolute path
    cwd = str(Path(cwd).resolve())

    if agent == "claude":
        from agent_mesh.runners.claude import run_claude
        return await run_claude(prompt, cwd, timeout_s)
    elif agent == "codex":
        from agent_mesh.runners.codex import run_codex
        return await run_codex(prompt, cwd, timeout_s)
    elif agent == "gemini":
        from agent_mesh.runners.gemini import run_gemini
        return await run_gemini(prompt, cwd, timeout_s)
    else:
        # Return error result for unknown agent
        now = datetime.now(timezone.utc)
        return AgentResult(
            agent="unknown",
            cwd=cwd,
            ok=False,
            exit_code=1,
            started_at=now,
            ended_at=now,
            duration_ms=0,
            stdout="",
            stderr=f"Unknown agent: {agent}. Must be claude, codex, or gemini.",
        )
