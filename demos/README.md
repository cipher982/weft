# Agent Mesh Demos

This directory contains demo scripts that showcase agent-to-agent interoperability via the agent-mesh MCP server.

## Prerequisites

Before running any demos, ensure:

1. **CLIs are installed and authenticated:**
   - Claude Code: `npm install -g @anthropic-ai/claude-code` then `claude auth`
   - Codex: `npm install -g @openai/codex` with `OPENAI_API_KEY` set
   - Gemini: `npm install -g @anthropic-ai/gemini-cli` with `GEMINI_API_KEY` set

2. **agent-mesh is installed:**
   ```bash
   cd /path/to/weft
   uv sync
   ```

## Available Demos

### 1. Codex Calls Claude (`codex_calls_claude.sh`)

Demonstrates Codex using Claude via the MCP `claude_run` tool.

**What it does:**
1. Registers agent-mesh as an MCP server in Codex
2. Has Codex invoke the `claude_run` tool
3. Claude responds to Codex's query
4. Cleans up temporary workspace

**Run it:**
```bash
./demos/codex_calls_claude.sh
```

**Expected output:**
- Registration confirmation
- Codex task execution
- Claude's response via MCP
- Clean teardown

### 2. Claude Calls Codex (`claude_calls_codex.sh`)

Demonstrates Claude using Codex via the MCP `codex_exec` tool.

**What it does:**
1. Registers agent-mesh as an MCP server in Claude
2. Has Claude invoke the `codex_exec` tool
3. Codex executes a task and returns results
4. Cleans up temporary workspace

**Run it:**
```bash
./demos/claude_calls_codex.sh
```

**Expected output:**
- Registration confirmation
- Claude prompt with tool usage
- Codex execution results
- Clean teardown

## Troubleshooting

### "Command not found" errors
Ensure the CLI is installed and in your PATH:
```bash
which claude
which codex
which gemini
```

### "Not authenticated" errors
Run the authentication command for each CLI:
```bash
claude auth          # Opens browser for OAuth
export OPENAI_API_KEY='your-key'
export GEMINI_API_KEY='your-key'
```

### MCP server already registered
If you see registration errors, the server may already exist. You can:
```bash
# Remove and re-add
codex mcp remove agent-mesh
claude mcp remove agent-mesh

# Or just continue - the demos handle this gracefully
```

### Timeouts
Demos use 60s timeouts by default. If your first request takes longer (cold start), you may see timeout messages. This is expected and won't affect the demo's educational value.

## Cleanup

All demos use temporary directories and trap handlers for automatic cleanup. No manual cleanup required.

To unregister MCP servers:
```bash
codex mcp remove agent-mesh
claude mcp remove agent-mesh
```

## Implementation Details

Each demo script:
- ✓ Validates prerequisites before running
- ✓ Creates isolated temporary workspaces
- ✓ Uses trap handlers for guaranteed cleanup
- ✓ Provides verbose output explaining each step
- ✓ Handles common errors gracefully
- ✓ Leaves no lingering processes or files
