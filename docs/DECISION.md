# Local Brain: Architecture Decision Record

**Date:** December 9, 2025  
**Status:** Approved (Phase 2 Complete)  
**Context:** Claude Code skill delegation to local Ollama models

---

## Executive Summary

After multi-model research analysis and spike validation, we have **implemented Smolagents** as the core execution engine. This replaces the custom tool-calling approach with a more secure, code-as-tool pattern.

---

## The Actual Use Case

```
┌─────────────┐     delegates      ┌─────────────┐     calls      ┌─────────┐
│ Claude Code │ ──────────────────►│ Local Brain │ ──────────────►│ Ollama  │
│   (Cloud)   │                    │ (Smolagents)│                │ (Local) │
│             │◄────────────────── │             │◄────────────── │         │
└─────────────┘     returns        └─────────────┘    responds    └─────────┘
                    results                        with code execution
```

**Key Insight:** Local Brain is NOT a standalone CLI competing with Aider. It's a **delegation target** for Claude Code skills, providing local model access with codebase tools.

---

## Decision: Implement Smolagents (Phase 2 Complete)

### Why Smolagents

After evaluating multiple approaches, Smolagents was chosen because:

- ✅ **Code-as-tool pattern** — Model writes Python code instead of calling fixed tools
- ✅ **Better security** — LocalPythonExecutor sandbox vs regex allowlists
- ✅ **Simpler codebase** — No separate tool registry or allowlist maintenance
- ✅ **LiteLLM integration** — Works seamlessly with Ollama
- ✅ **HuggingFace maintained** — Active development and support

### Why NOT Other Options

| Alternative | Verdict | Reason |
|-------------|---------|--------|
| **Aider** | ❌ Rejected | Interactive, not programmable |
| **LangChain** | ❌ Rejected | Too heavy (50+ deps), overkill |
| **LlamaIndex** | ❌ Rejected | RAG-focused, not tool-focused |
| **AutoGen** | ❌ Rejected | Multi-agent, overkill |
| **CrewAI** | ❌ Rejected | Multi-agent, overkill |
| **Custom tools/** | ❌ Replaced | Regex allowlists less secure than sandbox |

---

## Roadmap

### Phase 1: ✅ Complete - Improve Current Implementation

| Task | Priority | Status |
|------|----------|--------|
| Add path jailing (restrict to project root) | High | ✅ Done |
| Add model discovery (detect installed Ollama models) | High | ✅ Done |
| Add smart model selection based on task | Medium | ✅ Done |
| Add tests for allowlist/denylist behavior | Medium | ✅ Done |

### Phase 2: ✅ Complete - Implement Smolagents

| Task | Priority | Status |
|------|----------|--------|
| Spike 1: Test Smolagents + Ollama via LiteLLM | High | ✅ Done |
| Spike 2: Validate code-as-tool pattern | High | ✅ Done |
| Spike 3: Test LocalPythonExecutor sandbox | High | ✅ Done |
| Spike 4: Test Qwen-Coder code quality | High | ✅ Done |
| Implement smolagent.py with CodeAgent | High | ✅ Done |
| Convert tools to @tool decorator | High | ✅ Done |
| Remove legacy tools/ folder | Medium | ✅ Done |
| Update CLI to use Smolagents | High | ✅ Done |
| Add tests for new implementation | High | ✅ Done |

#### Spike Results Summary

All 4 spikes passed (see `spikes/SPIKE_RESULTS.md` for details):

1. **Smolagents + Ollama** — Seamless integration via LiteLLM
2. **Code-as-tool** — Model generates clean, executable Python
3. **Sandbox security** — File I/O, subprocess, dangerous imports all blocked
4. **Code quality** — Qwen-Coder produces high-quality code

### Phase 3: Future - Consider MCP Bridge

**What:** Model Context Protocol (MCP) is an emerging standard for LLM tooling.

**Opportunity:** Local Brain could become the **Ollama ↔ MCP bridge**:
- Receive tool schemas from MCP servers
- Translate to Ollama's tool format
- Execute via Ollama
- Return results via MCP protocol

**When to pursue:**
- MCP adoption increases
- Community needs Ollama↔MCP connectivity
- High effort, high risk, high potential reward

### Future Maybe

| Task | Notes |
|------|-------|
| Docker Sandbox | Stronger isolation when Docker available |
| Retry logic for Ollama calls | Low priority, Ollama is local and usually reliable |
| Streaming support | Nice-to-have for long responses |

---

## Current Architecture (v0.4.0)

```
Claude Code Skill
    │
    └──► local-brain CLI
            │
            ├──► models.py (model discovery)
            │       │
            │       └──► ollama.list() → smart model selection
            │
            ├──► smolagent.py (Smolagents CodeAgent)
            │       │
            │       ├──► LiteLLMModel → Ollama
            │       │
            │       └──► Tools (@tool decorator)
            │               ├── read_file [JAILED]
            │               ├── list_directory [JAILED]
            │               ├── file_info [JAILED]
            │               ├── git_diff
            │               ├── git_status
            │               ├── git_log
            │               └── git_changed_files
            │
            └──► security.py (path jailing)
```

### Security Features

- **LocalPythonExecutor sandbox** — Smolagents' built-in sandboxed execution
- **Path jailing** — All file operations restricted to project root
- **Import restrictions** — Dangerous imports (subprocess, socket, etc.) blocked
- **No network access** — Prevents data exfiltration
- **Truncation limits** — Large outputs capped to prevent context overflow

### Strengths

- **Smolagents CodeAgent** for secure code execution
- **LiteLLM** for Ollama integration
- ~350 lines of focused code (down from ~500)
- 4 dependencies (ollama, click, smolagents, litellm)
- Read-only security posture
- Smart model discovery

### Trade-offs Accepted

- Python 3.10-3.13 required (grpcio build issue with 3.14)
- Additional dependencies vs original 2
- Slightly slower execution (~7-35 seconds per task)

---

## Model Discovery & Selection

Local Brain includes smart model management:

### Model Discovery
```python
# Automatically detects installed Ollama models
ollama.list()  # Returns all installed models with metadata
```

### Recommended Models (Code Generation Capable)

| Model | Size | Code Quality | Best For |
|-------|------|--------------|----------|
| `qwen3:latest` | 4.4GB | ✅ Excellent | General purpose, default |
| `qwen2.5-coder:7b` | 4.7GB | ✅ Excellent | Code-focused tasks |
| `llama3.2:3b` | 2.0GB | ✅ Good | Fast, lightweight |
| `mistral:7b` | 4.1GB | ✅ Good | Balanced performance |
| `deepseek-coder-v2:16b` | 8.9GB | ✅ Excellent | Complex code analysis |

### Auto-Selection Logic
1. Check installed models against recommended list
2. If recommended model found → use it
3. If multiple found → prefer by capability tier
4. If none found → offer to pull recommended model

---

## Web Tools Consideration

**Decision:** ❌ **NOT adding web tools**

**Reasons:**
- **Security risk**: Data exfiltration, SSRF attacks, prompt injection from fetched content
- **Complexity**: URL validation, rate limiting, content sanitization
- **Scope creep**: Local Brain is for *local* codebase exploration
- **Dependencies**: Would add more packages

**Alternative for documentation lookup:**
- Claude Code already has web access
- Delegate web research to Claude, local execution to Local Brain

---

## Research Archive

The following documents were synthesized into this decision:

| Document | Model | Stance |
|----------|-------|--------|
| `RESEARCH-claude-4.5-opus-high.md` | Claude 4.5 Opus | Deprecate or pivot |
| `RESEARCH-composer-1.md` | Composer | Keep as-is |
| `RESEARCH-gemini-3-pro.md` | Gemini 3 Pro | Use Smolagents |
| `RESEARCH-gpt-5.1-codex-max.md` | GPT-5.1 Codex Max | Redundant but valuable |

All models agreed:
- Current code is clean and well-written
- The LLM tooling space has mature alternatives
- Security implementation could be improved

The key disagreement was resolved by recognizing the **actual use case** (delegation, not standalone CLI).

---

## Conclusion

**Local Brain now uses Smolagents for secure, sandboxed code execution.** The code-as-tool pattern simplifies the codebase while improving security over the previous regex-based allowlist approach.

**No web tools** — Claude Code handles web research; Local Brain handles local execution.

---

*Phase 1 completed: December 8, 2025*  
*Phase 2 completed: December 9, 2025*
