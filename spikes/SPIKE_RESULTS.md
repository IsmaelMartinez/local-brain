# Phase 3 Spike Results

**Date:** December 10, 2025  
**Environment:** Python 3.13.11, macOS

---

## Summary

| Spike | Result | Key Finding |
|-------|--------|-------------|
| 5: OTEL Tracing | ✅ **PASSED** | Works out of the box with Smolagents |
| 6: grep-ast | ✅ **PASSED** | AST-aware search works, API is `grep(pattern, ignore_case)` |
| 7: tree-sitter | ✅ **PASSED** | Definition extraction works perfectly |
| 8: Pyodide Sandbox | ⚠️ **DEFER** | Pyodide not available, LocalPythonExecutor is sufficient |

---

## Spike 5: OTEL Tracing ✅

### What Works
- `openinference-instrumentation-smolagents` v0.1.20 installs and imports cleanly
- `SmolagentsInstrumentor().instrument()` captures:
  - Agent runs (`CodeAgent.run`)
  - Individual steps (`Step 1`, `Step 2`, etc.)
  - LLM calls with token counts
  - Tool calls with inputs and outputs
- Console exporter works for debugging
- Structured spans with trace/span IDs

### Sample Output
```json
{
    "name": "SimpleTool",
    "attributes": {
        "tool.name": "add_numbers",
        "input.value": "{\"a\": 3, \"b\": 4}",
        "output.value": 7,
        "openinference.span.kind": "TOOL"
    }
}
```

### Recommendation
✅ **GO** — Add `--trace` flag that enables OTEL with ConsoleSpanExporter

---

## Spike 6: grep-ast ✅

### What Works
- `grep-ast` v0.9.0 installs cleanly
- Language detection: 7/7 correct (Python, JS, TS, CSS, HTML, TOML, unknown)
- `TreeContext` creation works
- Search returns AST-aware context

### API Note
Correct signature is:
```python
tc.grep(pattern, ignore_case=False)  # NOT tc.grep(pattern, color=False)
```

### Recommendation
✅ **GO** — Use grep-ast for `search_code` tool

---

## Spike 7: tree-sitter ✅

### What Works
- `tree-sitter` v0.25.2 + `tree-sitter-language-pack` v0.13.0 work on Python 3.13
- Parser loads and parses Python correctly
- Can extract all definitions (classes, functions)
- Can extract signatures without bodies

### Python 3.13 Compatibility Note
`tree-sitter-languages` doesn't support Python 3.13 yet, but `tree-sitter-language-pack` does and has the same API:
```python
try:
    import tree_sitter_language_pack as ts_langs
except ImportError:
    import tree_sitter_languages as ts_langs

parser = ts_langs.get_parser("python")
```

### Sample Output
```
class UserService:
  def __init__(self, db):
  def get_user(self, user_id: int) -> dict:
  def create_user(self, name: str, email: str) -> int:
def validate_email(email: str) -> bool:
def fetch_user_async(user_id: int) -> dict:
```

### Recommendation
✅ **GO** — Use tree-sitter for `list_definitions` tool

---

## Spike 8: Pyodide/WASM Sandbox ⚠️

### Findings

**Available Executors in Smolagents:**
- `LocalPythonExecutor` ✅ (default, recommended)
- `DockerExecutor` (requires Docker daemon)
- `E2BExecutor` (requires API key)
- `WasmExecutor` (exists but not PyodideExecutor)
- `BlaxelExecutor`, `ModalExecutor` (cloud services)

**PyodideExecutor:** Does NOT exist in smolagents (there's `WasmExecutor` instead)

**LocalPythonExecutor:** 
- Default executor
- Blocks dangerous imports
- Sufficient for our use case

### Recommendation
🔴 **DEFER** — Don't pursue WasmExecutor. LocalPythonExecutor is good enough.

---

## Dependencies Verified

| Package | Version | Python 3.13 | Status |
|---------|---------|-------------|--------|
| grep-ast | 0.9.0 | ✅ | Works |
| tree-sitter | 0.25.2 | ✅ | Works |
| tree-sitter-language-pack | 0.13.0 | ✅ | Use instead of tree-sitter-languages |
| tree-sitter-languages | 1.10.2 | ❌ | No Python 3.13 wheels |
| openinference-instrumentation-smolagents | 0.1.20 | ✅ | Works |
| opentelemetry-sdk | 1.39.0 | ✅ | Works |

---

## Decision Summary

| Item | Decision | Rationale |
|------|----------|-----------|
| OTEL Tracing | ✅ Implement | Works out of the box, captures everything |
| grep-ast search | ✅ Implement | Proven library, AST-aware context |
| tree-sitter definitions | ✅ Implement | Works perfectly for Python |
| Pyodide sandbox | 🔴 Skip | Not available, LocalPythonExecutor sufficient |
| Output truncation | ✅ Implement | Simple, essential guardrail |
| Timeouts | ✅ Implement | Simple, defensive measure |

---

## Next Steps

1. **Phase A: Harden (Week 1-2)**
   - Add output truncation to all tools
   - Add per-call timeouts  
   - Add `--trace` flag with OTEL
   - Add `local-brain doctor` command

2. **Phase B: Navigate (Week 3-5)**
   - Add `search_code` tool using grep-ast
   - Add `list_definitions` tool using tree-sitter
   - Add `code_stats` tool using pygount (optional)

3. **Phase C: Observe (Week 6+)**
   - Ship and gather feedback
   - Iterate based on real usage
