# Spikes: Technical Validation

This directory contains spike scripts to validate technical decisions before implementation.

## Prerequisites

```bash
# Install all spike dependencies
uv pip install -e ".[dev]"

# For Phase 3 spikes, also install:
uv pip install grep-ast tree-sitter tree-sitter-languages
uv pip install openinference-instrumentation-smolagents opentelemetry-sdk

# Ensure Ollama is running with a capable model
ollama pull qwen3:latest
```

---

## Phase 2 Spikes (Completed ✅)

Validated Smolagents as the agent framework.

| Spike | Purpose | Status |
|-------|---------|--------|
| `spike_01_smolagents_basic.py` | Basic Smolagents + Ollama integration | ✅ Passed |
| `spike_02_code_as_tool.py` | Code-as-tool pattern | ✅ Passed |
| `spike_03_sandbox_security.py` | LocalPythonExecutor restrictions | ✅ Passed |
| `spike_04_qwen_coder_quality.py` | Code quality with Qwen-Coder | ✅ Passed |

---

## Phase 3 Spikes (Completed ✅)

Validated tools and observability for the roadmap. **Run date: December 10, 2025**

| Spike | Purpose | Result |
|-------|---------|--------|
| `spike_05_otel_tracing.py` | OTEL tracing with Smolagents | ✅ **PASSED** |
| `spike_06_grep_ast.py` | AST-aware code search | ✅ **PASSED** |
| `spike_07_tree_sitter.py` | Extract code definitions | ✅ **PASSED** |
| `spike_08_pyodide_sandbox.py` | WASM sandbox availability | ⚠️ **DEFER** |

### Results

#### Spike 5: OTEL Tracing ✅
- [x] `openinference-instrumentation-smolagents` v0.1.20 imports cleanly
- [x] Tracer captures agent execution steps, LLM calls, tool calls
- [x] Console exporter works for debugging
- **Decision:** GO — Implement `--trace` flag

#### Spike 6: grep-ast ✅
- [x] `grep-ast` v0.9.0 works on Python 3.13
- [x] Language detection is 7/7 accurate
- [x] AST-aware search works (API: `tc.grep(pattern, ignore_case)`)
- **Decision:** GO — Use for `search_code` tool

#### Spike 7: tree-sitter ✅
- [x] `tree-sitter` v0.25.2 works
- [x] `tree-sitter-language-pack` v0.13.0 works (replaces tree-sitter-languages for Python 3.13)
- [x] Can parse Python and extract definitions
- [x] Can get signatures without full body
- **Decision:** GO — Use for `list_definitions` tool

#### Spike 8: Pyodide Sandbox ⚠️
- [x] PyodideExecutor does NOT exist (there's WasmExecutor)
- [x] LocalPythonExecutor is default and sufficient
- [x] DockerExecutor available but overkill
- **Decision:** DEFER — Stick with LocalPythonExecutor

See [SPIKE_RESULTS.md](./SPIKE_RESULTS.md) for full details.

---

## Running All Phase 3 Spikes

```bash
# Run all spikes in sequence
for spike in spikes/spike_0{5,6,7,8}*.py; do
    echo "Running $spike..."
    uv run python "$spike"
    echo ""
done
```

---

## Decision Criteria

### Go with grep-ast if:
- Language detection works for common languages
- AST context improves search results
- Performance is acceptable

### Go with tree-sitter if:
- Can reliably extract definitions across languages
- Output is clean and useful
- Doesn't require complex setup

### Enable OTEL tracing if:
- Smolagents instrumentation works out of the box
- Captures useful debugging information
- Minimal performance overhead

### Skip Pyodide sandbox if:
- Not available in current Smolagents
- LocalPythonExecutor provides adequate security
- Setup complexity outweighs benefits

---

## Recording Results

After running spikes, update `SPIKE_RESULTS.md` with findings.
