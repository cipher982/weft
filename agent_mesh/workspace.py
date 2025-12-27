"""Workspace utilities for git operations."""

import asyncio
from pathlib import Path


async def capture_git_diff(cwd: str) -> str:
    """Capture git diff (staged + unstaged) in the working directory."""
    cwd_path = Path(cwd).resolve()

    # Check if it's a git repo
    git_dir = cwd_path / ".git"
    if not git_dir.exists():
        return ""

    # Get combined diff (unstaged + staged)
    proc = await asyncio.create_subprocess_exec(
        "git", "diff", "HEAD",
        cwd=str(cwd_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    diff = stdout.decode("utf-8", errors="replace")

    # If no diff against HEAD, try just `git diff`
    if not diff.strip():
        proc = await asyncio.create_subprocess_exec(
            "git", "diff",
            cwd=str(cwd_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        diff = stdout.decode("utf-8", errors="replace")

    return diff


async def capture_git_status(cwd: str) -> str:
    """Capture git status in porcelain format."""
    cwd_path = Path(cwd).resolve()

    proc = await asyncio.create_subprocess_exec(
        "git", "status", "--porcelain",
        cwd=str(cwd_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    return stdout.decode("utf-8", errors="replace")
