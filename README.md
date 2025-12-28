# Agent Mesh

Headless agent coordination for Claude Code, Codex, and Gemini CLI. Enables agents to call each other via the Model Context Protocol (MCP).

## What is Agent Mesh?

Agent Mesh provides:
1. **Headless runners** - Run Claude, Codex, or Gemini non-interactively with structured JSON output
2. **MCP tool server** - Expose agent runners as MCP tools for agent-to-agent communication
3. **Normalized output** - Consistent response format across all agents (exit codes, timing, usage stats)

## Installation

```bash
# Clone and install
git clone <repo-url>
cd weft
uv sync

# Verify installation
uv run agent-mesh version
```

## Prerequisites

Each CLI must be installed and authenticated before use:

| CLI | Install | Auth |
|-----|---------|------|
| Claude Code | `npm install -g @anthropic-ai/claude-code` | `claude auth` (browser OAuth) |
| Codex | `npm install -g @openai/codex` | `export OPENAI_API_KEY='your-key'` |
| Gemini | `npm install -g @google/gemini-cli` | `export GEMINI_API_KEY='your-key'` |

## Usage

### 1. Direct CLI Usage

Run agents directly from the command line:

```bash
# Run Claude with a prompt
agent-mesh run --agent claude --prompt "Explain what MCP is in one sentence"

# Run Codex with a task
agent-mesh run --agent codex --prompt "List all Python files in the current directory"

# Run Gemini with a prompt
agent-mesh run --agent gemini --prompt "What is the capital of France?"

# All commands return normalized JSON output
```

**Output format:**
```json
{
  "agent": "claude",
  "mode": "headless",
  "ok": true,
  "exit_code": 0,
  "duration_ms": 5000,
  "stdout": "...",
  "structured": {
    "response": "...",
    "events": []
  },
  "usage": {
    "input_tokens": 100,
    "output_tokens": 50
  }
}
```

### 2. MCP Server Mode

Run as an MCP server to expose agents as tools:

```bash
# Start the MCP server (stdio mode)
python -m agent_mesh.mcp_server
```

The server exposes three tools:
- `claude_run` - Run Claude Code CLI
- `codex_exec` - Run Codex CLI
- `gemini_run` - Run Gemini CLI

### 3. Register with Other Agents

Register agent-mesh as an MCP server so agents can call each other:

**Codex:**
```bash
codex mcp add agent-mesh -- uv run python -m agent_mesh.mcp_server
codex mcp list  # Verify registration
```

**Claude:**
```bash
claude mcp add-json agent-mesh '{"type":"stdio","command":"uv","args":["run","python","-m","agent_mesh.mcp_server"]}'
claude mcp list  # Verify registration
```

### 4. Agent-to-Agent Communication

Once registered, agents can invoke each other:

**Example: Codex calls Claude**
```bash
# Codex can now use the claude_run tool
codex exec "Use the claude_run tool to ask Claude: 'What is MCP?'"
```

**Example: Claude calls Codex**
```bash
# Claude can now use the codex_exec tool
claude -p "Use the codex_exec tool to list all files in /tmp"
```

### 5. Interactive Demos

Pre-built demo scripts showcase agent-to-agent communication:

```bash
# Demo: Codex calls Claude
./demos/codex_calls_claude.sh

# Demo: Claude calls Codex
./demos/claude_calls_codex.sh
```

See `demos/README.md` for detailed explanations and troubleshooting.

## Common Use Cases

### Use Case 1: Code Review Pipeline
Have Claude implement a feature, then Codex review the changes:
```bash
# Step 1: Claude implements
agent-mesh run --agent claude --prompt "Add logging to main.py"

# Step 2: Capture git diff
git diff > changes.diff

# Step 3: Codex reviews
agent-mesh run --agent codex --prompt "Review these changes: $(cat changes.diff)"
```

### Use Case 2: Multi-Agent Research
Have different agents research different aspects:
```bash
# Claude researches architecture
agent-mesh run --agent claude --prompt "Research microservices architecture pros/cons"

# Codex analyzes code examples
agent-mesh run --agent codex --prompt "Find and analyze microservices examples in this repo"

# Gemini synthesizes findings
agent-mesh run --agent gemini --prompt "Synthesize the research and code analysis"
```

### Use Case 3: Fallback Strategy
Try one agent, fallback to another if it fails:
```bash
agent-mesh run --agent claude --prompt "Complex task" || \
  agent-mesh run --agent codex --prompt "Complex task" || \
  agent-mesh run --agent gemini --prompt "Complex task"
```

## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run specific test files
uv run pytest tests/test_types.py -v
uv run pytest tests/test_mcp_server.py -v

# Format code
uv run black agent_mesh tests

# Type checking
uv run mypy agent_mesh
```

## Architecture

```
agent_mesh/
├── cli.py              # Typer CLI entrypoint
├── types.py            # Pydantic models (AgentResult, RunConfig)
├── runners/            # Agent-specific subprocess runners
│   ├── base.py         # Base runner with timeout/capture
│   ├── claude.py       # Claude Code CLI runner
│   ├── codex.py        # Codex CLI runner
│   └── gemini.py       # Gemini CLI runner
├── mcp_server.py       # MCP stdio server exposing tools
└── workspace.py        # Git diff capture, cwd handling
```

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
