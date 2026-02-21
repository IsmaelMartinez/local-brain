# 006: Project Reframing — Honest Competitive Analysis & Strategic Options

**Status:** Research
**Date:** 2026-02-21
**Context:** Deep research into the full landscape of tools that give local LLM models the ability to explore code. Corrects the earlier assumption that "nobody does this."

---

## The Original Assumption (Wrong)

> "No library provides a lightweight, ready-to-use set of code exploration tools for local LLM agents. This is genuinely surprising."

This was true in mid-2024. **It is false as of February 2026.** The landscape exploded.

---

## What Actually Exists (February 2026)

### Tier 1: Direct CLI Competitors — Ollama + File/Code Tools

| Tool | Stars | Ollama | File Tools | Code Intelligence | Setup Complexity |
|------|-------|--------|------------|-------------------|-----------------|
| **OpenCode** | 95k | Native. `ollama launch opencode` | read/write, search, bash, LSP | LSP-powered intelligence | Single binary. Zero config. |
| **Aider** | 39k | Native. `OLLAMA_API_BASE` env var | Multi-file read/edit, auto-commit | tree-sitter + PageRank repo-map | `pip install aider-chat` |
| **Goose** (Block/Linux Foundation) | 27k | Native. Guided setup. | read/write, bash, git, DB, browser | MCP extensible | Desktop app or CLI |
| **ollama-code** (tcsenpai) | Small | Ollama-native (its identity) | Full tool_manager, file ops, MCP | MCP extensible | `npm install -g @tcsenpai/ollama-code` |
| **ollama-code-cli** (VigyatGoel) | Small | Native | File ops with permission system | Basic | `pip install ollama-code-cli` |
| **cli-code-agent** (PyPI) | Small | Native. `code-agent ollama chat` | File read, edit, command exec | Basic | `pip install cli-code-agent` |
| **local-brain** (us) | Tiny | Native | 9 tools (file, git, search) | AST-aware (grep-ast + tree-sitter) | `pip install local-brain` |

**Verdict:** OpenCode alone invalidates the "nobody does this" claim. It is a polished terminal CLI with Ollama support, file tools, and LSP-powered code intelligence. `ollama launch opencode` is a one-command experience.

### Tier 2: IDE-Based — Same Problem, Different Form Factor

| Tool | Stars | Ollama | Notes |
|------|-------|--------|-------|
| **Continue.dev** | Large | First-class | VS Code/JetBrains plugin. Context providers, agent mode, fully offline. |
| **Cline / Roo Code** | 22k | Yes | VS Code. Full file read/write, terminal, MCP. Local models struggle with complexity. |
| **Void Editor** | Growing | Auto-detects | VS Code fork with AI built in. Agent mode. |
| **Cursor / Windsurf** | Huge | Limited | Commercial IDEs. Local model support varies. |

### Tier 3: Platforms & Frameworks

| Tool | What It Is | Ollama | Why Not a Direct Competitor |
|------|-----------|--------|---------------------------|
| **Deep Agents** (LangChain) | LangGraph agent with file tools | Via `langchain-ollama` | Heavy (full LangChain stack). grep is literal-only. No AST. Ollama is second-class. |
| **Composio** | SaaS API integration platform | Via MCP bridge only | Cloud-dependent. Requires API key. Old local tools deprecated. Different problem. |
| **LiteLLM** | LLM routing/proxy layer | N/A | Zero tools. Zero agent logic. Just translates API calls between providers. |
| **Open Interpreter** | General-purpose computer control | Yes | Broader scope. Not code-exploration-specific. |
| **Plandex** | Multi-step coding planner | Yes | Heavy. Needs 32GB+ RAM. tree-sitter maps but overkill. |

### Tier 4: MCP Ecosystem

MCP servers for code exploration are mature and plentiful:

| Server | What It Provides |
|--------|-----------------|
| **@modelcontextprotocol/server-filesystem** | read/write/search files, directory ops, configurable sandboxing |
| **mcp-server-git** | status, diff, log, commit, branch, checkout, show |
| **mcp-server-tree-sitter** | AST parsing, symbol extraction, dependency analysis, 20+ languages |
| **code-index-mcp** | tree-sitter + ripgrep/ugrep combined. 7 languages. |
| **grep MCP servers** | Multiple options (local grep, remote grep.app) |

**But:** Ollama has no native MCP client support (issue #7865, open 15+ months). Third-party bridges exist (ollmcp, mcphost, dolphin-mcp) but add friction. LM Studio has native MCP since v0.3.17.

### Ollama's Own Evolution

As of January-February 2026:
- **`ollama launch`** (v0.15+): One command to set up OpenCode, Codex, Droid, or Goose with local models
- **Anthropic Messages API compatibility** (v0.14+): Claude Code can run against Ollama-served models
- **Built-in subagents and web search** (Feb 2026): Ollama itself is becoming an agent platform

---

## What Was Confirmed (Not Wrong)

### LiteLLM: Pure Routing, No Tools

LiteLLM is plumbing. It translates API calls between 100+ providers. It has:
- Zero file tools
- Zero agent loop
- Zero tool execution
- Zero codebase awareness

It's the wrong layer entirely. Could be used *inside* local-brain for provider flexibility, but doesn't replace any of our functionality.

### Composio: Cloud-Dependent, Different Problem

Composio connects agents to SaaS APIs (GitHub, Slack, Gmail) via managed OAuth. The old SDK had local file tools but they're deprecated. The new SDK routes everything through `backend.composio.dev`. Requires API key. No self-hosting. No offline mode. Solves a fundamentally different problem.

### Deep Agents: Heavy, No AST, Ollama Second-Class

Deep Agents provides similar file tools (ls, read_file, edit_file, glob, grep) but:
- grep is **literal text only** — no regex, no AST
- No tree-sitter, no symbol extraction, no language awareness
- Built on full LangChain stack (langchain-core, langchain-anthropic, langchain-google-genai mandatory)
- Requires Python >=3.11
- Ollama support requires extra packages and a sufficiently capable model
- Framework assumes Claude Sonnet 4-class reasoning

---

## Honest Differentiators (What We Actually Have)

After looking at every competitor, here's what local-brain genuinely offers that others don't (or do differently):

### 1. AST-Aware Code Search (Partial Differentiator)

`search_code` (grep-ast + tree-sitter) shows matches with structural context — which function/class a match lives in. This is genuinely useful.

**But:** Aider also uses tree-sitter (for repo-map with PageRank). OpenCode uses LSP. MCP has `mcp-server-tree-sitter` with 20+ languages. We're not alone here anymore, though we're the most lightweight option.

### 2. Definition Extraction (Moderate Differentiator)

`list_definitions` extracts class/function signatures with docstrings. 11 languages via tree-sitter.

**But:** LSP servers do this better. MCP tree-sitter servers do this. Aider's repo-map does this. The standalone simplicity is the differentiator, not the capability.

### 3. Extreme Minimalism (Real Differentiator)

~1,770 lines of Python across 5 files. A developer can read the entire codebase in 30 minutes. Compare:
- OpenCode: Massive Go codebase
- Aider: Thousands of files, complex architecture
- Goose: Rust binary, enormous scope
- Deep Agents: LangChain dependency tree

**This is the actual moat** — not features, but *comprehensibility*. Someone who wants to understand, fork, and customize has no lighter option.

### 4. Security by Default (Minor Differentiator)

Path jailing, sensitive file blocking, output truncation, sandboxed execution. Most competitors give full access or rely on the model to be well-behaved. Nice to have but not a buying decision.

### 5. Smart Model Selection (Temporary Differentiator)

Tiered model discovery, compatibility testing, blocking known-broken models. Useful today but will erode as Ollama improves its own model management.

---

## Strategic Options

### Option A: Accept the Niche — "The Minimal One"

**Positioning:** "The simplest possible code exploration toolkit for Ollama — when OpenCode and Aider are more than you need."

Target audience: Developers who want something they can read in 30 minutes, understand completely, and modify. People who don't want 95k-star projects with hidden complexity.

**Pros:** Honest. Defensible. Low maintenance.
**Cons:** Small audience. Hard to grow.

### Option B: Become the Toolkit — Extract the Tools

**Positioning:** "AST-aware code exploration tools for any Python agent framework."

Extract `search_code`, `list_definitions`, and the security layer into a standalone `local-brain-tools` package. Let smolagents, LangChain, CrewAI, or custom agents use them. The agent loop is commodity; the tree-sitter tools are the value.

**Pros:** Unique angle. No competitor offers extractable AST tools as a library. Composable.
**Cons:** Requires rearchitecting. Smaller market than a full CLI.

### Option C: Double Down on AST — Become the Code Intelligence Layer

**Positioning:** "The deepest local code understanding — not just grep, but structure."

Invest heavily in what competitors do poorly:
- Expand tree-sitter coverage beyond 11 languages
- Add call graph analysis (who calls what)
- Add dependency mapping (imports, requires)
- Add "explain this function's callers and callees"
- Make `list_definitions` output machine-readable for other tools

**Pros:** Genuine technical moat. Hard for competitors to replicate quickly.
**Cons:** Significant engineering investment. May over-engineer past the audience.

### Option D: Pivot to MCP — Become an MCP Server

**Positioning:** "The best MCP server for code exploration with local models."

Wrap our tools as an MCP server. Every MCP client (LM Studio, Claude Code, ollmcp, mcphost) gets our AST-aware search and definition extraction. Ride the MCP ecosystem wave.

**Pros:** Huge addressable market. MCP is growing fast. Our tools would be among the best MCP code servers.
**Cons:** Requires MCP implementation. Competes with `mcp-server-tree-sitter` directly. Loses the standalone CLI identity.

### Option E: Learning Tool — "Understand Before You Edit"

**Positioning:** "Read-only code exploration for learning and onboarding."

Every competitor focuses on *editing* code. We focus on *understanding* it. Add:
- `local-brain --summarize` — generate project overview
- `local-brain --explain src/auth/` — explain a module
- `local-brain --onboard` — guided tour of an unfamiliar codebase
- Interactive multi-turn exploration mode

**Pros:** Genuinely different niche. Competitors don't optimize for this. Junior devs and new team members are a real audience.
**Cons:** Narrow. Dependent on local model quality for explanations.

### Option F: Graceful Sunset

**Positioning:** The project served its purpose as a learning exercise and research vehicle. The landscape caught up. Redirect users to OpenCode or Aider.

**Pros:** Honest. Frees up time.
**Cons:** Abandons real users and working code.

---

## Recommendation

**No single option is obviously correct.** But some are clearly better than others:

- **Option A** (minimal niche) is the safe default — keep maintaining, be honest about positioning
- **Option B** (extract tools) is the most *interesting* — nobody ships AST code tools as a composable library
- **Option E** (learning/onboarding) is the most *differentiated* from the competitive field
- **Option D** (MCP server) is the highest *leverage* but highest effort

**Options C and F are probably wrong** — C over-invests, F gives up prematurely.

The honest answer: **local-brain is a good project in a crowded space.** The skill/plugin path was a dead end. The standalone path is viable but not unique. The real question is whether to stay minimal (A), extract value (B), find a niche (E), or ride MCP (D).

---

## Full Competitive Reference

### CLI Tools with Ollama + Code Access

- [OpenCode](https://github.com/opencode-ai/opencode) — 95k stars. Terminal CLI. LSP. `ollama launch opencode`.
- [Aider](https://github.com/paul-gauthier/aider) — 39k stars. Pair programmer. tree-sitter repo-map.
- [Goose](https://github.com/block/goose) — 27k stars. Autonomous agent. Linux Foundation.
- [ollama-code](https://github.com/tcsenpai/ollama-code) — Ollama-native CLI. Node.js.
- [ollama-code-cli](https://github.com/vigyatgoel/ollama-code-cli) — Python CLI. Tool calling.
- [cli-code-agent](https://pypi.org/project/cli-code-agent/) — Python CLI. Ollama chat.

### IDE Tools with Ollama Support

- [Continue.dev](https://github.com/continuedev/continue) — VS Code/JetBrains. First-class Ollama.
- [Cline](https://github.com/cline/cline) / [Roo Code](https://github.com/RooVetGit/Roo-Code) — VS Code. Autonomous agent.
- [Void Editor](https://voideditor.com/) — VS Code fork. Auto-detects Ollama.

### Platforms / Frameworks Evaluated

- [Deep Agents](https://github.com/langchain-ai/deepagents) — LangChain. File tools but no AST. Heavy.
- [Composio](https://composio.dev/) — SaaS API integration. Cloud-dependent. Not local.
- [LiteLLM](https://github.com/BerriAI/litellm) — Pure routing layer. Zero tools.
- [claude-flow](https://github.com/ruvnet/claude-flow) — Proxy hack. Fragile.

### MCP Servers for Code

- [mcp-server-filesystem](https://github.com/modelcontextprotocol/servers) — Official. File ops.
- [mcp-server-git](https://github.com/modelcontextprotocol/servers) — Official. Git ops.
- [mcp-server-tree-sitter](https://github.com/wrale/mcp-server-tree-sitter) — AST. 20+ languages.
- [code-index-mcp](https://github.com/johnhuang316/code-index-mcp) — tree-sitter + ripgrep.

### MCP Bridges for Ollama

- [ollmcp](https://github.com/jonigl/mcp-client-for-ollama) — TUI client. Multi-server.
- [mcphost](https://github.com/mark3labs/mcphost) — Go CLI. Multi-provider.
- [dolphin-mcp](https://github.com/QuixiAI/dolphin-mcp) — Python. Multi-provider.
- [ollama-mcp-bridge](https://github.com/jonigl/ollama-mcp-bridge) — FastAPI proxy.

### Ollama's Own Direction

- `ollama launch` (v0.15+) — one-command agent setup
- Anthropic Messages API compat (v0.14+)
- Native MCP support — still open issue (#7865), 15+ months

### Previous Research in This Repository

- ADR-001 through ADR-006
- Research docs 001-005
