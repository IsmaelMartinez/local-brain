# Local Brain: Strategic Roadmap

**Date:** December 10, 2025  
**Status:** Research Document  
**Version:** 2.0 (Simplified)

---

## Executive Summary

Local Brain is a Claude Code plugin that delegates codebase exploration to local Ollama models via Smolagents. After successful Phase 2 validation, the focus is on **hardening** and **better navigation tools**.

### Key Findings

1. **Solid Foundation**: Clean, minimal architecture (~500 lines)
2. **Right Framework**: Smolagents provides security and flexibility
3. **Built-in Observability**: Smolagents has native OTEL support — use it
4. **Verified Tools**: `grep-ast`, `tree-sitter`, `detect-secrets` are production-ready

### Action Plan

| Phase | Goal | Timeline |
|-------|------|----------|
| **A: Harden** | Safety guardrails, observability | Week 1-2 |
| **B: Navigate** | Better code search & structure tools | Week 3-5 |
| **C: Observe** | Ship, gather feedback, iterate | Week 6+ |

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
| `read_file` | Read file contents (path-jailed) |
| `list_directory` | Glob-based file listing |
| `file_info` | File metadata |
| `git_diff` | Show changes |
| `git_status` | Branch/changes summary |
| `git_log` | Commit history |
| `git_changed_files` | Modified file list |

### Gaps to Address

| Gap | Current | Target |
|-----|---------|--------|
| **Output safety** | No limits | Truncation + timeouts |
| **Observability** | Verbose flag only | OTEL tracing |
| **Code search** | Basic glob | AST-aware (grep-ast) |
| **Navigation** | Read whole file | Extract definitions only |

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

### Phase A: Harden (Week 1-2)

#### A.1 Output Truncation

```python
def truncate_output(content: str, max_lines: int = 100, max_chars: int = 10000) -> str:
    """Clamp tool outputs with truncation metadata."""
    lines = content.split('\n')
    truncated = False
    
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        truncated = True
    
    result = '\n'.join(lines)
    if len(result) > max_chars:
        result = result[:max_chars]
        truncated = True
    
    if truncated:
        result += f"\n\n[TRUNCATED: Output exceeded limits. Use more specific queries.]"
    
    return result
```

#### A.2 Per-Call Timeouts

```python
import signal
from functools import wraps

def with_timeout(seconds: int = 30):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def handler(signum, frame):
                raise TimeoutError(f"Tool {func.__name__} timed out")
            
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds)
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
        return wrapper
    return decorator
```

#### A.3 OTEL Tracing (Spike #5 Validated ✅)

**What gets traced automatically:**
- Agent runs (`CodeAgent.run`)
- Individual steps (`Step 1`, `Step 2`)
- LLM calls with token counts
- Tool calls with inputs/outputs

```python
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor

def setup_tracing():
    """Enable OTEL tracing - Smolagents captures everything automatically."""
    tracer_provider = TracerProvider()
    trace.set_tracer_provider(tracer_provider)
    tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    SmolagentsInstrumentor().instrument(tracer_provider=tracer_provider)

# CLI flag
@click.option('--trace', is_flag=True, help='Enable tracing')
def main(trace: bool, ...):
    if trace:
        setup_tracing()
```

#### A.4 Health Check Command

```bash
$ local-brain doctor

✅ Ollama is running (v0.4.1)
✅ Models available: qwen3:latest, qwen2.5-coder:7b
✅ Recommended model installed: qwen3:latest
✅ Tool test: read_file executed successfully
```

#### A.5 Tasks

| Task | Effort | Priority |
|------|--------|----------|
| Add output truncation | 1 day | P0 |
| Add per-call timeouts | 0.5 day | P0 |
| Add `--trace` flag (OTEL) | 0.5 day | P1 |
| Add `local-brain doctor` | 1 day | P1 |
| Integration tests for path-jailing | 1 day | P1 |

---

### Phase B: Navigate (Week 3-5)

#### B.1 AST-Aware Code Search (Spike #6 Validated ✅)

**API Note:** `tc.grep(pattern, ignore_case)` — NOT `color=False`

```python
from grep_ast import TreeContext, filename_to_lang

@tool
def search_code(pattern: str, file_path: str, ignore_case: bool = True) -> str:
    """Search code with AST awareness - shows context intelligently.
    
    Args:
        pattern: Text pattern to search for
        file_path: File to search in
        ignore_case: Whether to ignore case in search
    
    Returns:
        Matches with AST-aware context (function/class boundaries)
    """
    lang = filename_to_lang(file_path)
    if not lang:
        return _simple_grep(pattern, file_path)
    
    tc = TreeContext(file_path, code=Path(file_path).read_text())
    return tc.grep(pattern, ignore_case=ignore_case)
```

#### B.2 List Definitions (Spike #7 Validated ✅)

**Python 3.13 Compatibility:** Use `tree-sitter-language-pack` (not `tree-sitter-languages`)

```python
# Compatibility import for Python 3.13
try:
    import tree_sitter_language_pack as ts_langs
except ImportError:
    import tree_sitter_languages as ts_langs

@tool
def list_definitions(file_path: str) -> str:
    """Extract class/function definitions without reading full content.
    
    Args:
        file_path: Path to the source file
    
    Returns:
        List of classes/functions with signatures and docstrings
    """
    code = Path(file_path).read_text()
    parser = ts_langs.get_parser("python")
    tree = parser.parse(code.encode())
    
    # Walk AST and extract definitions
    # See spike_07_tree_sitter.py for full implementation
```

**Sample Output:**
```
class UserService:
  def __init__(self, db):
  def get_user(self, user_id: int) -> dict:
  def create_user(self, name: str, email: str) -> int:
def validate_email(email: str) -> bool:
```

#### B.3 Code Statistics (pygount)

```python
@tool
def code_stats(path: str = ".") -> str:
    """Get code statistics for the project.
    
    Args:
        path: Directory to analyze
    
    Returns:
        Lines of code by language
    """
    # Wrap pygount for LOC counts
```

#### B.4 Tasks

| Task | Effort | Priority |
|------|--------|----------|
| Add `search_code` (grep-ast) | 1-2 days | P0 |
| Add `list_definitions` (tree-sitter) | 2 days | P0 |
| Add `code_stats` (pygount) | 0.5 day | P2 |

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
- [ ] Define clear docstring with Args/Returns
- [ ] Implement path jailing (if file-related)
- [ ] Add timeout handling
- [ ] Add output truncation
- [ ] Write unit tests
- [ ] Add to `ALL_TOOLS` list
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

*Next review: January 2025*
