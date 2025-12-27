"""Review pipeline: Claude implements → Codex reviews."""

import json


async def run_review_pipeline(prompt: str, cwd: str) -> str:
    """Run the review pipeline: Claude implements, Codex reviews."""
    from agent_mesh.runners.claude import run_claude
    from agent_mesh.runners.codex import run_codex
    from agent_mesh.workspace import capture_git_diff

    # Step 1: Claude implements
    claude_result = await run_claude(prompt, cwd)
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
