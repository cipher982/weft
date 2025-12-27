"""CLI for agent-mesh."""

from typing import Annotated

import typer

from agent_mesh import __version__

app = typer.Typer(
    name="agent-mesh",
    help="Headless agent mesh for Claude, Codex, and Gemini CLI cooperation.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Show version information."""
    typer.echo(f"agent-mesh {__version__}")


@app.command()
def run(
    agent: Annotated[str, typer.Option("--agent", "-a", help="Agent to run: claude, codex, or gemini")],
    prompt: Annotated[str, typer.Option("--prompt", "-p", help="Prompt to send to the agent")],
    cwd: Annotated[str, typer.Option("--cwd", "-C", help="Working directory")] = ".",
    timeout: Annotated[int, typer.Option("--timeout", "-t", help="Timeout in seconds")] = 120,
) -> None:
    """Run a single agent in headless mode."""
    import asyncio
    import json

    from agent_mesh.runners import run_agent

    result = asyncio.run(run_agent(agent, prompt, cwd, timeout))
    typer.echo(result.model_dump_json(indent=2))


@app.command()
def pipeline(
    name: Annotated[str, typer.Argument(help="Pipeline name: review")],
    prompt: Annotated[str, typer.Option("--prompt", "-p", help="Prompt for the pipeline")] = "",
    cwd: Annotated[str, typer.Option("--cwd", "-C", help="Working directory")] = ".",
) -> None:
    """Run a pipeline (e.g., review: Claude implements → Codex reviews)."""
    if name == "review":
        import asyncio

        from agent_mesh.pipelines.review import run_review_pipeline

        result = asyncio.run(run_review_pipeline(prompt, cwd))
        typer.echo(result)
    else:
        typer.echo(f"Unknown pipeline: {name}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
