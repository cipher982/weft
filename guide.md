Below is a handoff-ready **spec + roadmap** for a Python “agent mesh” that lets **Claude Code CLI, Codex CLI, and Gemini CLI** cooperate **headlessly**, with clean **exit behavior**, plus an **MCP layer** so any one of them can call the others as tools.

---

## 0) Executive summary

Build a Python project (“agent-mesh”) that provides two integration paths:

1. **Headless subprocess adapters (MVP core):**
   Run each CLI in its *non-interactive* mode so it **exits automatically** and returns **structured output** (JSON / JSONL) for scripts.

2. **MCP tool server (MVP+):**
   Expose the above adapters as **MCP tools** (stdio transport), so *any* MCP-capable host agent (Claude Code, Codex, Gemini, your own orchestrator) can call:

   * `agent_mesh.claude_run(prompt, cwd, …)`
   * `agent_mesh.codex_exec(task, cwd, …)`
   * `agent_mesh.gemini_run(prompt, cwd, …)`

This gives you the “codex can call claude” style collaboration without background zombie sessions.

---

## 1) Why MCP is different from “just call a CLI command”

Calling a CLI command is **one-off**: spawn process → capture stdout/stderr → done.

MCP is a **standard tool protocol** (JSON-RPC) where:

* A “host” (agent) can **discover tools** (`tools/list`)
* Then **call tools** (`tools/call`) with typed JSON args
* Over **stdio** or **streamable HTTP** transports ([Model Context Protocol][1])

So with MCP, Claude/Codex/Gemini don’t need to know how to run each other’s CLIs; they just call `codex_review` / `claude_fix` tools exposed by your Python MCP server.

---

## 2) Known-good headless modes (exit behavior + machine-readable output)

### Claude Code CLI

Use **print mode**:

* `claude -p "..."` runs non-interactively and exits ([Claude Code][2])
* Output control: `--output-format text|json|stream-json` ([Claude Code][2])
* You can force MCP sources: `--mcp-config …` + `--strict-mcp-config` ([Claude Code][2])
* Non-interactive permission prompts can be delegated to an MCP tool via `--permission-prompt-tool` ([Claude Code][2])

MCP config can be added via CLI using JSON:

* `claude mcp add-json <name> '<json>'` including `type:"stdio"` servers ([Claude Code][3])

### Codex CLI

Use **non-interactive exec**:

* `codex exec "<task>"` streams progress to stderr and prints final message to stdout ([OpenAI Developers][4])
* Machine-readable events: `codex exec --json …` emits JSONL events ([OpenAI Developers][4])
* Structured final output: `--output-schema <path>` (+ `-o`) ([OpenAI Developers][4])
* Sandbox/permissions: `--sandbox read-only|workspace-write|danger-full-access` and `--full-auto` ([OpenAI Developers][5])

Codex MCP management:

* `codex mcp add <name> -- <command...>` registers a stdio MCP server ([OpenAI Developers][5])
* Codex as MCP server: `codex mcp-server` and it **exits when downstream closes** ([OpenAI Developers][5])

### Gemini CLI

Use **headless mode**:

* `gemini --prompt "..."` / `-p` runs headlessly ([Google Gemini][6])
* JSON output includes `response` plus stats/metadata ([Google Gemini][6])

Gemini MCP servers are configured via `settings.json` `mcpServers` (supports stdio/SSE/streamable HTTP) ([Google Gemini][7])

---

## 3) MVP goals / non-goals

### Goals

* **Zero interactive sessions** in the core path: every run must naturally exit.
* **Structured outputs** (JSON/JSONL) to feed downstream agents.
* A **single Python API** to run any agent:

  * `run_claude(prompt, cwd, …) -> AgentResult`
  * `run_codex(task, cwd, …) -> AgentResult`
  * `run_gemini(prompt, cwd, …) -> AgentResult`
* An **MCP server** that exposes those as tools (stdio transport), so Claude/Codex/Gemini can call each other.

### Non-goals (for MVP)

* Driving full-screen TUIs via pexpect/PTY automation.
* Multi-machine orchestration.
* Long-lived “chat sessions” bridging between them (you can add later).

---

## 4) System architecture

### 4.1 Components

**A) Python library (`agent_mesh/`)**

* `runners/claude.py` → subprocess wrapper around `claude -p`
* `runners/codex.py` → wrapper around `codex exec`
* `runners/gemini.py` → wrapper around `gemini --prompt`
* `types.py` → `AgentResult`, `RunConfig`, `Usage`, `Artifacts`
* `normalize.py` → unify outputs into consistent schema
* `workspace.py` → working dir, temp copies, git diff capture

**B) Python CLI entrypoint**

* `agent-mesh run --agent claude --cwd ... --prompt ...`
* `agent-mesh pipeline review` (Claude implements → Codex reviews → Claude applies fixes)
* outputs machine-readable JSON by default

**C) MCP server (`agent_mesh/mcp_server.py`)**

* Stdio MCP server exposing tools:

  * `claude_run`
  * `codex_exec`
  * `gemini_run`
  * (optional) `git_diff`, `git_apply_patch`, `read_file` (keep minimal for MVP)

---

## 5) Output contract (normalize everything)

Define a single result shape the whole system speaks:

```json
{
  "agent": "claude|codex|gemini",
  "mode": "headless",
  "cwd": "/abs/path",
  "ok": true,
  "exit_code": 0,
  "started_at": "...",
  "ended_at": "...",
  "duration_ms": 12345,
  "stdout": "...",
  "stderr": "...",
  "structured": { "response": "...", "events": [] },
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

Notes:

* Codex supports JSONL event streaming (`--json`) and structured output with `--output-schema`. ([OpenAI Developers][4])
* Gemini headless JSON output includes `response` and stats. ([Google Gemini][6])
* Claude print mode supports `--output-format json` / `stream-json`. ([Claude Code][2])

---

## 6) MVP flows you’ll actually use

### Flow A: “Claude implements, Codex reviews”

1. `claude -p --output-format json` to implement change in repo
2. capture `git diff`
3. `codex exec --output-schema review_schema.json` to review diff + repo context
4. optionally feed review back into Claude for fixes

### Flow B: “Codex calls Claude” (via MCP tools)

* Register `agent-mesh` MCP server in Codex:

  * `codex mcp add agent-mesh -- python -m agent_mesh.mcp_server` ([OpenAI Developers][5])
* Then Codex can invoke `claude_run()` as a tool in its own reasoning loop.

### Flow C: “Gemini as a second reviewer”

* Gemini headless with JSON output for “fast safety / style pass”
* Useful when you want 2 independent reviewers.

---

## 7) Detailed implementation spec (what your coding agent should build)

### 7.1 Repo scaffolding

* `pyproject.toml` with:

  * `typer` (CLI)
  * `pydantic` (schemas)
  * `anyio` or `asyncio` utilities
  * an MCP server library (see 7.4)
* `agent_mesh/` package, `agent_mesh/__main__.py` for `python -m agent_mesh …`

### 7.2 Subprocess runner requirements

For each runner:

* Must support:

  * `cwd`
  * environment override
  * timeout
  * streaming capture (optional)
* Must return:

  * `stdout`, `stderr`, exit code, timestamps
  * parsed JSON if requested

**Claude runner**

* Command template:

  * `claude -p "<prompt>" --output-format json`
* Optional safety:

  * restrict tools: `--tools "Read,Edit,Bash"` or disable tools for pure analysis `--tools ""` ([Claude Code][2])
* MCP:

  * allow `--mcp-config <file>` and `--strict-mcp-config` ([Claude Code][2])

**Codex runner**

* Command templates:

  * Minimal final-only:

    * `codex exec "<task>"`
  * JSONL events:

    * `codex exec --json "<task>"`
  * Structured final:

    * `codex exec --output-schema schema.json -o out.json "<task>"` ([OpenAI Developers][4])
* Use sandbox flags explicitly (`--sandbox workspace-write` etc.) ([OpenAI Developers][5])

**Gemini runner**

* Headless:

  * `gemini --prompt "<prompt>" --output-format json` (per docs section “JSON Output”) ([Google Gemini][6])
  * If CLI uses a different flag name in your installed version, the wrapper should detect capability via `gemini --help` once and cache it.

### 7.3 Workspace + diff capture

* Always capture:

  * `git status --porcelain`
  * `git diff`
  * `git diff --staged`
* Optionally support a temp worktree mode later (not MVP).

### 7.4 MCP server (stdio)

Implement an MCP server that:

* Writes **only MCP JSON-RPC messages to stdout**, logs to stderr ([Model Context Protocol][1])
* Tools:

  * `claude_run(prompt: str, cwd: str, output_format="json", timeout_s=...)`
  * `codex_exec(task: str, cwd: str, json_events: bool=False, output_schema: Optional[str]=None, timeout_s=...)`
  * `gemini_run(prompt: str, cwd: str, output_format="json", timeout_s=...)`
* Returns `AgentResult` JSON.

This immediately unlocks:

* Claude as MCP client (via `--mcp-config` / config files) ([Claude Code][2])
* Codex as MCP client (via `codex mcp add …`) ([OpenAI Developers][5])
* Gemini as MCP client (via `settings.json` `mcpServers`) ([Google Gemini][7])

### 7.5 Configuration examples (hand to your agent)

**Codex: register agent-mesh MCP server**

```bash
codex mcp add agent-mesh -- python -m agent_mesh.mcp_server
```

(Uses the documented `codex mcp add <name> -- <command...>` form.) ([OpenAI Developers][5])

**Claude: add agent-mesh MCP server via JSON**

```bash
claude mcp add-json agent-mesh '{"type":"stdio","command":"python","args":["-m","agent_mesh.mcp_server"],"env":{}}'
```

(Claude Code supports `add-json` with `type:"stdio"`, `command`, `args`, `env`.) ([Claude Code][3])

**Gemini: add agent-mesh MCP server in settings.json**
Add something like (exact file location depends on Gemini CLI, but schema is `mcpServers`):

```json
{
  "mcpServers": {
    "agent-mesh": {
      "command": "python",
      "args": ["-m", "agent_mesh.mcp_server"]
    }
  }
}
```

Gemini CLI discovers MCP servers from `settings.json` `mcpServers` and supports stdio transport. ([Google Gemini][7])

---

## 8) Roadmap (milestones + acceptance criteria)

### Milestone 0 — Skeleton + contracts

**Deliverables**

* Repo scaffold
* `AgentResult` schema + JSON serializer
* `agent-mesh --help`

**Acceptance**

* `agent-mesh version` works
* Unit test validates result schema round-trip

---

### Milestone 1 — Headless runners (core MVP)

**Deliverables**

* `run_claude()`, `run_codex()`, `run_gemini()`
* `agent-mesh run --agent {claude|codex|gemini} …` returns JSON to stdout

**Acceptance**

* Each command exits cleanly and returns `exit_code == 0` on success
* JSON parseable output for each agent path:

  * Claude: `--output-format json` ([Claude Code][2])
  * Codex: `codex exec --json` JSONL capture ([OpenAI Developers][4])
  * Gemini: headless JSON output ([Google Gemini][6])

---

### Milestone 2 — “Claude → Codex review” pipeline command

**Deliverables**

* `agent-mesh pipeline review --impl claude --review codex`
* Auto-captures `git diff` after implementation
* Feeds diff into Codex review schema

**Acceptance**

* Produces `review.json` with structured fields like:

  * `issues[]`, `severity`, `files[]`, `suggested_patch` (optional)

---

### Milestone 3 — MCP server (stdio) for tool-style composition

**Deliverables**

* `python -m agent_mesh.mcp_server` implements MCP tools listed above
* Minimal docs: how to register in Codex/Claude/Gemini

**Acceptance**

* Codex can list tools after `codex mcp add …` and can call them ([OpenAI Developers][5])
* Server writes only JSON-RPC to stdout (protocol compliance) ([Model Context Protocol][1])

---

### Milestone 4 — Agent-to-agent interoperability demos

**Deliverables**

* Demo script: “Codex calls Claude tool to refactor; then Codex applies review”
* Demo script: “Claude calls Codex tool to do review”

**Acceptance**

* One command reproduces the behavior end-to-end with clean teardown (no lingering processes)

---

## 9) Practical guardrails (so this doesn’t get messy)

1. **Hard timeouts everywhere** (per-run; per-tool call).
2. **Explicit sandbox/permission policies**:

   * Codex: use `--sandbox` deliberately ([OpenAI Developers][5])
   * Claude: constrain tools via `--tools` where appropriate ([Claude Code][2])
3. **Structured outputs > scraping text**:

   * Codex `--output-schema` ([OpenAI Developers][4])
   * Claude JSON output formats ([Claude Code][2])
   * Gemini JSON output schema ([Google Gemini][6])
4. **MCP stdout hygiene**: never print logs to stdout in MCP mode ([Model Context Protocol][1])

---

## 10) “Exactly what’s needed” checklist for your terminal coding agent

* [ ] Create `agent_mesh` package + `AgentResult` schema
* [ ] Implement subprocess runner utility (`run_cmd()`) with timeout + capture
* [ ] Implement `claude_run` using `claude -p … --output-format json` ([Claude Code][2])
* [ ] Implement `codex_exec` using:

  * `codex exec --json …` for event capture ([OpenAI Developers][4])
  * optional `--output-schema` for structured final output ([OpenAI Developers][4])
* [ ] Implement `gemini_run` using headless `--prompt/-p` and JSON output ([Google Gemini][6])
* [ ] Implement `agent-mesh pipeline review` (Claude implements → Codex reviews)
* [ ] Implement `agent_mesh.mcp_server` (stdio MCP tools)
* [ ] Add docs with the exact registration commands:

  * `codex mcp add agent-mesh -- python -m agent_mesh.mcp_server` ([OpenAI Developers][5])
  * `claude mcp add-json … type:"stdio" …` ([Claude Code][3])
  * Gemini `settings.json` `mcpServers` config ([Google Gemini][7])

---

If you want the spec to also include **a concrete JSON schema** for “review output” (issues/severity/files/suggested diffs) that Codex must conform to via `--output-schema`, say the word and I’ll paste a good default.

[1]: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports "Transports - Model Context Protocol"
[2]: https://code.claude.com/docs/en/cli-reference "CLI reference - Claude Code Docs"
[3]: https://code.claude.com/docs/en/mcp "Connect Claude Code to tools via MCP - Claude Code Docs"
[4]: https://developers.openai.com/codex/sdk/ "Codex SDK"
[5]: https://developers.openai.com/codex/cli/reference/ "Command line options"
[6]: https://google-gemini.github.io/gemini-cli/docs/cli/headless.html "Headless Mode | gemini-cli"
[7]: https://google-gemini.github.io/gemini-cli/docs/tools/mcp-server.html "MCP servers with the Gemini CLI | gemini-cli"

