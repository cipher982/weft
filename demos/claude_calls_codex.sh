#!/usr/bin/env bash
# Demo: Claude calls Codex via agent-mesh MCP server
#
# This script demonstrates:
# 1. Registering agent-mesh as an MCP server in Claude
# 2. Claude using the codex_exec tool to invoke Codex
# 3. Clean teardown
#
# Prerequisites:
# - Claude CLI installed and authenticated
# - Codex CLI installed and authenticated (with OPENAI_API_KEY)
# - agent-mesh installed (uv sync)

set -euo pipefail

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$DEMO_DIR/.." && pwd)"

echo "=== Claude Calls Codex Demo ==="
echo ""
echo "Prerequisites check:"
echo "  - Claude CLI: $(which claude || echo 'NOT FOUND')"
echo "  - Codex CLI: $(which codex || echo 'NOT FOUND')"
echo "  - OPENAI_API_KEY: $([ -n "${OPENAI_API_KEY:-}" ] && echo 'SET' || echo 'NOT SET')"
echo "  - agent-mesh: $(cd "$PROJECT_ROOT" && uv run agent-mesh version 2>/dev/null || echo 'NOT FOUND')"
echo ""

# Check prerequisites
if ! command -v claude &> /dev/null; then
    echo "ERROR: Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
    exit 1
fi

if ! command -v codex &> /dev/null; then
    echo "ERROR: Codex CLI not found. Install with: npm install -g @openai/codex"
    exit 1
fi

if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "ERROR: OPENAI_API_KEY environment variable not set"
    echo "  Set it with: export OPENAI_API_KEY='your-key-here'"
    exit 1
fi

echo "Step 1: Register agent-mesh MCP server in Claude"
echo "  Command: claude mcp add-json agent-mesh '{\"type\":\"stdio\",\"command\":\"uv\",\"args\":[\"run\",\"python\",\"-m\",\"agent_mesh.mcp_server\"]}'"
cd "$PROJECT_ROOT"
claude mcp add-json agent-mesh '{"type":"stdio","command":"uv","args":["run","python","-m","agent_mesh.mcp_server"]}' || {
    echo "  Note: Server may already be registered, continuing..."
}
echo "  ✓ Registered"
echo ""

echo "Step 2: Verify MCP server is available"
echo "  Command: claude mcp list"
claude mcp list | grep -q agent-mesh && echo "  ✓ agent-mesh MCP server found" || {
    echo "  ERROR: agent-mesh not found in MCP server list"
    exit 1
}
echo ""

echo "Step 3: Create temporary workspace for demo"
TEMP_WORKSPACE=$(mktemp -d)
echo "  Workspace: $TEMP_WORKSPACE"
trap "rm -rf '$TEMP_WORKSPACE'" EXIT
cd "$TEMP_WORKSPACE"

# Create a simple file for Codex to work with
echo "# Demo Project" > README.md
echo "This is a test file for the demo." >> README.md
echo "  ✓ Created README.md"
echo ""

echo "Step 4: Have Claude call Codex via MCP"
echo "  Prompt: 'Use the codex_exec tool to list all files in the current directory and count them'"
echo ""

# Use --output-format json for structured output, with prompt that uses the MCP tool
claude -p "Use the codex_exec tool to execute this task: 'List all files in the current directory using ls -la and count how many files there are'. After getting the result, tell me what Codex found." --output-format json --cwd "$TEMP_WORKSPACE" > claude_output.json 2>&1 || {
    echo "  Note: Claude execution may have failed or timed out"
    echo "  Output saved to: $TEMP_WORKSPACE/claude_output.json"
}

echo "Step 5: Display results"
if [ -f claude_output.json ]; then
    echo "  Output file size: $(wc -c < claude_output.json) bytes"
    echo ""
    echo "  First 500 characters:"
    head -c 500 claude_output.json
    echo ""
    echo ""
    echo "  Full output saved to: $TEMP_WORKSPACE/claude_output.json"
    echo "  (Workspace will be cleaned up on exit)"
else
    echo "  No output file generated"
fi
echo ""

echo "Step 6: Cleanup (automatic via trap)"
echo "  Temporary workspace will be removed: $TEMP_WORKSPACE"
echo ""

echo "=== Demo Complete ==="
echo ""
echo "What happened:"
echo "  1. Registered agent-mesh as an MCP server in Claude"
echo "  2. Claude invoked the codex_exec MCP tool"
echo "  3. agent-mesh ran Codex CLI in headless mode"
echo "  4. Codex's response was returned to Claude"
echo "  5. All temporary files cleaned up"
echo ""
echo "To unregister: claude mcp remove agent-mesh"
