# Phase 2 Spikes: Smolagents Evaluation

This directory contains spike scripts to evaluate Smolagents as a replacement for the current tool-based approach.

## Prerequisites

```bash
# Install spike dependencies
uv add smolagents litellm --dev

# Ensure Ollama is running with a code-capable model
ollama pull qwen2.5-coder:7b
```

## Spikes

| Spike | Purpose | Run Command |
|-------|---------|-------------|
| `spike_01_smolagents_basic.py` | Test basic Smolagents + Ollama integration | `uv run python spikes/spike_01_smolagents_basic.py` |
| `spike_02_code_as_tool.py` | Test code-as-tool pattern | `uv run python spikes/spike_02_code_as_tool.py` |
| `spike_03_sandbox_security.py` | Test LocalPythonExecutor restrictions | `uv run python spikes/spike_03_sandbox_security.py` |
| `spike_04_qwen_coder_quality.py` | Test code quality with Qwen-Coder | `uv run python spikes/spike_04_qwen_coder_quality.py` |

## Expected Outcomes

### Spike 1: Basic Integration
- ✅ Smolagents connects to Ollama via LiteLLM
- ✅ Model can be initialized
- ✅ Basic chat works

### Spike 2: Code-as-Tool
- ✅ Model generates executable Python code
- ✅ Code executes correctly
- ✅ Results are returned properly

### Spike 3: Sandbox Security
- ✅ File I/O is blocked
- ✅ Dangerous imports are restricted
- ✅ subprocess/os.system calls are blocked

### Spike 4: Code Quality
- ✅ Model generates correct file reading code
- ✅ Model handles errors gracefully
- ✅ Code is readable and maintainable

## Decision Criteria

**Go with Smolagents if:**
- All 4 spikes pass
- Code quality is acceptable
- Sandboxing provides better security than current regex allowlist

**Keep current implementation if:**
- Smolagents doesn't work reliably with Ollama
- Code generation quality is poor
- Sandboxing is insufficient

