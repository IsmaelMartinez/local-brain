# 006: Project Reframing — Honest Competitive Analysis & Strategic Options

**Status:** Research
**Date:** 2026-02-21
**Context:** Deep research into the full landscape of tools that give local LLM models the ability to explore code. Corrects the earlier assumption that "nobody does this." Includes verified deep-dives into every named competitor.

---

## The Original Assumption (Wrong)

> "No library provides a lightweight, ready-to-use set of code exploration tools for local LLM agents. This is genuinely surprising."

This was true in mid-2024. **It is false as of February 2026.** The landscape grew — but not as much as it first appeared. Many "competitors" are paper tigers on closer inspection.

---

## What Actually Exists (February 2026)

### Tier 1: Serious CLI Competitors

These are real, actively maintained projects with substantial communities.

| Tool | Stars | Ollama | File Tools | Code Intelligence | Setup |
|------|-------|--------|------------|-------------------|-------|
| **OpenCode** (anomalyco) | 108k | `ollama launch opencode` | read, write, edit, grep, glob, bash, patch, webfetch | ripgrep search. Experimental LSP tool. **No AST-aware search.** tree-sitter only used internally for bash safety parsing. | Single binary. Zero config. |
| **Aider** | 39k | `OLLAMA_API_BASE` env var | Multi-file read/edit, auto-commit | tree-sitter + PageRank repo-map | `pip install aider-chat` |
| **Goose** (Block/Linux Foundation) | 27k | Guided setup | read/write, bash, git, DB, browser | MCP extensible | Desktop app or CLI |
| **local-brain** (us) | Tiny | Native | 9 tools (file, git, search) | **AST-aware search** (grep-ast + tree-sitter), definition extraction | `pip install local-brain` |

**Note on OpenCode:** There are two projects with this name. The original `opencode-ai/opencode` (Go, ~11k stars) was **archived September 2025**. Its successor is **Crush** by Charmbracelet. The active 108k-star project is `anomalyco/opencode` (TypeScript, backed by SST/Y Combinator) — a completely different codebase. `ollama launch opencode` points to the anomalyco version.

**OpenCode's limitations with local models:** Requires 24+ GB VRAM for reasonable performance. Designed for cloud models (Claude, GPT-4) first; local is a supported-but-secondary path. Local models perform significantly worse in OpenCode's complex tool-calling flows.

### Tier 1.5: The "Small Ollama CLI" Projects (Paper Tigers)

These were flagged as competitors in initial research. **On deep inspection, none are real threats.**

#### ollama-code (tcsenpai) — 304 stars, abandoned

**Not original code.** It is a fork of Qwen Code, which is a fork of Google Gemini CLI, with the API endpoint changed to point at localhost. tcsenpai's actual contributions: ~3 commits ("forked to ollama-code", "optimizations and / commands", "fixed hot reload of models"). The other 11 commits are from upstream Qwen Code authors.

| Fact | Detail |
|------|--------|
| Language | TypeScript (inherited from Gemini CLI) |
| Stars | 304 (from initial "Gemini CLI but local!" hype) |
| npm downloads | ~86/week |
| Last commit | August 6, 2025 (6+ months ago) |
| Issues filed | 0. Ever. No community. |
| AST/tree-sitter | No |
| Path jailing | No |
| Sensitive file blocking | No |
| Original code | ~3 commits. Everything else inherited. |

**The one independent review** (Fresh/Brewed blog, August 2025): Tool was extremely slow — over 7 hours without writing files with Qwen3. ~7 minutes just to add a comment to a README. Created files with "@" symbols in filenames (parsing bug). Author concluded: "I really cannot see why I would switch to it."

**Verdict: Do not migrate to this. It is worse than local-brain in every measurable dimension.**

#### ollama-code-cli (VigyatGoel) — 11 stars, weekend project

| Fact | Detail |
|------|--------|
| Language | Python |
| Stars | 11 |
| Created | August 30, 2025 |
| Last code change | September 6, 2025 (then only README updates) |
| Tools | 6 total: read_file, write_file, execute_code, list_files, run_command, run_python_file |
| AST/tree-sitter | No |
| Code search | None whatsoever |
| Path jailing | No |
| Sensitive file blocking | No |
| Test suite | Not found |

**Verdict: A weekend project with 6 basic tools and no code intelligence. Not a competitor.**

#### cli-code-agent (BlueCentre) — 1 star, archived

| Fact | Detail |
|------|--------|
| Stars | 1 |
| Status | **Archived** (June 21, 2025). Read-only. Dead. |
| Code origin | Self-described as "99.95% built by LLM models" |
| Model focus | Google AI Studio default, not Ollama-first |

**Verdict: Dead. Not a competitor.**

### Tier 2: IDE-Based — Same Problem, Different Form Factor

| Tool | Stars | Ollama | Notes |
|------|-------|--------|-------|
| **Continue.dev** | Large | First-class | VS Code/JetBrains. Context providers, agent mode, fully offline. |
| **Cline / Roo Code** | 22k | Yes | VS Code. Full file r/w, terminal, MCP. Local models struggle with complexity. |
| **Void Editor** | Growing | Auto-detects | VS Code fork with AI built in. Agent mode. |
| **Crush** (Charmbracelet) | Growing | Via OpenAI-compat config | Go. Successor to original OpenCode. Reports of significant tool calling issues with local models. |

### Tier 3: Platforms & Frameworks

| Tool | What It Is | Ollama | Why Not a Direct Competitor |
|------|-----------|--------|---------------------------|
| **Deep Agents** (LangChain) | LangGraph agent with file tools | Via `langchain-ollama` | Heavy (full LangChain stack). grep is literal-only. No AST. No tree-sitter. No symbol extraction. Ollama is second-class. Assumes Claude Sonnet 4-class reasoning. |
| **Composio** | SaaS API integration platform | Via MCP bridge only | Cloud-dependent. Requires API key. Old local tools deprecated. New SDK routes everything through `backend.composio.dev`. No self-hosting. No offline mode. Different problem entirely. |
| **LiteLLM** | LLM routing/proxy layer | N/A | **Zero tools. Zero agent logic. Zero tool execution. Zero codebase awareness.** Just translates API calls between 100+ providers. Wrong layer entirely. |
| **Open Interpreter** | General-purpose computer control | Yes | Broader scope. Not code-exploration-specific. |
| **Plandex** | Multi-step coding planner | Yes | Heavy. Needs 32GB+ RAM. tree-sitter maps but overkill. |

### Tier 4: MCP Ecosystem

MCP servers for code exploration exist but face a critical gap:

| Server | What It Provides |
|--------|-----------------|
| **@modelcontextprotocol/server-filesystem** | read/write/search files, directory ops, configurable sandboxing |
| **mcp-server-git** | status, diff, log, commit, branch, checkout, show |
| **mcp-server-tree-sitter** | AST parsing, symbol extraction, dependency analysis, 20+ languages |
| **code-index-mcp** | tree-sitter + ripgrep/ugrep combined. 7 languages. |

**Critical limitation:** Ollama has **no native MCP client support** (issue #7865, open 15+ months). Third-party bridges (ollmcp, mcphost, dolphin-mcp) exist but add friction. LM Studio has native MCP since v0.3.17. Until Ollama ships native MCP, these servers are inaccessible to Ollama users without bridging.

### Ollama's Own Evolution

As of January-February 2026:
- **`ollama launch`** (v0.15+, confirmed real): One command to set up OpenCode, Codex, Droid, or Goose with local models. Interactive model selection. Auto-configuration.
- **Anthropic Messages API compatibility** (v0.14+): Claude Code can run against Ollama-served models.
- Ollama is evolving from "model server" toward "agent platform," but native MCP support is still missing.

---

## Honest Differentiators (What We Actually Have)

After deep-diving every competitor:

### 1. AST-Aware Code Search (Real Differentiator)

`search_code` (grep-ast + tree-sitter) shows matches with structural context — which function/class a match lives in.

- **OpenCode does NOT have this.** Uses ripgrep (text regex only). tree-sitter is only used internally for bash command safety parsing, not for code search.
- **Aider uses tree-sitter** but for repo-map (PageRank-based file ranking), not for search-with-context.
- **ollama-code, ollama-code-cli, cli-code-agent** — none have any form of AST awareness.
- **MCP has `mcp-server-tree-sitter`** but Ollama can't use MCP natively.

**local-brain is the only lightweight CLI that provides AST-aware code search to Ollama models.**

### 2. Definition Extraction (Real Differentiator)

`list_definitions` extracts class/function signatures with docstrings. 11 languages via tree-sitter.

None of the small competitors have this. OpenCode's experimental LSP tool can do similar things but requires running language servers. Aider's repo-map extracts definitions but uses them for context ranking, not as a callable tool.

### 3. Extreme Minimalism (Real Differentiator)

~1,770 lines of Python across 5 files. A developer can read the entire codebase in 30 minutes.

| Project | Size | Readability |
|---------|------|-------------|
| **local-brain** | ~1,770 LOC Python | Read in 30 minutes |
| **OpenCode** (anomalyco) | 100k+ LOC TypeScript | Days to understand |
| **Aider** | Thousands of files | Complex architecture |
| **Goose** | Rust binary | Requires Rust knowledge |
| **ollama-code** | Inherited Gemini CLI (huge TypeScript) | Impossible to understand what's original |

**This is the actual moat** — not features, but *comprehensibility*. Someone who wants to understand, fork, and customize has no lighter option.

### 4. Security by Default (Minor Differentiator)

Path jailing, sensitive file blocking (.env, .pem, .key, id_*), output truncation, sandboxed execution.

- **ollama-code**: No path jailing, no sensitive file blocking.
- **ollama-code-cli**: Permission prompts only. No jailing.
- **cli-code-agent**: Had workspace restriction + dangerous command blocking, but the project is dead.
- **OpenCode**: Sandbox execution via Docker/Podman, but no sensitive file blocking.

### 5. Smart Model Selection (Temporary Differentiator)

Tiered model discovery, compatibility testing, blocking known-broken models (qwen2.5-coder, deepseek-r1, llama3.2:1b). No other small project does this. OpenCode relies on `ollama launch` to handle model selection.

### 6. Local-First Design (Philosophical Differentiator)

local-brain is designed for local models from day one. Every tool, every timeout, every output limit is tuned for 4-8k context windows and slower inference. OpenCode, Aider, and Goose all assume cloud-model capabilities as the primary path; local is a secondary/degraded mode.

---

## Feature-by-Feature Comparison (Verified)

| Feature | local-brain | ollama-code (tcsenpai) | ollama-code-cli | OpenCode (anomalyco) | Aider |
|---------|-------------|------------------------|-----------------|---------------------|-------|
| **Original code** | Yes (1,770 LOC) | No (rebadged Gemini CLI) | Yes (~300 LOC) | Yes (100k+ LOC) | Yes |
| **AST-aware search** | Yes (grep-ast + tree-sitter) | No | No | No (ripgrep only) | tree-sitter for repo-map |
| **Definition extraction** | Yes (tree-sitter, 11 langs) | No | No | Experimental LSP | Via repo-map |
| **Path jailing** | Yes | No | No | No | N/A |
| **Sensitive file blocking** | Yes | No | No | No | .gitignore respect |
| **Output truncation** | Yes (200 lines / 20k chars) | Unknown | No | Unknown | Yes |
| **Model compatibility checking** | Yes (tiered, blocks broken models) | No | No | No | Model metadata DB |
| **Interactive multi-turn** | Single-shot | Yes (inherited REPL) | Yes | Yes | Yes |
| **Sandbox execution** | smolagents LocalPythonExecutor | Docker/Podman option | No | Docker/Podman | N/A |
| **Test suite** | Yes (963 LOC) | Inherited (Vitest) | Not found | Yes (large) | Yes (large) |
| **Actively maintained** | Yes | No (Aug 2025) | No (Sep 2025) | Yes (yesterday) | Yes |
| **Stars** | Tiny | 304 (hollow) | 11 | 108k | 39k |

---

## Strategic Options

### Option A: Accept the Niche — "The Minimal One"

**Positioning:** "The simplest possible code exploration toolkit for Ollama — when OpenCode and Aider are more than you need."

Target audience: Developers who want something they can read in 30 minutes, understand completely, and modify. Educators. People who don't want 108k-star projects with hidden complexity.

**Pros:** Honest. Defensible. Low maintenance.
**Cons:** Small audience. Hard to grow.

### Option B: Become the Toolkit — Extract the Tools

**Positioning:** "AST-aware code exploration tools for any Python agent framework."

Extract `search_code`, `list_definitions`, and the security layer into a standalone `local-brain-tools` package. Let smolagents, LangChain, CrewAI, or custom agents use them. The agent loop is commodity; the tree-sitter tools are the value.

**Pros:** Unique angle. No competitor offers extractable AST tools as a library. Composable. Other projects could depend on us.
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

**Positioning:** "The best MCP server for AST-aware code exploration."

Wrap our tools as an MCP server. Every MCP client (LM Studio, Claude Code, ollmcp, mcphost) gets our AST-aware search and definition extraction. Ride the MCP ecosystem wave. **Especially interesting because Ollama lacks native MCP** — when they ship it, we'd be ready.

**Pros:** Huge addressable market. MCP is growing fast. Our tools would be among the best MCP code servers. Complements (not replaces) the CLI.
**Cons:** Requires MCP implementation. Competes with `mcp-server-tree-sitter` directly.

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

**Positioning:** The project served its purpose as a learning exercise and research vehicle. Redirect users to OpenCode or Aider.

**Pros:** Honest. Frees up time.
**Cons:** Abandons real users and working code. Premature — the AST tools are genuinely unique.

---

## Recommendation

**No single option is obviously correct.** But some are clearly better than others:

- **Option A** (minimal niche) is the safe default — keep maintaining, be honest about positioning
- **Option B** (extract tools) is the most *interesting* — nobody ships AST code tools as a composable library
- **Option E** (learning/onboarding) is the most *differentiated* from the competitive field
- **Option D** (MCP server) is the highest *leverage* — especially with Ollama's MCP gap

**Options C and F are probably wrong** — C over-invests, F gives up prematurely when the AST differentiator is real.

**The honest answer:** local-brain is a good, small project in a space with one giant (OpenCode) and one strong incumbent (Aider). The small "ollama-code" clones are paper tigers — abandoned forks and weekend projects. The real differentiators are AST-aware search, minimalism, and local-first design. These are genuine and defensible. The question is how to leverage them.

---

## Full Competitive Reference (Verified)

### Serious CLI Competitors

- [OpenCode](https://github.com/anomalyco/opencode) — 108k stars. TypeScript. `ollama launch opencode`. ripgrep search, no AST. v1.2.10 released Feb 20, 2026.
- [Aider](https://github.com/paul-gauthier/aider) — 39k stars. Python. tree-sitter repo-map. Code editing focus.
- [Goose](https://github.com/block/goose) — 27k stars. Rust. Linux Foundation. MCP extensible.
- [Crush](https://github.com/charmbracelet/crush) — Go. Successor to original OpenCode. Tool calling issues with local models reported.

### Paper Tigers (Not Real Threats)

- [ollama-code](https://github.com/tcsenpai/ollama-code) — 304 stars. Rebadged Gemini CLI fork. TypeScript. 86 npm downloads/week. Abandoned Aug 2025. No AST, no security.
- [ollama-code-cli](https://github.com/vigyatgoel/ollama-code-cli) — 11 stars. Python. 6 basic tools. Weekend project. Last code Sep 2025.
- [cli-code-agent](https://github.com/BlueCentre/code-agent) — 1 star. Archived Jun 2025. 99.95% LLM-generated. Dead.

### IDE Tools with Ollama Support

- [Continue.dev](https://github.com/continuedev/continue) — VS Code/JetBrains. First-class Ollama.
- [Cline](https://github.com/cline/cline) / [Roo Code](https://github.com/RooVetGit/Roo-Code) — VS Code. Autonomous agent.
- [Void Editor](https://voideditor.com/) — VS Code fork. Auto-detects Ollama.

### Platforms / Frameworks (Not Direct Competitors)

- [Deep Agents](https://github.com/langchain-ai/deepagents) — LangChain. File tools but no AST. Literal-only grep. Heavy.
- [Composio](https://composio.dev/) — Cloud-dependent SaaS API integration. Not local. Not code exploration.
- [LiteLLM](https://github.com/BerriAI/litellm) — Pure routing layer. Zero tools. Wrong layer.
- [claude-flow](https://github.com/ruvnet/claude-flow) — Proxy hack for Claude Code. Fragile.

### MCP Servers for Code (Ollama Can't Use Natively)

- [mcp-server-filesystem](https://github.com/modelcontextprotocol/servers) — Official. File ops.
- [mcp-server-git](https://github.com/modelcontextprotocol/servers) — Official. Git ops.
- [mcp-server-tree-sitter](https://github.com/wrale/mcp-server-tree-sitter) — AST. 20+ languages.
- [code-index-mcp](https://github.com/johnhuang316/code-index-mcp) — tree-sitter + ripgrep.

### MCP Bridges for Ollama (Workarounds)

- [ollmcp](https://github.com/jonigl/mcp-client-for-ollama) — TUI client. Multi-server.
- [mcphost](https://github.com/mark3labs/mcphost) — Go CLI. Multi-provider.
- [dolphin-mcp](https://github.com/QuixiAI/dolphin-mcp) — Python. Multi-provider.

### Ollama's Own Direction

- `ollama launch` (v0.15+, confirmed) — one-command agent setup
- Anthropic Messages API compat (v0.14+)
- Native MCP support — still open issue (#7865), 15+ months and counting

### Previous Research in This Repository

- ADR-001 through ADR-006
- Research docs 001-005
