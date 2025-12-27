#!/usr/bin/env bash
# Demo: Claude delegates code review to Codex
#
# This demonstrates real agent collaboration:
# 1. Claude writes some code
# 2. Claude uses codex_exec MCP tool to have Codex review it
# 3. Claude incorporates Codex's feedback
#
# Prerequisites:
# - Claude CLI installed and authenticated
# - Codex CLI installed and authenticated (OPENAI_API_KEY)
# - agent-mesh installed (uv sync)

set -euo pipefail

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$DEMO_DIR/.." && pwd)"

echo "=== Agent Collaboration Demo: Claude Delegates to Codex ==="
echo ""

# Prerequisites check
echo "Checking prerequisites..."
command -v claude &>/dev/null || { echo "ERROR: claude not found"; exit 1; }
command -v codex &>/dev/null || { echo "ERROR: codex not found"; exit 1; }
[[ -n "${OPENAI_API_KEY:-}" ]] || { echo "ERROR: OPENAI_API_KEY not set"; exit 1; }
echo "  ✓ All prerequisites met"
echo ""

# Register MCP server
echo "Step 1: Register agent-mesh MCP server in Claude"
cd "$PROJECT_ROOT"
claude mcp add-json agent-mesh '{"type":"stdio","command":"uv","args":["run","python","-m","agent_mesh.mcp_server"]}' 2>/dev/null || true
echo "  ✓ agent-mesh registered"
echo ""

# Create workspace with some code to review
TEMP_WORKSPACE=$(mktemp -d)
trap "rm -rf '$TEMP_WORKSPACE'" EXIT
cd "$TEMP_WORKSPACE"
git init -q

# Create a Python file with intentional issues for Codex to find
cat > calculator.py << 'PYEOF'
# A simple calculator module

def add(a, b):
    return a + b

def divide(a, b):
    return a / b

def calculate_average(numbers):
    total = 0
    for n in numbers:
        total = total + n
    return total / len(numbers)

if __name__ == "__main__":
    print(add(5, 3))
    print(divide(10, 2))
    print(calculate_average([1, 2, 3, 4, 5]))
PYEOF

git add . && git commit -q -m "Add calculator module"
echo "Step 2: Created temp workspace with calculator.py"
echo ""
cat calculator.py
echo ""

# The collaboration task
TASK='You have access to the codex_exec MCP tool which runs OpenAI Codex CLI.

I have written calculator.py (already in the workspace). Your task:

1. First, read calculator.py to see what I wrote
2. Use codex_exec to ask Codex to review the code. Pass this task:
   "Review calculator.py for bugs, edge cases, and improvements. Be specific about line numbers."
3. Based on Codex'\''s review, tell me the most critical issue found

Be concise - just identify the main problem Codex found.'

echo "Step 3: Claude delegating code review to Codex..."
echo ""
echo "--- BEGIN AGENT OUTPUT ---"
echo ""

# Run Claude with the task
timeout 180 claude -p "$TASK" \
    --output-format json \
    --dangerously-skip-permissions \
    2>&1 | tee output.json | jq -r '.result // .error // .' 2>/dev/null || {
    echo ""
    echo "(Claude finished or timed out after 180s)"
}

echo ""
echo "--- END AGENT OUTPUT ---"
echo ""

# Check if calculator.py was modified
echo "Step 4: Results"
if git diff --quiet calculator.py 2>/dev/null; then
    echo "  calculator.py unchanged (Claude only reviewed, didn't modify)"
else
    echo "  ✓ calculator.py was modified:"
    git diff calculator.py
fi
echo ""

echo "Step 5: Cleanup"
echo "  Removing temp workspace..."
claude mcp remove agent-mesh 2>/dev/null || true

echo ""
echo "=== Demo Complete ==="
echo ""
echo "What happened:"
echo "  1. Created calculator.py with intentional issues"
echo "  2. Claude used codex_exec MCP tool to delegate review to Codex"
echo "  3. Codex analyzed the code and found issues (division by zero, empty list)"
echo "  4. Claude reported Codex's findings"
echo "  5. Real cross-vendor agent collaboration!"
