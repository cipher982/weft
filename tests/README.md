# Agent Mesh Tests

## Test Structure

```
tests/
├── test_types.py          # Unit tests for Pydantic models
├── test_mcp_server.py     # MCP protocol tests (no API calls)
├── test_e2e.py            # E2E integration tests (REAL API calls)
├── E2E_TEST_REPORT.md     # Detailed test results and analysis
└── README.md              # This file
```

## Running Tests

### Quick Start

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_e2e.py -v

# Run with verbose output
uv run pytest -v --tb=short
```

### Test Categories

#### Unit Tests (Fast, No API Calls)
```bash
# Types and models
uv run pytest tests/test_types.py -v

# MCP protocol (subprocess only)
uv run pytest tests/test_mcp_server.py -v
```

#### E2E Tests (Slow, Real API Calls)
```bash
# All e2e tests (costs money, ~$0.02 per run)
uv run pytest tests/test_e2e.py -v

# Skip expensive tests
uv run pytest tests/test_e2e.py -m "not slow" -v

# Run only slow tests
uv run pytest tests/test_e2e.py -m "slow" -v
```

### Test Markers

- `@pytest.mark.e2e` - End-to-end integration tests
- `@pytest.mark.slow` - Tests that make real API calls or take significant time

Filter by markers:
```bash
# Only e2e tests
uv run pytest -m "e2e" -v

# Only slow tests
uv run pytest -m "slow" -v

# Exclude slow tests
uv run pytest -m "not slow" -v
```

## Prerequisites

### Required CLIs

E2E tests require agent CLIs to be installed and authenticated:

| CLI | Install | Auth |
|-----|---------|------|
| Claude | `npm install -g @anthropic-ai/claude-code` | `claude auth` |
| Codex | `npm install -g @openai/codex` | `export OPENAI_API_KEY='...'` |
| Gemini | `npm install -g @anthropic-ai/gemini-cli` | `export GEMINI_API_KEY='...'` |

### Checking CLI Availability

```bash
# Check which CLIs are available
which claude
command -v codex
echo $GEMINI_API_KEY
```

Tests will automatically skip if required CLIs are not available.

## Test Details

### Unit Tests

**test_types.py** - Validates Pydantic models
- AgentResult structure
- Usage tracking
- Artifacts handling
- JSON serialization

**test_mcp_server.py** - Validates MCP protocol (no API calls)
- Server initialization
- Tool discovery
- Tool signatures
- stdout cleanliness

### E2E Integration Tests

**test_e2e.py** - Complete system integration with real APIs

#### Runner Tests
- `test_claude_runner_real_call` - Claude CLI with JSON output
- `test_codex_runner_real_call` - Codex CLI with JSONL events
- `test_gemini_runner_real_call` - Gemini CLI (if API key set)
- `test_timeout_handling` - Timeout enforcement (1s test)
- `test_invalid_agent_handling` - Error handling

#### MCP Server Tests
- `test_mcp_server_initialize` - Protocol initialization
- `test_mcp_server_tools_list` - Tool discovery
- `test_mcp_tool_call_claude` - Claude tool via MCP
- `test_mcp_tool_call_codex` - Codex tool via MCP

#### Pipeline Tests
- `test_review_pipeline` - Full pipeline: Claude → git diff → Codex

#### Cross-Agent Tests
- `test_cross_agent_setup` - Verify MCP registration (informational)

## Performance

### Test Duration

| Test Suite | Duration |
|------------|----------|
| Unit tests | <5s |
| E2E (all) | ~86s |
| E2E (fast only) | ~4s |

### API Costs

- Claude: ~$0.003/1K tokens
- Codex: ~$0.002/1K tokens
- **Estimated cost per full e2e run**: ~$0.02

## CI/CD Considerations

### Recommended Strategy

```yaml
# Fast feedback
on: [pull_request]
  - uv run pytest -m "not slow"

# Full validation (nightly or pre-release)
on: [schedule]
  - uv run pytest tests/test_e2e.py -v
```

### Environment Variables

Required for full e2e coverage:
- `OPENAI_API_KEY` - For Codex tests
- `GEMINI_API_KEY` - For Gemini tests (optional)

Claude uses OAuth authentication (not env var).

## Troubleshooting

### Tests Skipped

If tests are skipped, check:
```bash
# Verify CLIs are installed
which claude
command -v codex

# Verify API keys
echo $OPENAI_API_KEY
echo $GEMINI_API_KEY

# Test CLI manually
claude -p "test"
codex exec "test"
```

### Timeout Errors

If tests timeout:
- Check network connectivity
- Verify API keys are valid
- Consider increasing timeout in test

### Authentication Errors

If authentication fails:
```bash
# Re-authenticate Claude
claude auth

# Verify API keys
export OPENAI_API_KEY='your-key'
export GEMINI_API_KEY='your-key'
```

## Contributing Tests

When adding new tests:

1. **Use appropriate markers**:
   ```python
   @pytest.mark.e2e
   @pytest.mark.slow  # if makes API calls
   ```

2. **Skip if dependencies missing**:
   ```python
   @pytest.mark.skipif(not has_claude_cli(), reason="...")
   ```

3. **Use temp directories for git operations**:
   ```python
   def test_my_test(temp_git_repo):
       # temp_git_repo is automatically cleaned up
   ```

4. **Set reasonable timeouts**:
   ```python
   timeout_s=60  # for API calls
   timeout_s=5   # for fast operations
   ```

5. **Document API costs in docstring**

## References

- See `E2E_TEST_REPORT.md` for detailed test results
- See `../README.md` for agent-mesh usage
- See `../docs/specs/agent-mesh.md` for architecture
