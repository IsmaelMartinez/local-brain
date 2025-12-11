# Local Brain: Strategic Roadmap

**Date:** December 10, 2025  
**Status:** Research Document  
**Version:** 2.2 (Phase B Complete)

---

## Executive Summary

Local Brain is a Claude Code plugin that delegates codebase exploration to local Ollama models via Smolagents. After successful Phase A (hardening) and Phase B (navigation), the focus is now on **observation and feedback**.

### Key Findings

1. **Solid Foundation**: Clean, minimal architecture (~600 lines)
2. **Right Framework**: Smolagents provides security and flexibility
3. **Built-in Observability**: Smolagents has native OTEL support — use it
4. **Verified Tools**: `grep-ast`, `tree-sitter`, `detect-secrets` are production-ready

### Action Plan

| Phase | Goal | Timeline | Status |
|-------|------|----------|--------|
| **A: Harden** | Safety guardrails, observability | Week 1-2 | ✅ **COMPLETE** (v0.5.0) |
| **B: Navigate** | Better code search & structure tools | Week 3-5 | ✅ **COMPLETE** (v0.6.0) |
| **C: Observe** | Ship, gather feedback, iterate | Week 6+ | 🔜 Next |

---

## 1. Current State

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code (Cloud)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │ delegates
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Local Brain (CLI)                         │
│  ┌──────────────┐   ┌────────────────┐   ┌───────────────┐ │
│  │   CLI        │──▶│  Smolagents    │──▶│   Ollama      │ │
│  │  (click)     │   │  (CodeAgent)   │   │   (Local LLM) │ │
│  └──────────────┘   └────────────────┘   └───────────────┘ │
│         │                    │                              │
│         ▼                    ▼                              │
│  ┌──────────────┐   ┌────────────────┐                     │
│  │  Security    │   │    Tools       │                     │
│  │  (path jail) │   │  (7 @tool fns) │                     │
│  └──────────────┘   └────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

### Current Tools

| Tool | Purpose |
|------|---------|
| `read_file` | Read file contents (path-jailed, truncated, with timeout) |
| `list_directory` | Glob-based file listing (truncated, with timeout) |
| `file_info` | File metadata (with timeout) |
| `git_diff` | Show changes (truncated) |
| `git_status` | Branch/changes summary (truncated) |
| `git_log` | Commit history (truncated) |
| `git_changed_files` | Modified file list (truncated) |
| `search_code` | **NEW v0.6.0** - AST-aware code search with intelligent context |
| `list_definitions` | **NEW v0.6.0** - Extract class/function signatures from files |

### Gaps Addressed (v0.5.0)

| Gap | Before | After (v0.5.0) |
|-----|--------|----------------|
| **Output safety** | No limits | ✅ Truncation (200 lines/20K chars) + timeouts (30s) |
| **Observability** | Verbose flag only | ✅ OTEL tracing (`--trace` flag) |
| **Health checks** | None | ✅ `local-brain doctor` command |
| **Test coverage** | Basic | ✅ 60 tests (path-jailing, truncation, timeouts) |

### Gaps Addressed (v0.6.0)

| Gap | Before | After (v0.6.0) |
|-----|--------|----------------|
| **Code search** | Basic glob | ✅ AST-aware search via `search_code` (grep-ast) |
| **Navigation** | Read whole file | ✅ Extract definitions via `list_definitions` (tree-sitter) |
| **Test coverage** | 60 tests | ✅ 75 tests (navigation tools tested) |

---

## 2. Verified Pip-Installable Tools

**Spike-validated (December 10, 2025)** — All tested on Python 3.13:

| Library | Version | Python 3.13 | Spike | Status |
|---------|---------|-------------|-------|--------|
| [`grep-ast`](https://pypi.org/project/grep-ast/) | 0.9.0 | ✅ | #6 | **GO** |
| [`tree-sitter`](https://pypi.org/project/tree-sitter/) | 0.25.2 | ✅ | #7 | **GO** |
| [`tree-sitter-language-pack`](https://pypi.org/project/tree-sitter-language-pack/) | 0.13.0 | ✅ | #7 | **GO** (replaces tree-sitter-languages) |
| [`openinference-instrumentation-smolagents`](https://pypi.org/project/openinference-instrumentation-smolagents/) | 0.1.20 | ✅ | #5 | **GO** |
| [`opentelemetry-sdk`](https://pypi.org/project/opentelemetry-sdk/) | 1.39.0 | ✅ | #5 | **GO** |
| [`pygount`](https://pypi.org/project/pygount/) | 3.1.0 | ✅ | - | Optional |
| [`detect-secrets`](https://pypi.org/project/detect-secrets/) | 1.5.0 | ✅ | - | Deferred |

> **Note:** `tree-sitter-languages` v1.10.2 does NOT support Python 3.13. Use `tree-sitter-language-pack` instead (same API).

---

## 3. Implementation Plan

### Phase A: Harden (Week 1-2) ✅ COMPLETE

#### A.1 Output Truncation ✅

Implemented in `security.py`:

```python
def truncate_output(content: str, max_lines: int = 100, max_chars: int = 10000) -> str:
    """Clamp tool outputs with truncation metadata."""
    # Applied to all tools with 200 lines / 20K chars default
```

#### A.2 Per-Call Timeouts ✅

Implemented in `security.py`:

```python
def with_timeout(seconds: int = 30):
    """Decorator to add timeout to tools using SIGALRM."""
    # Applied to read_file, list_directory, file_info
```

#### A.3 OTEL Tracing ✅

Implemented in `tracing.py`:

```python
def setup_tracing():
    """Enable OTEL tracing - Smolagents captures everything automatically."""
    # Enabled via --trace flag
```

#### A.4 Health Check Command ✅

```bash
$ local-brain doctor

🔍 Local Brain Health Check

Checking Ollama...
  ✅ Ollama is installed (ollama version is 0.13.1)

Checking Ollama server...
  ✅ Ollama server is running (9 models)

Checking recommended models...
  ✅ Recommended models installed: qwen3:latest

Checking tools...
  ✅ Tools working (7 tools available)

Checking optional features...
  ✅ OTEL tracing available (--trace flag)

========================================
✅ All checks passed! Local Brain is ready.
```

#### A.5 Tasks ✅

| Task | Effort | Priority | Status |
|------|--------|----------|--------|
| Add output truncation | 1 day | P0 | ✅ Done |
| Add per-call timeouts | 0.5 day | P0 | ✅ Done |
| Add `--trace` flag (OTEL) | 0.5 day | P1 | ✅ Done |
| Add `local-brain doctor` | 1 day | P1 | ✅ Done |
| Integration tests for path-jailing | 1 day | P1 | ✅ Done (60 tests) |

---

### Phase B: Navigate (Week 3-5) ✅ COMPLETE

#### B.1 AST-Aware Code Search ✅

Implemented in `smolagent.py` using `grep-ast`:

```python
@tool
def search_code(pattern: str, file_path: str, ignore_case: bool = True) -> str:
    """Search code with AST awareness - shows intelligent context."""
    # Uses TreeContext.grep() to find line numbers
    # Then add_lines_of_interest() + add_context() + format()
    # Falls back to simple grep for unsupported languages
```

**Key Learning:** `tc.grep()` returns a *set of line numbers*, not formatted output.
Must call `tc.add_lines_of_interest(lines)`, `tc.add_context()`, then `tc.format()`.

#### B.2 List Definitions ✅

Implemented in `smolagent.py` using `tree-sitter-language-pack`:

```python
@tool
def list_definitions(file_path: str) -> str:
    """Extract class/function definitions with signatures and docstrings."""
    # Python 3.13: uses tree-sitter-language-pack (not tree-sitter-languages)
    # Walks AST to extract class/function nodes
    # Includes signatures and docstrings
```

**Sample Output:**
```
class UserService:
  "Service for managing users."
  def __init__(self, db):
  def get_user(self, user_id: int) -> dict:
    "Get user by ID."
  def create_user(self, name: str, email: str) -> int:
    "Create a new user."
def validate_email(email: str) -> bool:
  "Check if email is valid."
```

#### B.3 Code Statistics (Deferred)

`code_stats` using pygount deferred - low priority (P2). Can be added later if needed.

#### B.4 Tasks ✅

| Task | Effort | Priority | Status |
|------|--------|----------|--------|
| Add `search_code` (grep-ast) | 1-2 days | P0 | ✅ Done |
| Add `list_definitions` (tree-sitter) | 2 days | P0 | ✅ Done |
| Add `code_stats` (pygount) | 0.5 day | P2 | ⏸️ Deferred |

---

### Phase C: Observe & Learn (Week 6+)

**Do:**
- Ship Phases A & B
- Gather real usage feedback
- Monitor which tools are used most

**Then evaluate:**
- Is semantic search (RAG) actually needed?
- Do users want secrets scanning?
- Is the one-shot CLI sufficient?

> **Principle:** Don't build features in anticipation. Build what's needed based on evidence.

---

## 4. Deferred Ideas (Backlog)

These ideas are captured for future reference but are **not planned**:

| Idea | Why Deferred | Spike |
|------|--------------|-------|
| Pyodide/WASM sandbox | Not available in Smolagents. LocalPythonExecutor is sufficient. | #8 ❌ |
| Semantic search (ChromaDB/RAG) | High effort, unclear value. See if grep-ast is enough. | - |
| Secrets scanning integration | `detect-secrets` exists. Use it directly if needed. | - |
| MCP bridge | Wait for ecosystem maturity. | - |
| Plugin architecture | No demand. Over-engineering risk. | - |
| Service daemon mode | Major architecture change. `--trace` is enough for now. | - |

---

## 5. Tool Implementation Checklist

For each new tool:
- [x] Define clear docstring with Args/Returns
- [x] Implement path jailing (if file-related)
- [x] Add timeout handling
- [x] Add output truncation
- [x] Write unit tests
- [x] Add to `ALL_TOOLS` list
- [ ] Update SKILL.md documentation

---

## 6. References

### Core
- [Smolagents Documentation](https://huggingface.co/docs/smolagents)
- [Ollama Models](https://ollama.ai/library)

### Verified Tools (December 2025)
- [grep-ast](https://pypi.org/project/grep-ast/) v0.9.0
- [tree-sitter](https://pypi.org/project/tree-sitter/) v0.25.2
- [tree-sitter-languages](https://pypi.org/project/tree-sitter-languages/) v1.10.2
- [pygount](https://pypi.org/project/pygount/) v3.1.0
- [detect-secrets](https://github.com/Yelp/detect-secrets) v1.5.0
- [openinference-instrumentation-smolagents](https://pypi.org/project/openinference-instrumentation-smolagents/) v0.1.20

---

## 7. Changelog

### v0.6.0 (December 10, 2025) - Phase B: Navigate

**New Features:**
- `search_code` tool: AST-aware code search using grep-ast
  - Shows intelligent context around matches (function/class boundaries)
  - Supports Python, JavaScript, TypeScript, Go, Rust, Ruby, Java, C/C++
  - Falls back to simple grep for unsupported languages
- `list_definitions` tool: Extract class/function definitions using tree-sitter
  - Shows signatures and docstrings without full implementation
  - Great for understanding file structure quickly
  - Python 3.13 compatible via `tree-sitter-language-pack`

**Improvements:**
- 9 tools total (was 7)
- Better code navigation without reading entire files

**Testing:**
- 75 tests total (was 60)
- Comprehensive tests for new navigation tools
- Security tests for new tools (path-jailing, sensitive files)

**Dependencies:**
- New: `grep-ast>=0.9.0`
- New: `tree-sitter>=0.25.0`
- New: `tree-sitter-language-pack>=0.13.0`

---

### v0.5.0 (December 10, 2025) - Phase A: Harden

**New Features:**
- Output truncation for all tools (200 lines / 20K chars default)
- Per-call timeouts (30s default) using SIGALRM
- OTEL tracing support via `--trace` flag
- `local-brain doctor` health check command

**Improvements:**
- Enhanced path-jailing with sensitive file detection
- Consistent error handling with `ToolTimeoutError`

**Testing:**
- 60 tests total (all passing)
- Comprehensive security tests (path traversal, symlinks)
- Truncation and timeout tests

**Dependencies:**
- Optional: `openinference-instrumentation-smolagents>=0.1.20`
- Optional: `opentelemetry-sdk>=1.39.0`

---

*Next review: January 2026*
