#!/usr/bin/env bash
# Demo: Codex orchestrates Claude to write code, then reviews it
#
# This demonstrates real agent collaboration:
# 1. Codex uses claude_run MCP tool to have Claude write a Python script
# 2. Codex reviews what Claude wrote and suggests improvements
#
# Prerequisites:
# - Codex CLI installed and authenticated (OPENAI_API_KEY)
# - Claude CLI installed and authenticated
# - agent-mesh installed (uv sync)

set -euo pipefail

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$DEMO_DIR/.." && pwd)"

echo "=== Agent Collaboration Demo: Codex Orchestrates Claude ==="
echo ""

# Prerequisites check
echo "Checking prerequisites..."
command -v codex &>/dev/null || { echo "ERROR: codex not found"; exit 1; }
command -v claude &>/dev/null || { echo "ERROR: claude not found"; exit 1; }
[[ -n "${OPENAI_API_KEY:-}" ]] || { echo "ERROR: OPENAI_API_KEY not set"; exit 1; }
echo "  ✓ All prerequisites met"
echo ""

# Register MCP server with absolute Python path (works from any directory)
echo "Step 1: Register agent-mesh MCP server in Codex"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python3"
codex mcp add agent-mesh -- "$VENV_PYTHON" -m agent_mesh.mcp_server 2>/dev/null || true
echo "  ✓ agent-mesh registered"
echo ""

# Create workspace
TEMP_WORKSPACE=$(mktemp -d)
trap "rm -rf '$TEMP_WORKSPACE'" EXIT
cd "$TEMP_WORKSPACE"
git init -q
echo "# Demo Project" > README.md
git add . && git commit -q -m "init"
echo "Step 2: Created temp workspace: $TEMP_WORKSPACE"
echo ""

# The actual collaboration task
TASK='You have access to the claude_run MCP tool which runs Claude Code CLI.

Your task:
1. Use claude_run to ask Claude to write a Python script called "fetch_weather.py" that:
   - Takes a city name as a command line argument
   - Uses the requests library to fetch weather from wttr.in
   - Prints a formatted weather summary

   Pass this to claude_run: "Write fetch_weather.py - a CLI script that fetches weather from wttr.in for a given city. Use requests library. Include error handling."

2. After Claude creates the file, review what was written and tell me:
   - What Claude created
   - One specific improvement you would make

Be concise. This is a demo of agent collaboration.'

echo "Step 3: Codex orchestrating Claude..."
echo "  Task: Have Claude write a weather script, then Codex reviews it"
echo ""
echo "--- BEGIN AGENT OUTPUT ---"
echo ""

# Run with --json for structured output, --full-auto for tool access
timeout 180 codex exec --json --full-auto "$TASK" 2>&1 | tee output.jsonl | while read -r line; do
    # Extract and display agent messages in real-time
    if echo "$line" | jq -e '.item.type == "agent_message"' &>/dev/null; then
        echo "$line" | jq -r '.item.text // empty' 2>/dev/null || true
    fi
done || {
    echo ""
    echo "(Codex finished or timed out after 180s)"
}

echo ""
echo "--- END AGENT OUTPUT ---"
echo ""

# Show what files were created
echo "Step 4: Results"
if [ -f fetch_weather.py ]; then
    echo "  ✓ Claude created fetch_weather.py:"
    echo ""
    cat fetch_weather.py
    echo ""
else
    echo "  (No file created - Claude may have been blocked or task incomplete)"
fi

echo ""
echo "Step 5: Cleanup"
echo "  Removing temp workspace..."
# Note: Keep agent-mesh MCP server registered for future use
# To unregister: codex mcp remove agent-mesh

echo ""
echo "=== Demo Complete ==="
echo ""
echo "What happened:"
echo "  1. Codex received a task requiring Claude's help"
echo "  2. Codex used the claude_run MCP tool to invoke Claude"
echo "  3. Claude wrote Python code in the workspace"
echo "  4. Codex reviewed Claude's output and provided feedback"
echo "  5. Real agent-to-agent collaboration via MCP!"
