# Agent Mesh

Headless agent coordination for Claude Code, Codex, and Gemini CLI.

## Installation

```bash
uv sync
```

## Usage

### Run a single agent

```bash
agent-mesh run --agent claude --prompt "Say hello"
agent-mesh run --agent codex --prompt "List files"
agent-mesh run --agent gemini --prompt "Say hello"
```

### Run as MCP server

```bash
python -m agent_mesh.mcp_server
```

### Register as MCP tool

**Codex:**
```bash
codex mcp add agent-mesh -- uv run python -m agent_mesh.mcp_server
```

**Claude:**
```bash
claude mcp add-json agent-mesh '{"type":"stdio","command":"uv","args":["run","python","-m","agent_mesh.mcp_server"]}'
```

## Development

```bash
uv sync --all-extras
uv run pytest
```
