# 005 - Can LiteLLM/Ollama Replace Local-Brain?

**Date:** 2026-02-12
**Status:** Evaluation
**Relates to:** ADR-002 (Smolagents), ADR-005 (CodeAgent with Markdown Tags)

## Problem Statement

We already use Bedrock models via LiteLLM for cloud work. Can we **eliminate local-brain entirely** by using LiteLLM and/or Ollama directly — particularly for sub-agent delegation from Claude Code?

Local-brain currently provides:
1. A multi-step **agent loop** (smolagents CodeAgent) where the local model autonomously decides which tools to call
2. **9 codebase tools** (read files, search code, git operations)
3. **Security** (path jailing, output truncation, sensitive file blocking)
4. A **Claude Code skill** (`/local-brain`) so Claude can delegate tasks

The question: which of these can off-the-shelf components replace?

---

## What Local-Brain Actually Does (The Agent Loop)

```
Claude Code: "What changed in security.py?"
  → /local-brain "What changed in security.py?"
    → Ollama (qwen3:30b) thinks...
      Step 1: calls git_log(5)        → sees recent commits
      Step 2: calls git_diff("security.py") → sees the diff
      Step 3: calls read_file("security.py") → reads current code
      Step 4: synthesizes answer
    → Returns analysis to Claude Code
```

The key value: **the local model autonomously runs a multi-step reasoning loop**, deciding what to explore at each step. This is NOT a single completion — it's 4-10 LLM round-trips with tool execution between each.

---

## Replacement Option A: Claude Code → Ollama Directly (ANTHROPIC_BASE_URL)

Since Ollama v0.14, it speaks the Anthropic Messages API natively:

```bash
export ANTHROPIC_BASE_URL="http://localhost:11434"
export ANTHROPIC_API_KEY="ollama"
# Now Claude Code talks to local Ollama
```

### What This Replaces
- **Everything** — Claude Code itself runs on the local model
- Claude Code's own tools (Read, Bash, Grep, etc.) become the tools

### Why This Doesn't Work as a Sub-Agent
- This **replaces Claude**, not augments it. You lose Claude's reasoning entirely.
- Local models (even qwen3:30b) can't reliably drive Claude Code's complex tool orchestration.
- You want both: Claude for complex tasks, local models for cheap/private reconnaissance.

### Verdict: Not a replacement. This is "run Claude Code on Ollama" not "use Ollama as a sub-agent."

---

## Replacement Option B: ollama-mcp (MCP Server)

[ollama-mcp](https://github.com/rawveg/ollama-mcp) exposes Ollama as MCP tools:

```json
{
  "mcpServers": {
    "ollama": {
      "command": "npx",
      "args": ["-y", "ollama-mcp"]
    }
  }
}
```

### Tools Exposed (14)
- `ollama_chat` — Single chat completion (supports tool/function calling)
- `ollama_generate` — Text completion
- `ollama_embed` — Embeddings
- `ollama_list`, `ollama_pull`, etc. — Model management

### What This Replaces
- Claude Code can call `ollama_chat("What does this function do?", ...)` as a tool
- Single-shot Q&A: "summarize this file", "explain this error"

### What It CANNOT Replace
- **The agent loop.** `ollama_chat` is a single LLM call. The Ollama model cannot:
  - Decide to call `read_file` → inspect the result → decide to call `git_diff` → synthesize
  - There is no multi-step tool execution within the MCP call
  - Claude Code would have to manually orchestrate: call ollama_chat → parse response → execute tool → call ollama_chat again → repeat

### Verdict: Replaces single-shot delegation. Does NOT replace the autonomous agent loop.

---

## Replacement Option C: litellm-agent-mcp

[BerriAI/litellm-agent-mcp](https://github.com/BerriAI/litellm-agent-mcp) lets Claude Code call any LLM:

### Tools Exposed (7)
- `call` — Call any LLM (OpenAI format)
- `messages` — Anthropic Messages API
- `generate_content` — Gemini format
- `compare` — Compare responses from multiple models
- `recommend` — Get model recommendation for a task
- `models` — List available models

### What This Replaces
- Model routing: Claude Code can pick the right model per task
- Cost optimization: Use cheap models for simple queries
- Multi-model comparison: "Ask GPT-4 and qwen3 the same question"

### What It CANNOT Replace
- **Still single-shot completions.** No agent loop, no tool calling within the LLM call.
- The "call" tool sends one prompt, gets one response. No iteration.

### Verdict: Great for routing and model selection. Does NOT replace the agent loop.

---

## Replacement Option D: LiteLLM Proxy Server

Run LiteLLM as a proxy with routing, fallbacks, load balancing:

```yaml
# litellm_config.yaml
model_list:
  - model_name: local-agent
    litellm_params:
      model: ollama_chat/qwen3:30b
      api_base: http://localhost:11434
  - model_name: local-agent
    litellm_params:
      model: ollama_chat/qwen2.5:3b  # fallback
      api_base: http://localhost:11434
```

### What This Replaces
- Model routing with automatic fallback
- Token tracking, rate limiting, cost management
- Unified API for cloud + local models

### What It CANNOT Replace
- **Still just an API proxy.** No agent loop. Callers get single completions.

### Verdict: Infrastructure improvement, not a functional replacement.

---

## Replacement Option E: Claude Code Orchestrates the Loop Itself

What if Claude Code manually runs the agent loop?

```
Claude Code thinking:
  1. Call ollama_chat("What should I look at for security.py changes?")
  2. Ollama says: "Check git log and recent diffs"
  3. Claude Code runs: git_log, git_diff (using its OWN tools)
  4. Call ollama_chat("Here's the diff: {diff}. Analyze the security impact.")
  5. Ollama returns analysis
  6. Claude Code synthesizes final answer
```

### What This Replaces
- The entire local-brain pipeline — Claude Code IS the agent loop orchestrator
- Claude Code already has better tools than local-brain (Read, Bash, Grep, Glob, Edit, Write)

### Problems
- **Context window cost**: Every intermediate step consumes Claude's context (and API tokens)
- **Latency**: Claude round-trip + Ollama round-trip at each step
- **Defeats the purpose**: The original goal was to offload work FROM Claude to save tokens/cost
- **Claude could just... do the task itself**: If Claude is orchestrating, why involve Ollama at all?

### Verdict: Technically works but defeats the purpose of local delegation.

---

## The Gap: Autonomous Agent Loops

Here is the core finding:

| Capability | local-brain | ollama-mcp | litellm-agent-mcp | LiteLLM Proxy | Claude orchestrating |
|-----------|-------------|------------|-------------------|---------------|---------------------|
| Single LLM completion | Yes | Yes | Yes | Yes | Yes |
| Multi-step agent loop | **Yes** | No | No | No | Yes (but wasteful) |
| Tool execution within loop | **Yes (9 tools)** | No | No | No | Yes (Claude's tools) |
| Model decides next action | **Yes** | No | No | No | Yes (but Claude decides) |
| Runs without Claude API | **Yes** | N/A | N/A | N/A | No |
| Cost: $0 per query | **Yes** | Yes | Yes | Yes | No |

**The agent loop is what none of the off-the-shelf replacements provide.**

The MCP servers (ollama-mcp, litellm-agent-mcp) expose "call a model" — a single prompt→response. Local-brain provides "give a model a task and let it autonomously explore using tools until it finds the answer" — that's the smolagents CodeAgent loop.

---

## What CAN Be Replaced

Some parts of local-brain are genuinely replaceable:

| Component | Current (local-brain) | Replacement |
|-----------|----------------------|-------------|
| Single-shot Q&A | Overkill (full agent loop for simple questions) | ollama-mcp `ollama_chat` |
| Model selection | `models.py` (300 LOC) | litellm-agent-mcp `recommend` |
| Model routing/fallback | Not implemented | LiteLLM Router or Proxy |
| Git operations | Custom @tool functions | Claude Code native (Bash git) |
| File reading | Custom @tool with truncation | Claude Code native (Read) |
| Code search | Custom grep-ast integration | Claude Code native (Grep + Glob) |

**The tools themselves are redundant with Claude Code's native tools.** Claude Code has Read, Grep, Glob, Bash — which are strictly better than local-brain's 9 tools.

---

## Recommendation

### Keep local-brain for: Autonomous multi-step exploration

The agent loop — where a local model independently explores the codebase across multiple steps — has no off-the-shelf replacement. This is valuable when:
- You want to save Claude API tokens on reconnaissance tasks
- You need privacy (code never leaves your machine)
- You want parallel exploration (Claude works on one thing, local-brain on another)

### Replace with MCP for: Simple delegation

For single-shot questions ("summarize this file", "what does this function do"), an MCP server is simpler:
- `ollama-mcp` for direct Ollama access
- `litellm-agent-mcp` for multi-model routing

### Consider for the future: Smolagents as an MCP Server

The ideal replacement would be **packaging smolagents itself as an MCP server** — exposing a `run_agent(prompt, tools, model)` MCP tool that runs the full agent loop. This would:
- Eliminate the local-brain CLI and skill wrapper
- Keep the autonomous agent loop
- Be usable from any MCP client (Claude Code, Cursor, etc.)
- Allow LiteLLM routing within the agent

This is essentially local-brain's `run_smolagent()` function exposed as an MCP tool instead of a CLI command.

### The hybrid architecture

```
Claude Code
  ├── ollama-mcp (simple queries, single-shot)
  │     "Summarize this file" → ollama_chat → done
  │
  ├── litellm-agent-mcp (model routing, comparison)
  │     "Which model is best for this?" → recommend → done
  │
  └── smolagents-mcp [NEW — replaces local-brain]
        "Explore security.py changes" → full agent loop
          Step 1: model calls read_file
          Step 2: model calls git_diff
          Step 3: model synthesizes
        → Returns analysis
```

---

## Option F: Wrap Smolagents as an MCP Server (The Clear Path)

Instead of replacing local-brain, **re-package it as an MCP server**. The agent loop IS the value — just expose it directly to Claude Code as a tool.

### What Changes

```
BEFORE (current):
  Claude Code → /local-brain skill → Bash("local-brain 'prompt'") → CLI → smolagents → Ollama

AFTER (MCP server):
  Claude Code → MCP tool call: run_agent("prompt") → smolagents → Ollama
```

### The Implementation (~30 lines of new code)

```python
# local_brain/mcp_server.py
from mcp.server.fastmcp import FastMCP

from .smolagent import run_smolagent, create_agent
from .models import select_model_for_task
from .security import set_project_root

server = FastMCP("local-brain")


@server.tool()
def run_agent(
    prompt: str,
    model: str | None = None,
    project_root: str = ".",
) -> str:
    """Run a local Ollama model as an autonomous agent that explores the codebase.

    The agent runs a multi-step reasoning loop: it reads files, searches code,
    checks git history, and synthesizes an answer — all locally, at zero cost.

    Use for: code review, exploration, understanding unfamiliar code, git analysis.
    Don't use for: simple file reads or git commands (use native tools instead).

    Args:
        prompt: What you want the agent to explore or analyze.
        model: Ollama model name (e.g. "qwen3:30b"). Auto-selects if not specified.
        project_root: Project directory to explore (default: current directory).
    """
    set_project_root(project_root)
    selected_model, _ = select_model_for_task(model)
    return run_smolagent(prompt=prompt, model=selected_model)
```

### Claude Code MCP Config

```json
{
  "mcpServers": {
    "local-brain": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/local-brain", "python", "-m", "local_brain.mcp_server"]
    }
  }
}
```

Or if published to PyPI:

```json
{
  "mcpServers": {
    "local-brain": {
      "command": "uvx",
      "args": ["local-brain-mcp"]
    }
  }
}
```

### What Gets Eliminated

| Component | LOC | Fate |
|-----------|-----|------|
| `cli.py` (Click CLI) | 303 | **Removed** — Claude Code is the UI |
| `SKILL.md` | 303 | **Removed** — MCP tool description replaces it |
| `plugin.json` + marketplace | ~50 | **Removed** — MCP server registration replaces it |
| `models.py` model selection | 295 | **Simplified** — still useful for auto-select, but CLI flags gone |
| `smolagent.py` (tools + agent) | 770 | **Kept as-is** — this is the core value |
| `security.py` | 259 | **Kept as-is** — still needed for path jailing |

From ~1700 LOC to ~1100 LOC, with the MCP server being ~30 LOC.

### Why This Works

1. **Claude Code already knows how to call MCP tools** — no skill/prompt engineering needed
2. **The agent loop runs entirely inside the MCP call** — Claude sends one tool call, gets one result back
3. **Zero Claude API tokens consumed** during the agent's exploration — only the final result enters Claude's context
4. **smolagents handles the hard part** — multi-step reasoning, tool execution, sandboxing
5. **LiteLLM routing can be added inside** — swap `LiteLLMModel` for a routed version, transparent to Claude

### Hybrid Setup (MCP for Everything)

```json
{
  "mcpServers": {
    "local-brain": {
      "command": "uvx",
      "args": ["local-brain-mcp"],
      "comment": "Multi-step agent loop for complex exploration"
    },
    "ollama": {
      "command": "npx",
      "args": ["-y", "ollama-mcp"],
      "comment": "Single-shot queries — fast, no agent overhead"
    }
  }
}
```

Claude Code decides which to use:
- **Complex exploration** → `run_agent("Trace the auth flow end-to-end")`
- **Quick question** → `ollama_chat("What does this function return?")`

---

## Decision Needed

1. ~~Keep local-brain as-is~~ — CLI/skill approach works but is more plumbing than needed
2. ~~Add ollama-mcp alongside~~ — still useful for single-shot, but doesn't replace the agent loop
3. **Evolve local-brain into an MCP server (recommended)** — keep the agent loop, drop the CLI/skill wrapper
4. ~~Replace with Claude-does-everything~~ — defeats the cost/privacy purpose

**Option 3 is the clear path.** The agent loop (smolagents CodeAgent) is the unique value. Everything else is replaceable plumbing. Re-packaging as an MCP server:
- Eliminates ~600 LOC of CLI/skill/plugin boilerplate
- Makes the agent loop callable from any MCP client (Claude Code, Cursor, etc.)
- Keeps zero-cost local execution
- Opens the door to LiteLLM routing inside the agent

---

## References

- [ollama-mcp](https://github.com/rawveg/ollama-mcp) — MCP Server exposing Ollama SDK
- [litellm-agent-mcp](https://github.com/BerriAI/litellm-agent-mcp) — MCP Server for 100+ LLMs via LiteLLM
- [LiteLLM MCP Docs](https://docs.litellm.ai/docs/mcp) — LiteLLM's MCP Gateway
- [Claude Code + MCP Tutorial](https://docs.litellm.ai/docs/tutorials/claude_mcp) — Connecting MCP servers to Claude Code
- [Connecting Claude Code to Local LLMs](https://medium.com/@michael.hannecke/connecting-claude-code-to-local-llms-two-practical-approaches-faa07f474b0f) — Two approaches (proxy vs direct)
- [Run Claude Code with Local Models](https://medium.com/@luongnv89/run-claude-code-on-local-cloud-models-in-5-minutes-ollama-openrouter-llama-cpp-6dfeaee03cda) — Ollama v0.14+ native Anthropic API
- [Smolagents Multi-Agent Docs](https://huggingface.co/docs/smolagents/en/examples/multiagents) — managed_agents orchestration
- [LiteLLM Ollama Provider](https://docs.litellm.ai/docs/providers/ollama) — LiteLLM + Ollama configuration
- [LiteLLM Router/Proxy Config](https://docs.litellm.ai/docs/proxy/configs) — Routing and fallback setup
