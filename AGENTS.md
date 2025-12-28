# weft

Tiny MCP tool server that exposes Claude/Codex/Gemini CLIs as callable tools.

## Purpose

- Make `claude`, `codex`, and `gemini` usable headlessly and composable via MCP.
- Keep the tool surface stable: `claude_run`, `codex_exec`, `gemini_run`.

## Commands

```bash
uv sync
uv run agent-mesh doctor         # no LLM calls; checks MCP + binaries
uv run agent-mesh smoke          # makes real calls (costs money)
uv run python -m agent_mesh.mcp_server
```

## Design Notes

- `agent_mesh/mcp_server.py` must keep stdout MCP-clean (log only to stderr).
- Prefer small, “boring” wrappers over orchestration features.
- Pipelines are optional examples; avoid expanding them unless a real workflow repeats.
