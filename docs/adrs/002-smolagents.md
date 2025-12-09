# ADR-002: Use Smolagents for Code Execution

**Status:** Accepted  
**Date:** 2025-12-09

## Context

The original implementation used Ollama's native tool-calling with a custom tool registry and regex-based command allowlists. We needed better security and a simpler architecture.

## Decision

Replace the custom agent with [Smolagents](https://github.com/huggingface/smolagents) CodeAgent.

### What Smolagents Provides
- `CodeAgent` — Executes tasks via code generation (code-as-tool pattern)
- `LiteLLMModel` — Connects to Ollama via LiteLLM
- `@tool` decorator — Registers custom tools with the agent
- `LocalPythonExecutor` — Sandboxed Python execution

### Why Smolagents
- **Code-as-tool pattern** — Model writes Python code instead of calling fixed tools
- **Better security** — LocalPythonExecutor sandbox vs regex allowlists
- **Simpler codebase** — No separate tool registry or allowlist maintenance
- **HuggingFace maintained** — Active development and support

### Spike Validation
All 4 spikes passed before implementation:
1. Smolagents + Ollama via LiteLLM ✅
2. Code-as-tool pattern ✅
3. LocalPythonExecutor sandbox ✅
4. Qwen-Coder code quality ✅

## Consequences

- Removed `local_brain/tools/` folder — tools now in `smolagent.py`
- Removed `local_brain/agent.py` — replaced by Smolagents CodeAgent
- Added dependencies: `smolagents`, `litellm`
- Python restricted to 3.10-3.13 (grpcio build issue with 3.14)
- Better security via sandbox instead of regex allowlists

