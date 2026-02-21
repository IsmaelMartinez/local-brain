# 006: Project Reframing — Local Brain as Standalone Code Explorer

**Status:** Research
**Date:** 2026-02-21
**Context:** Extensive evaluation of skill packaging, WASM distribution, claude-flow, deepagents, and the broader agent tooling landscape.

---

## The Question We Kept Asking

> Can local-brain be useful as a skill/sub-agent called by Claude Code?

After thorough investigation, the answer is **no** — and that's the wrong question.

---

## Why the Skill/Sub-Agent Path Is a Dead End

### The Fundamental Contradiction

Claude Code already has native `Read`, `Write`, `Edit`, `Grep`, `Glob`, and `Bash` tools. Telling it to shell out to `local-brain "analyze this code"` adds a middleman that is:

- **Slower** — shell invocation + Ollama inference vs. native tool calls
- **Less capable** — local models vs. Claude for reasoning
- **Redundant** — reimplements tools the host agent already has

### Distribution Doesn't Help

| Approach | Verdict |
|----------|---------|
| **WASM** | Impossible — needs network (Ollama API), filesystem, subprocesses (git), native extensions (tree-sitter, grpcio) |
| **PyInstaller** | Per-platform binaries, messy to ship with a SKILL.md |
| **`uvx local-brain`** | Closest to viable, but doesn't solve the fundamental redundancy |
| **MCP server** | Adds protocol overhead, still redundant with host agent's tools |

### Existing Solutions We Evaluated

| Project | What It Does | Why Not |
|---------|-------------|---------|
| **claude-flow** (ruvnet, 14.3k stars) | Proxy-hijacks `ANTHROPIC_BASE_URL` to route Claude Code to Ollama via LiteLLM | Fragile hack. Reports of sub-agents falling back to Claude anyway. Massive scope (60+ agents, swarm orchestration, consensus algorithms). Alpha quality. |
| **deepagents** (LangChain, 9.5k stars) | Pre-built file tools (read, grep, glob, edit) + LangGraph agent loop | 48 dependencies including forced `langchain-anthropic` and `langchain-google-genai`. grep is literal-only (no regex, no AST). No equivalent to our `search_code` or `list_definitions`. Requires Python >=3.11. Ollama tool calling is fragile. |
| **aider** (paul-gauthier) | AI pair programmer CLI with Ollama support | Complete application, not a library. File tools are internal, not extractable. Different goal (code editing, not exploration). |
| **goose** (Block, 30k stars) | Autonomous coding agent with Ollama support | Rust binary, not a Python library. Not composable. |
| **LangChain FileToolkit** | Read, write, list, copy, delete, move, search | No grep, no glob, no AST. Missing the tools that matter for code exploration. |
| **smolagents** (HuggingFace) | Agent framework (what we already use) | Zero built-in file tools. We already wrote our own. |

### The Gap Nobody Fills

No library provides a **lightweight, ready-to-use set of code exploration tools** for local LLM agents. Specifically:

- **AST-aware code search** — our `search_code` (grep-ast + tree-sitter) shows matches with structural context (function/class boundaries). Nothing else does this.
- **Definition extraction** — our `list_definitions` (tree-sitter) extracts class/function signatures with docstrings across 11 languages. No library offers this.
- **Security-conscious file access** — path jailing, sensitive file blocking, output truncation. Most frameworks either give full access or require a sandbox runtime.

This is genuinely surprising. Ollama has 130k+ stars and millions of users, yet there is no standard "give your local model the ability to explore code" toolkit.

---

## The Reframing

### What Local Brain Is NOT

- Not a Claude Code skill or plugin
- Not a sub-agent to be called by a more capable model
- Not a framework or platform
- Not trying to compete with Claude, GPT-4, or any cloud model

### What Local Brain IS

**A standalone CLI that gives local Ollama models the ability to explore and understand codebases.**

Think of it as: **`ollama run` but with eyes** — the model can actually read your files, search your code, understand your project structure, and look at your git history. Without local-brain, Ollama models are blind — they can chat about code you paste in, but they can't explore.

### The Value Proposition (Reframed)

| Scenario | Why Local Brain |
|----------|----------------|
| **No API key** | `local-brain "explain this module"` — works with zero cloud accounts |
| **Offline** | Airplane, air-gapped environments, restricted networks |
| **Privacy** | Code never leaves your machine. Period. |
| **CI/CD** | Free code review in pipelines — no API costs at scale |
| **Learning** | Junior devs exploring unfamiliar codebases without burning API credits |
| **Triage** | Quick "what does this do" before deciding if you need Claude for deeper analysis |

### What Makes It Differentiated

1. **AST-aware search** — `search_code` uses grep-ast + tree-sitter to show matches with surrounding function/class context. No other local-model tool does this.

2. **Definition extraction** — `list_definitions` parses source files with tree-sitter and returns structured class/function signatures. 11 languages supported.

3. **Security by default** — path jailing, sensitive file blocking, output truncation, sandboxed execution. Not an afterthought.

4. **Smart model selection** — tiered model discovery with compatibility testing. Knows which Ollama models support tool calling and which don't. Blocks known-broken models.

5. **Zero configuration** — `local-brain "what does this project do"` in any git repo. No config files, no API keys, no setup beyond `ollama pull qwen3`.

---

## Revised Roadmap

### Keep (Core Strengths)

- [x] CLI UX — simple, fast, zero-config
- [x] AST-aware search (`search_code`)
- [x] Definition extraction (`list_definitions`)
- [x] Security model (path jail, sensitive files, truncation)
- [x] Smart model selection with tiered fallback
- [x] OpenTelemetry tracing

### Improve (Based on Research)

- [ ] **read_file pagination** — add `offset`/`limit` parameters instead of read-everything-then-truncate (stolen from deepagents, ~30 lines)
- [ ] **Large result eviction** — when tool output exceeds N tokens, return head+tail preview with a "use read_file with offset to see more" hint (~30 lines)
- [ ] **Expand file tools** — add `find_files` (glob with metadata) and `grep` (regex, not just AST-aware) as separate tools for when structural context isn't needed
- [ ] **Interactive mode** — multi-turn conversation instead of single-prompt-and-exit
- [ ] **Streaming output** — show model thinking in real-time instead of waiting for full response

### Drop (Dead Ends)

- ~~Claude Code skill/plugin packaging~~
- ~~WASM distribution~~
- ~~Sub-agent delegation from cloud models~~
- ~~MCP server bridge~~
- ~~Framework dependencies (deepagents, LangChain)~~

### Explore (Future)

- **Pipe-friendly mode** — `git diff | local-brain "review this"` — accept stdin as context
- **Project summaries** — `local-brain --summarize` — generate a cached project overview the model can reference
- **Custom tool loading** — let users drop Python files in `.local-brain/tools/` to extend the agent
- **`brew install local-brain`** / **`uv tool install local-brain`** — easy installation for non-Python users

---

## The Competitive Landscape (Honest Assessment)

### Direct Competitors

| Tool | How It Differs |
|------|---------------|
| **aider** | Code editing focus, not exploration. Heavier. More mature. Different goal. |
| **goose** (Block) | Full autonomous agent. Rust binary. Enormous scope. Not lightweight. |
| **continue.dev** | IDE plugin, not CLI. Cloud-model focused. |
| **Cursor/Windsurf** | Full IDEs. Not CLI. Not local-only. |
| **`ollama run`** | No file access. Blind to your codebase. This is the gap we fill. |

### Why This Gap Exists

1. **Ollama focuses on model serving**, not agent tooling. Their philosophy is "run models" not "build agents."
2. **Agent frameworks target cloud models** — LangChain, smolagents, CrewAI all assume GPT-4/Claude-class capabilities. Local models with 4-8k context windows and weaker instruction following are an afterthought.
3. **Code exploration is hard to do well** — naive grep is easy; AST-aware search with tree-sitter across 11 languages is not. Most projects punt on this.
4. **The "local-first" market is underserved** — most developer tooling assumes cloud connectivity and API keys.

---

## Decision

**Local Brain is a standalone CLI for local code exploration with Ollama.** It is not a skill, not a sub-agent, not a framework. Its differentiation is:

1. AST-aware code intelligence (grep-ast + tree-sitter)
2. Security-conscious design (path jailing, sensitive file blocking)
3. Smart local model management (tiered selection, compatibility checking)
4. Zero-config simplicity

The skill/plugin exploration was valuable research but confirmed that the standalone path is the right one. Focus energy here.

---

## References

- [claude-flow](https://github.com/ruvnet/claude-flow) — Proxy-based multi-model routing for Claude Code
- [deepagents](https://github.com/langchain-ai/deepagents) — LangChain's file-tool-equipped agent framework
- [aider](https://github.com/paul-gauthier/aider) — AI pair programmer CLI
- [goose](https://github.com/block/goose) — Block's autonomous coding agent
- [MCP filesystem server](https://github.com/modelcontextprotocol/servers) — Reference file tools over MCP
- ADR-001 through ADR-006 in this repository
- Research docs 001-005 in this repository
