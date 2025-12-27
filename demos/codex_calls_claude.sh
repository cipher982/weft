#!/usr/bin/env bash
# Demo: Codex calls Claude via agent-mesh MCP server
#
# This script demonstrates:
# 1. Registering agent-mesh as an MCP server in Codex
# 2. Codex using the claude_run tool to invoke Claude
# 3. Clean teardown
#
# Prerequisites:
# - Codex CLI installed and authenticated
# - Claude CLI installed and authenticated
# - agent-mesh installed (uv sync)

set -euo pipefail

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$DEMO_DIR/.." && pwd)"

echo "=== Codex Calls Claude Demo ==="
echo ""
echo "Prerequisites check:"
echo "  - Codex CLI: $(which codex || echo 'NOT FOUND')"
echo "  - Claude CLI: $(which claude || echo 'NOT FOUND')"
echo "  - agent-mesh: $(cd "$PROJECT_ROOT" && uv run agent-mesh version 2>/dev/null || echo 'NOT FOUND')"
echo ""

# Check prerequisites
if ! command -v codex &> /dev/null; then
    echo "ERROR: Codex CLI not found. Install with: npm install -g @openai/codex"
    exit 1
fi

if ! command -v claude &> /dev/null; then
    echo "ERROR: Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
    exit 1
fi

echo "Step 1: Register agent-mesh MCP server in Codex"
echo "  Command: codex mcp add agent-mesh -- uv run python -m agent_mesh.mcp_server"
cd "$PROJECT_ROOT"
codex mcp add agent-mesh -- uv run python -m agent_mesh.mcp_server || {
    echo "  Note: Server may already be registered, continuing..."
}
echo "  ✓ Registered"
echo ""

echo "Step 2: Verify MCP server is available"
echo "  Command: codex mcp list"
codex mcp list | grep -q agent-mesh && echo "  ✓ agent-mesh MCP server found" || {
    echo "  ERROR: agent-mesh not found in MCP server list"
    exit 1
}
echo ""

echo "Step 3: Create temporary workspace for demo"
TEMP_WORKSPACE=$(mktemp -d)
echo "  Workspace: $TEMP_WORKSPACE"
trap "rm -rf '$TEMP_WORKSPACE'" EXIT
echo ""

echo "Step 4: Have Codex call Claude via MCP"
echo "  Task: 'Use the claude_run tool to ask Claude to say hello and explain what MCP is in one sentence'"
echo ""
cd "$TEMP_WORKSPACE"

# Use --json to get structured output, timeout after 60s
codex exec --json --timeout 60 "Use the claude_run tool to ask Claude to say 'Hello from Claude via MCP!' and explain what MCP (Model Context Protocol) is in exactly one sentence" > codex_output.json 2>&1 || {
    echo "  Note: Codex execution may have failed or timed out"
    echo "  Output saved to: $TEMP_WORKSPACE/codex_output.json"
}

echo "Step 5: Display results"
if [ -f codex_output.json ]; then
    echo "  Output file size: $(wc -c < codex_output.json) bytes"
    echo ""
    echo "  First 500 characters:"
    head -c 500 codex_output.json
    echo ""
    echo ""
    echo "  Full output saved to: $TEMP_WORKSPACE/codex_output.json"
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
echo "  1. Registered agent-mesh as an MCP server in Codex"
echo "  2. Codex invoked the claude_run MCP tool"
echo "  3. agent-mesh ran Claude CLI in headless mode"
echo "  4. Claude's response was returned to Codex"
echo "  5. All temporary files cleaned up"
echo ""
echo "To unregister: codex mcp remove agent-mesh"
