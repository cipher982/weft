"""Review pipeline: Claude implements → Codex reviews."""

import json


async def run_review_pipeline(prompt: str, cwd: str, auto_approve: bool = True) -> str:
    """Run the review pipeline: Claude implements, Codex reviews.

    Args:
        prompt: What to implement
        cwd: Working directory (should be a git repo)
        auto_approve: If True, auto-approve Claude's file writes (default True for pipeline)
    """
    from agent_mesh.runners.claude import run_claude
    from agent_mesh.runners.codex import run_codex
    from agent_mesh.workspace import capture_git_diff

    # Step 1: Claude implements (auto-approve enabled for pipeline use)
    claude_result = await run_claude(prompt, cwd, auto_approve=auto_approve)
    if not claude_result.ok:
        return json.dumps({
            "stage": "implementation",
            "success": False,
            "error": claude_result.stderr,
            "claude_result": claude_result.model_dump(mode="json"),
        }, indent=2)

    # Step 2: Capture git diff
    diff = await capture_git_diff(cwd)

    # Step 3: Codex reviews
    review_prompt = f"""Review the following code changes and provide feedback:

```diff
{diff}
```

Provide your review as JSON with fields:
- issues: list of {{description, severity, file, line}}
- summary: brief overall assessment
- approved: boolean
"""
    codex_result = await run_codex(review_prompt, cwd)

    return json.dumps({
        "stage": "complete",
        "success": True,
        "diff": diff,
        "claude_result": claude_result.model_dump(mode="json"),
        "codex_result": codex_result.model_dump(mode="json"),
    }, indent=2)
