# 007: Rust Rewrite Plan — Single Binary with ollama-rs

**Status:** Research
**Date:** 2026-02-21
**Context:** Following the competitive analysis in 006, this document evaluates mature compiled-language alternatives to smolagents, deep-dives into MCPHost as prior art, and proposes a concrete Rust rewrite plan using `ollama-rs`. Goal: ship `local-brain` as a single binary with zero runtime dependencies.

---

## Why Consider a Rewrite

The Python implementation has two distribution problems:

1. **Python runtime required.** `pip install local-brain` works for developers but not for end users who don't have Python. PyInstaller bundles exist but are fragile (150MB+, slow startup, SIGALRM not available on Windows).
2. **smolagents is heavyweight.** smolagents pulls in PyTorch, transformers, and HuggingFace Hub — ~1GB of dependencies — even though local-brain only uses the tool-calling agent loop.

The AST differentiators (`search_code`, `list_definitions`) depend on grep-ast and tree-sitter, which are Python and C libraries. They work well but are a permanent dependency on the Python ecosystem.

A Rust binary would be: `curl -L .../local-brain | install -m 755 /dev/stdin /usr/local/bin/local-brain`. Zero dependencies. 5MB binary. Sub-100ms startup.

---

## Compiled Language Framework Landscape (February 2026)

### Rust Options

| Framework | Stars | Ollama | Agent Loop | Verdict |
|-----------|-------|--------|------------|---------|
| **Rig** | 6.1k | Native (first-class provider) | Multi-turn, configurable depth | Best full-featured option |
| **ollama-rs** | 986 | IS the Ollama client | Coordinator pattern | Best minimal option |
| **graniet/llm** | 310 | Yes | Reactive agents | Smaller community |
| **langchain-rust** | 1.2k | Partial (tool calling unclear) | Yes | Ollama tool-calling story unclear |
| **AutoAgents** | 385 | Via mistral.rs | ReAct | Ambitious but early |
| **llm-chain** | 1.6k | Unknown | Yes | **Dead** — last release May 2023 |

### Go Options

| Framework | Stars | Ollama | Agent Loop | Verdict |
|-----------|-------|--------|------------|---------|
| **Eino** (ByteDance) | 9.7k | Native ChatModel | ReAct graph | Best Go option, ByteDance-backed |
| **LangChainGo** | 8.7k | Yes | Conversational agent | 1,711 dependents, Oct 2025 last release |
| **go-openai** | 10.6k | Via compat endpoint | DIY (~100 lines) | Client only, no agent abstractions |

### MCP SDKs (both production-ready for writing MCP servers)

- **Rust**: Official `rmcp` — 3k stars, v0.16.0, Feb 2026. stdio + streamable HTTP.
- **Go**: Official `go-sdk` (3.9k stars) + community `mcp-go` (8.2k stars, 400+ dependents).

---

## MCPHost — Deep Dive as Prior Art

[MCPHost](https://github.com/mark3labs/mcphost) (Go, 1.6k stars, MIT) is the most direct prior art: a Go binary that connects LLMs (including Ollama) to tools via MCP. Backed by the same team as `mcp-go`.

### Architecture

```
+------------------+       +-------------------+       +------------------+
|   LLM Provider   | <---> |    MCPHost (Host)  | <---> |   MCP Servers    |
| (Ollama/Claude/  |       |   - Agent Loop     |       | (stdio/SSE/HTTP/ |
|  OpenAI/Gemini)  |       |   - Tool Manager   |       |  builtin)        |
+------------------+       +-------------------+       +------------------+
```

Uses **Eino** (ByteDance's Go agent library) under the hood as the provider abstraction layer.

### What MCPHost Does Well

- **Polished CLI**: Charmbracelet (Bubble Tea + Lip Gloss) terminal UI, spinners, streaming display, ESC to cancel.
- **Multi-provider**: Ollama, Anthropic, OpenAI, Gemini via the same interface.
- **Three execution modes**: Interactive REPL, single-shot, YAML script mode.
- **Session persistence**: Save/load conversation JSON.
- **Tool approval**: Configurable per-tool approval gate before execution.
- **Streaming with deferred tool calls**: Accumulates tool call chunks until EOF, then executes — prevents partial tool invocations.
- **4 builtin in-process tools**: `bash`, `fetch`, `todo`, `filesystem`.
- **Go SDK**: `sdk.New()` → `host.Prompt()` for programmatic embedding.
- **Ollama GPU→CPU fallback**: Automatically falls back to CPU if VRAM insufficient.

### What MCPHost Cannot Do For Us

**Tools must be MCP servers.** You cannot register a Rust function as a tool — you must stand up a stdio or HTTP MCP server. The 4 builtin servers show it's possible in-process, but every tool requires a full MCP server implementation (JSON-RPC protocol, capability negotiation, `ListTools`, `CallTool` handlers).

For local-brain's 9 tightly-coupled tools (which need to share path-jailing logic and security config), this is unnecessary indirection. MCP is the right architecture when tools need to be swappable by users across multiple clients — not when tools are internal implementation details of a single CLI.

**Useful patterns to steal from MCPHost:**
1. Namespaced tool registry (`server__toolname`) — prevents collisions
2. Deferred-tool-call streaming — execute only on EOF
3. YAML frontmatter script mode — portable, self-contained agent definitions
4. ESC key cancellation integrated into the agent loop

**Verdict:** MCPHost solves "connect any LLM to any MCP server." local-brain needs "single CLI with built-in tools." Wrong fit, right inspiration.

---

## Recommended Approach: Rust + ollama-rs

### Why ollama-rs over Rig

**ollama-rs** is the Ollama client. It is what Rig's Ollama provider wraps internally. For a project that is Ollama-only by design (local-first, no cloud), using ollama-rs directly is the right level of abstraction:

- No framework lock-in (Rig's abstractions don't help when you only support one provider)
- Lighter dependency tree
- `#[function]` macro makes tool definition as ergonomic as smolagents' `@tool`
- Coordinator gives you the agent loop out of the box
- v0.3.4, active as of February 2026

**If multi-provider support is ever needed later, migrate to Rig.** That's a one-day refactor, not a rewrite.

### Key Crates

| Crate | Purpose |
|-------|---------|
| `ollama-rs` | Ollama client, Coordinator agent loop, `#[function]` tool macro |
| `clap` | CLI argument parsing (`derive` feature) |
| `tokio` | Async runtime |
| `tree-sitter` | AST parsing (native Rust — tree-sitter's home language) |
| `tree-sitter-*` | Grammar crates: `tree-sitter-python`, `tree-sitter-rust`, `tree-sitter-go`, `tree-sitter-javascript`, `tree-sitter-typescript`, `tree-sitter-java`, `tree-sitter-c`, `tree-sitter-cpp` |
| `walkdir` | Recursive directory traversal |
| `glob` | File glob pattern matching |
| `reqwest` | HTTP calls to Ollama `/api/tags` for model discovery |
| `serde` / `serde_json` | JSON serialization |
| `anyhow` | Error handling |
| `colored` | Terminal color output |

**No `langchain-rust`, no `rig`, no `llm`.** Just ollama-rs + tree-sitter + clap.

---

## Project Structure

```
local-brain-rs/
├── Cargo.toml
├── src/
│   ├── main.rs           # Entry point, clap CLI dispatch
│   ├── agent.rs          # ollama-rs Coordinator setup, model selection
│   ├── models.rs         # Ollama model discovery (GET /api/tags), tiered selection
│   ├── security.rs       # Path jailing, sensitive file blocking, truncation
│   └── tools/
│       ├── mod.rs        # Tool registration, ALL_TOOLS list
│       ├── file.rs       # read_file, list_directory, file_info
│       ├── git.rs        # git_diff, git_status, git_log, git_changed_files
│       └── code.rs       # search_code (AST-aware), list_definitions
```

### Tool Definition (ollama-rs #[function] macro)

```rust
// tools/file.rs
use ollama_rs::tool::function;

#[function]
/// Read the contents of a file. Returns file contents as text.
/// Args:
///   file_path: Path to the file to read (relative to working directory)
pub async fn read_file(file_path: String) -> Result<String, String> {
    let path = security::jail_path(&file_path)?;
    let content = tokio::fs::read_to_string(&path)
        .await
        .map_err(|e| e.to_string())?;
    Ok(security::truncate(&content))
}
```

### Agent Loop (ollama-rs Coordinator)

```rust
// agent.rs
use ollama_rs::coordinator::Coordinator;
use ollama_rs::Ollama;

pub async fn run(prompt: &str, model: &str) -> anyhow::Result<String> {
    let ollama = Ollama::default(); // localhost:11434
    let coordinator = Coordinator::new(ollama, model.to_string())
        .add_tool(read_file)
        .add_tool(list_directory)
        .add_tool(file_info)
        .add_tool(git_diff)
        .add_tool(git_status)
        .add_tool(git_log)
        .add_tool(git_changed_files)
        .add_tool(search_code)
        .add_tool(list_definitions);

    let response = coordinator.chat(prompt).await?;
    Ok(response)
}
```

---

## The grep-ast Replacement

`search_code` in the Python version uses grep-ast, which finds regex matches in source files and then uses tree-sitter to display the match with its containing function/class as context. This is the key differentiator.

In Rust, this is native:

```
1. Regex match → get matching line numbers (use the `regex` crate)
2. Parse file with tree-sitter → get AST
3. For each matching line:
   a. Walk AST upward from the matching node
   b. Find the nearest ancestor that is a function_definition, class_definition,
      method_definition, etc.
   c. Collect that ancestor's entire source range
4. Format: show the function/class header + the matching lines highlighted
```

This is ~200-300 lines of tree-sitter traversal. Since tree-sitter is native Rust (it's literally written in Rust), this is more ergonomic in Rust than in Python via the C bindings that grep-ast uses.

**Language support:** All 11 languages local-brain currently supports (`tree-sitter-python`, `tree-sitter-javascript`, `tree-sitter-typescript`, `tree-sitter-rust`, `tree-sitter-go`, `tree-sitter-java`, `tree-sitter-c`, `tree-sitter-cpp`, `tree-sitter-ruby`, `tree-sitter-c-sharp`, `tree-sitter-kotlin`) have official Rust grammar crates.

---

## What Maps Directly (Easy)

| Python | Rust | Notes |
|--------|------|-------|
| `@tool def read_file()` | `#[function] fn read_file()` | Direct equivalent |
| `subprocess.run(["git", ...])` | `std::process::Command::new("git")` | Same concept |
| `os.path.realpath()` | `std::fs::canonicalize()` | Path jailing |
| `glob.glob()` | `glob` crate | Same API shape |
| `os.walk()` | `walkdir` crate | Same concept |
| `requests.get()` | `reqwest` | Same concept |
| Click CLI | `clap` derive macros | More ergonomic in Rust |
| smolagents agent loop | ollama-rs Coordinator | Direct replacement |
| OTEL tracing | `tracing` + `tracing-opentelemetry` | Optional, add later |

## What Needs Reimplementing (Non-trivial)

| Python | Rust | Effort |
|--------|------|--------|
| `grep-ast` TreeContext | Custom tree-sitter traversal | ~200-300 lines |
| `tree-sitter-language-pack` | Individual grammar crates | Just Cargo deps |
| SIGALRM timeouts | `tokio::time::timeout()` | ~10 lines, actually simpler |
| `smolagents` agent loop | `ollama-rs` Coordinator | ~50 lines |

**Total estimate:** ~2,000-2,500 lines of Rust for feature parity with the current ~1,770 lines of Python.

---

## Distribution

```bash
# Build
cargo build --release
# Result: target/release/local-brain (5-8 MB, statically linked)

# Install
cargo install local-brain

# Or one-liner
curl -L https://github.com/.../releases/download/v1.0.0/local-brain-linux-x86_64 \
  | install -m 755 /dev/stdin /usr/local/bin/local-brain
```

Cross-compilation targets via `cross`:
- `x86_64-unknown-linux-musl` (static Linux binary)
- `aarch64-unknown-linux-musl` (ARM64 Linux, Raspberry Pi, etc.)
- `x86_64-apple-darwin` (Intel Mac)
- `aarch64-apple-darwin` (Apple Silicon)
- `x86_64-pc-windows-gnu` (Windows)

GitHub Actions CI produces all 5 binaries on tag push.

---

## MCP Server Path (Future)

If local-brain later wants to expose its tools to Claude Code, LM Studio, or other MCP clients, the official `rmcp` SDK (v0.16.0, Feb 2026) makes this straightforward:

```rust
// Add to Cargo.toml: rmcp = "0.16"
// Wrap existing tool functions as MCP tools — no rewrite needed
```

The Rust rewrite positions us well for this: the same `search_code` and `list_definitions` functions could be exposed both via the ollama-rs Coordinator (direct agent mode) and via rmcp (MCP server mode). Two interfaces, one implementation.

---

## Go Alternative

If Rust feels like too much, **Eino + Go** is the pragmatic alternative:
- `smacker/go-tree-sitter` for AST (Go bindings to the tree-sitter C library)
- `cloudwego/eino` for the agent loop with native Ollama support
- Similar single-binary distribution story
- Faster to write (~1.5x faster development vs Rust)
- Downside: Go's tree-sitter bindings are less ergonomic than Rust's native crates

**Recommendation:** Rust if tree-sitter code quality matters (it's the main differentiator); Go if development speed matters more.

---

## Strategic Rationale

This rewrite directly addresses the distribution problem while preserving the real differentiators:

| Differentiator | Python | Rust |
|----------------|--------|------|
| AST-aware search | grep-ast (Python C bindings) | Native tree-sitter (better) |
| Definition extraction | tree-sitter-language-pack | Same tree-sitter, native |
| Path jailing + security | `os.path.realpath()` | `std::fs::canonicalize()` (same) |
| Local-first design | smolagents + Ollama | ollama-rs (more direct) |
| **Minimalism / readability** | ~1,770 LOC | ~2,000-2,500 LOC (comparable) |
| **Distribution** | pip + Python runtime | Single binary |

The rewrite does not change what local-brain is — it changes how it ships.

---

## References

### Rust Frameworks
- [ollama-rs](https://github.com/pepperoni21/ollama-rs) — v0.3.4, Feb 2026. The Ollama Rust client.
- [ollama-rs function calling](https://deepwiki.com/pepperoni21/ollama-rs/5.2-function-calling) — #[function] macro, Coordinator pattern.
- [Rig](https://github.com/0xPlaygrounds/rig) — 6.1k stars. Multi-provider agent framework.
- [AutoAgents](https://github.com/liquidos-ai/AutoAgents) — 385 stars. ReAct, WASM sandbox.

### Go Frameworks
- [Eino](https://github.com/cloudwego/eino) — 9.7k stars. ByteDance. Native Ollama ChatModel.
- [LangChainGo](https://github.com/tmc/langchaingo) — 8.7k stars. 1,711 dependents.
- [MCPHost](https://github.com/mark3labs/mcphost) — Go CLI. Ollama + MCP. Go SDK available.

### MCP SDKs (for future MCP server path)
- [rmcp (Rust official)](https://github.com/modelcontextprotocol/rust-sdk) — v0.16.0, Feb 2026.
- [mcp-go (community Go)](https://github.com/mark3labs/mcp-go) — 8.2k stars. 400+ dependents.
- [go-sdk (Go official)](https://github.com/modelcontextprotocol/go-sdk) — 3.9k stars.

### tree-sitter in Rust
- [tree-sitter (Rust core)](https://github.com/tree-sitter/tree-sitter) — Native Rust implementation.
- [tree-sitter-python](https://github.com/tree-sitter/tree-sitter-python) — and all other grammar crates.
