#!/bin/bash
# Pytest shortcuts for agent-mesh testing
# Source this file or copy commands as needed

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Agent Mesh Test Shortcuts${NC}"
echo "========================================="
echo ""

# All tests
alias test-all='uv run pytest -v --tb=short'
echo "test-all              Run all tests (unit + e2e)"

# E2E tests
alias test-e2e='uv run pytest tests/test_e2e.py -v --tb=short'
echo "test-e2e              Run all e2e tests (~86s, costs ~\$0.02)"

# Fast tests only
alias test-fast='uv run pytest -m "not slow" -v --tb=short'
echo "test-fast             Run fast tests only (no API calls)"

# Slow tests only
alias test-slow='uv run pytest -m "slow" -v --tb=short'
echo "test-slow             Run slow tests only (API calls)"

# Unit tests
alias test-unit='uv run pytest tests/test_types.py tests/test_mcp_server.py -v'
echo "test-unit             Run unit tests only"

# Specific test files
alias test-types='uv run pytest tests/test_types.py -v'
alias test-mcp='uv run pytest tests/test_mcp_server.py -v'
echo "test-types            Run type/model tests"
echo "test-mcp              Run MCP protocol tests"

# With output
alias test-e2e-verbose='uv run pytest tests/test_e2e.py -v -s'
echo "test-e2e-verbose      Run e2e with output (-s flag)"

# Show summary
alias test-summary='uv run pytest tests/test_e2e.py::test_e2e_summary -v -s'
echo "test-summary          Show e2e test coverage summary"

# Specific runner tests
alias test-claude='uv run pytest tests/test_e2e.py::test_claude_runner_real_call -v -s'
alias test-codex='uv run pytest tests/test_e2e.py::test_codex_runner_real_call -v -s'
alias test-gemini='uv run pytest tests/test_e2e.py::test_gemini_runner_real_call -v -s'
echo "test-claude           Test Claude runner only"
echo "test-codex            Test Codex runner only"
echo "test-gemini           Test Gemini runner only"

# Pipeline test
alias test-pipeline='uv run pytest tests/test_e2e.py::test_review_pipeline -v -s'
echo "test-pipeline         Test review pipeline"

echo ""
echo -e "${YELLOW}Example usage:${NC}"
echo "  source .pytest_shortcuts.sh"
echo "  test-fast"
echo "  test-claude"
echo ""
echo -e "${YELLOW}Or run commands directly:${NC}"
echo "  uv run pytest -m 'not slow' -v"
echo "  uv run pytest tests/test_e2e.py -v"
