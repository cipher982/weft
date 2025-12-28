# weft

Tiny MCP tool server that exposes Claude Code, Codex CLI, and Gemini CLI as callable tools.

## Quickstart

```bash
uv sync
uv run agent-mesh doctor   # no LLM calls; checks MCP + binaries
uv run agent-mesh smoke    # real calls (costs money)
```

## What this repo is for

- Make the three CLIs usable headlessly (no interactive sessions).
- Provide an MCP server (`python -m agent_mesh.mcp_server`) that exposes:
  - `claude_run`
  - `codex_exec`
  - `gemini_run`

## Prereqs

Install the CLIs:

```bash
npm install -g @anthropic-ai/claude-code
npm install -g @openai/codex
npm install -g @google/gemini-cli
```

Auth/env:

- Claude: `claude auth` (browser OAuth)
- Codex: `OPENAI_API_KEY=...`
- Gemini: `GEMINI_API_KEY=...` (or whatever auth your installed `gemini` CLI is configured for)

## MCP Server

```bash
uv run python -m agent_mesh.mcp_server
```

## Register in each CLI

Codex:

```bash
codex mcp add agent-mesh -- uv run python -m agent_mesh.mcp_server
codex mcp list
```

Claude:

```bash
claude mcp add-json agent-mesh '{"type":"stdio","command":"uv","args":["run","python","-m","agent_mesh.mcp_server"]}'
claude mcp list
```

Gemini: configure an MCP stdio server entry pointing at `uv run python -m agent_mesh.mcp_server` (exact location/schema depends on your gemini-cli version).

## Notes

- `agent-mesh smoke` makes real model calls and costs money.
- `agent-mesh pipeline review` exists as an example/recipe, not the core product.

## Troubleshooting

### "Command not found"
Ensure CLIs are installed and in PATH:
```bash
which claude
which codex
which gemini
```

### "Authentication failed"
Run the appropriate auth command:
```bash
claude auth                          # OAuth browser flow
export OPENAI_API_KEY='your-key'    # For Codex
export GEMINI_API_KEY='your-key'    # For Gemini
```

### "MCP server not found"
After registering, restart the agent CLI to load the new MCP server configuration.

### Timeouts
Increase timeout for long-running tasks:
```bash
agent-mesh run --agent claude --prompt "Complex task" --timeout 300
```

## Contributing

See `docs/specs/agent-mesh.md` for the full specification and implementation phases.

## License

MIT
