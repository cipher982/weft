# Agent Mesh Specification

**Status:** In Progress
**Protocol:** SDP-1
**Created:** 2024-12-27

---

## Executive Summary

Build a Python package "agent-mesh" (package name: `agent_mesh`) that enables headless, structured interaction between Claude Code CLI, Codex CLI, and Gemini CLI. The system provides:

1. **Subprocess adapters** - Run each CLI non-interactively with JSON output
2. **MCP tool server** - Expose adapters as MCP tools for agent-to-agent calls

---

## Prerequisites

Each CLI must be installed and authenticated:

| CLI | Install | Auth |
|-----|---------|------|
| Claude Code | `npm install -g @anthropic-ai/claude-code` | `claude auth` (browser OAuth) |
| Codex | `npm install -g @openai/codex` | `OPENAI_API_KEY` env var |
| Gemini | `npm install -g @anthropic-ai/gemini-cli` | `GEMINI_API_KEY` env var |

---

## Decision Log

### Decision: Package name `agent_mesh` with CLI command `agent-mesh`
**Context:** Need consistent naming for Python package and CLI
**Choice:** Package `agent_mesh`, CLI `agent-mesh`, repo `weft`
**Rationale:** Follows Python naming conventions (underscore for package, hyphen for CLI)
**Revisit if:** Naming conflicts arise

### Decision: Use `mcp` library from Anthropic for MCP server
**Context:** Need MCP server implementation
**Choice:** Use `mcp` PyPI package (official Anthropic MCP SDK)
**Rationale:** Official, well-documented, handles protocol details
**Revisit if:** Performance issues or missing features

### Decision: Async-first architecture with sync wrappers
**Context:** Subprocesses benefit from async, but CLI needs sync
**Choice:** Core is async (`asyncio`), CLI uses `asyncio.run()`
**Rationale:** Better timeout handling, future streaming support
**Revisit if:** Complexity outweighs benefits

### Decision: Bash scripts for demos with comprehensive error handling
**Context:** Need demos that work without manual intervention
**Choice:** Bash scripts with prerequisite checks, trap handlers for cleanup, and verbose output
**Rationale:** Self-contained, easy to read, guaranteed cleanup via traps
**Revisit if:** Need cross-platform support (consider Python scripts)

---

## Architecture

```
agent_mesh/
├── __init__.py          # Package exports
├── __main__.py          # CLI entrypoint (python -m agent_mesh)
├── cli.py               # Typer CLI app
├── types.py             # Pydantic models (AgentResult, RunConfig, etc.)
├── normalize.py         # Output normalization
├── workspace.py         # Git diff capture, cwd handling
├── runners/
│   ├── __init__.py
│   ├── base.py          # Base runner with subprocess utilities
│   ├── claude.py        # Claude Code CLI runner
│   ├── codex.py         # Codex CLI runner
│   └── gemini.py        # Gemini CLI runner
├── mcp_server.py        # MCP stdio server
└── pipelines/
    ├── __init__.py
    └── review.py        # Claude→Codex review pipeline
```

---

## Output Contract

All runners return this normalized structure:

```json
{
  "agent": "claude|codex|gemini",
  "mode": "headless",
  "cwd": "/abs/path",
  "ok": true,
  "exit_code": 0,
  "started_at": "2024-12-27T10:00:00Z",
  "ended_at": "2024-12-27T10:00:05Z",
  "duration_ms": 5000,
  "stdout": "...",
  "stderr": "...",
  "structured": {
    "response": "...",
    "events": []
  },
  "artifacts": {
    "files_written": [],
    "git_diff": "..."
  },
  "usage": {
    "input_tokens": null,
    "output_tokens": null,
    "cached_input_tokens": null
  }
}
```

---

## Implementation Phases

### Phase 0: Validate & Spec ✓
- [x] Read requirements from guide.md
- [x] Create this spec document
- [x] Commit spec

### Phase 1: Skeleton + Contracts (Milestone 0) ✓
**Goal:** Working package structure with schema definitions

**Deliverables:**
- pyproject.toml with dependencies
- agent_mesh package structure
- AgentResult Pydantic model
- Basic CLI that responds to `agent-mesh version` and `--help`

**Acceptance criteria:**
- [x] `uv run agent-mesh version` outputs version string
- [x] `uv run agent-mesh --help` shows available commands
- [x] Unit test validates AgentResult schema serialization

**Test commands:**
```bash
uv run agent-mesh version
uv run agent-mesh --help
uv run pytest tests/test_types.py -v
```

### Phase 2: Headless Runners (Milestone 1) ✓
**Goal:** Implement subprocess runners for all three CLIs

**Deliverables:**
- Base runner with timeout, capture, async subprocess
- Claude runner: `claude -p "..." --output-format json`
- Codex runner: `codex exec --json "..."`
- Gemini runner: `gemini --output-format json "..."`
- CLI command: `agent-mesh run --agent {claude|codex|gemini} --prompt "..."`

**Acceptance criteria:**
- [x] `agent-mesh run --agent claude --prompt "Say hello"` returns JSON
- [x] `agent-mesh run --agent codex --prompt "List files"` returns JSON
- [x] `agent-mesh run --agent gemini --prompt "Say hello"` returns JSON (requires GEMINI_API_KEY)
- [x] All commands exit cleanly (no zombie processes)
- [x] Timeout handling works (kills subprocess after limit)

**Test commands:**
```bash
uv run agent-mesh run --agent claude --prompt "Say 'test passed'" --timeout 30
uv run agent-mesh run --agent codex --prompt "echo 'test passed'" --timeout 30
uv run agent-mesh run --agent gemini --prompt "Say 'test passed'" --timeout 30
```

### Phase 3: Pipeline Review Command (Milestone 2)
**Goal:** Implement Claude→Codex review workflow

**Deliverables:**
- Workspace module for git diff capture
- Review pipeline: Claude implements → git diff → Codex reviews
- CLI command: `agent-mesh pipeline review --prompt "..." --cwd ...`

**Acceptance criteria:**
- [ ] `agent-mesh pipeline review` captures implementation diff
- [ ] Review output has structured fields (issues, severity, files)
- [ ] Pipeline handles failures gracefully

**Test commands:**
```bash
# In a test git repo:
uv run agent-mesh pipeline review --prompt "Add a hello.py file" --cwd /tmp/test-repo
```

### Phase 4: MCP Server (Milestone 3) ✓
**Goal:** Expose runners as MCP tools

**Deliverables:**
- MCP stdio server with tools: `claude_run`, `codex_exec`, `gemini_run`
- Server writes only JSON-RPC to stdout, logs to stderr
- Registration documentation

**Acceptance criteria:**
- [x] `python -m agent_mesh.mcp_server` starts and responds to MCP protocol
- [x] Tools discoverable via `tools/list`
- [x] Tool calls return AgentResult JSON
- [x] No non-MCP output to stdout

**Test commands:**
```bash
# Run comprehensive MCP server tests
uv run python tests/test_mcp_server.py

# Register in Codex and test
codex mcp add agent-mesh -- uv run python -m agent_mesh.mcp_server
```

### Phase 5: Integration & Demos (Milestone 4) ✓
**Goal:** Validate agent-to-agent interoperability

**Deliverables:**
- Demo script: Codex calls Claude via MCP
- Demo script: Claude calls Codex via MCP
- End-to-end test with clean teardown

**Acceptance criteria:**
- [x] Demo scripts complete without manual intervention
- [x] No lingering processes after demos
- [x] README with usage examples

**Test commands:**
```bash
# Run demos
./demos/codex_calls_claude.sh
./demos/claude_calls_codex.sh

# Verify demos directory structure
ls -la demos/
```

---

## Dependencies

```toml
[project]
dependencies = [
    "typer>=0.9.0",
    "pydantic>=2.0.0",
    "mcp>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]
```

---

## CLI Commands

```
agent-mesh version                           # Show version
agent-mesh run --agent {claude|codex|gemini} # Run single agent
agent-mesh pipeline review                   # Claude→Codex review flow
```

---

## MCP Tools Schema

### claude_run
```json
{
  "name": "claude_run",
  "description": "Run Claude Code CLI in headless mode",
  "inputSchema": {
    "type": "object",
    "properties": {
      "prompt": {"type": "string", "description": "The prompt to send"},
      "cwd": {"type": "string", "description": "Working directory"},
      "output_format": {"type": "string", "enum": ["json", "text"], "default": "json"},
      "timeout_s": {"type": "integer", "default": 120}
    },
    "required": ["prompt"]
  }
}
```

### codex_exec
```json
{
  "name": "codex_exec",
  "description": "Run Codex CLI exec in headless mode",
  "inputSchema": {
    "type": "object",
    "properties": {
      "task": {"type": "string", "description": "The task to execute"},
      "cwd": {"type": "string", "description": "Working directory"},
      "json_events": {"type": "boolean", "default": false},
      "timeout_s": {"type": "integer", "default": 120}
    },
    "required": ["task"]
  }
}
```

### gemini_run
```json
{
  "name": "gemini_run",
  "description": "Run Gemini CLI in headless mode",
  "inputSchema": {
    "type": "object",
    "properties": {
      "prompt": {"type": "string", "description": "The prompt to send"},
      "cwd": {"type": "string", "description": "Working directory"},
      "timeout_s": {"type": "integer", "default": 120}
    },
    "required": ["prompt"]
  }
}
```

---

## Registration Commands

**Codex:**
```bash
codex mcp add agent-mesh -- uv run python -m agent_mesh.mcp_server
```

**Claude:**
```bash
claude mcp add-json agent-mesh '{"type":"stdio","command":"uv","args":["run","python","-m","agent_mesh.mcp_server"]}'
```

**Gemini:** Add to `~/.gemini/settings.json`:
```json
{
  "mcpServers": {
    "agent-mesh": {
      "command": "uv",
      "args": ["run", "python", "-m", "agent_mesh.mcp_server"]
    }
  }
}
```
