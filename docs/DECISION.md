# Local Brain: Architecture Decision Record

**Date:** December 8, 2025  
**Status:** Approved  
**Context:** Claude Code skill delegation to local Ollama models

---

## Executive Summary

After multi-model research analysis, the decision is to **keep the current implementation** with incremental improvements, while evaluating Smolagents as a future option.

---

## The Actual Use Case

```
┌─────────────┐     delegates      ┌─────────────┐     calls      ┌─────────┐
│ Claude Code │ ──────────────────►│ Local Brain │ ──────────────►│ Ollama  │
│   (Cloud)   │                    │   (Local)   │                │ (Local) │
│             │◄────────────────── │             │◄────────────── │         │
└─────────────┘     returns        └─────────────┘    responds    └─────────┘
                    results                           with tools
```

**Key Insight:** Local Brain is NOT a standalone CLI competing with Aider. It's a **delegation target** for Claude Code skills, providing local model access with codebase tools.

---

## Decision: Keep Current Implementation

### Why NOT Aider
- Aider is **interactive** (designed for humans in terminals)
- No programmatic API for delegation
- Expects user input/confirmation loops
- Cannot be called as a subprocess with structured results

### Why NOT Frameworks (LangChain, LlamaIndex, etc.)
- **Overkill**: 50+ dependencies vs 2 (ollama, click)
- **Abstraction overhead**: We talk directly to Ollama
- **Maintenance burden**: Frameworks evolve, APIs break
- Current ~450 lines of focused code is the right size

### Why Keep Current
- ✅ **Works** for the delegation use case
- ✅ **Minimal** dependencies
- ✅ **Focused** on read-only codebase exploration
- ✅ **Simple** to maintain and extend
- ✅ **Native** Ollama integration

---

## Roadmap

### Phase 1: Now - Improve Current Implementation

| Task | Priority | Status |
|------|----------|--------|
| Add path jailing (restrict to project root) | High | ✅ Done |
| Add model discovery (detect installed Ollama models) | High | ✅ Done |
| Add smart model selection based on task | Medium | ✅ Done |
| Add tests for allowlist/denylist behavior | Medium | ✅ Done |

### Phase 2: Next - Evaluate Smolagents + Sandboxing

**What:** Code-as-tool pattern where model writes Python instead of calling fixed tools.

**Why consider:**
- Eliminates tool maintenance entirely
- **Sandboxed execution** (better than regex allowlists)
- Model writes `import os; os.listdir('.')` instead of calling `list_directory` tool
- Smolagents requires minimum security level for code execution

**Experiment:**
1. Create `feature/smolagents` branch
2. Test with Qwen-Coder via Ollama
3. Validate code generation quality
4. If works: Replace `local_brain/tools/`
5. If doesn't: Keep current approach

#### Sandboxing Research (Required for Smolagents)

**Requirement:** Smolagents requires sandboxing for safe code execution. We need a solution that can ship with the tool (no external services).

##### Sandboxing Options Evaluated

| Solution | Type | Ship-able | Pros | Cons |
|----------|------|-----------|------|------|
| **LocalPythonExecutor** | smolagents built-in | ✅ Yes | No deps, restricted imports, no file I/O | Limited isolation, not true sandbox |
| **E2B Sandbox** | Cloud service | ❌ No | Strong isolation | Requires API key, external service |
| **Docker Sandbox** | Container | ⚠️ Partial | Strong isolation | Requires Docker installed |
| **WebAssembly (Pyodide+Deno)** | WASM | ⚠️ Partial | Good isolation | Complex setup, limited Python libs |
| **RestrictedPython** | AST-based | ✅ Yes | No deps, pure Python | Bypassable, limited security |
| **bubblewrap (bwrap)** | Linux syscall | ❌ No | Strong isolation | Linux-only, needs installation |

##### Recommended Approach: LocalPythonExecutor (Phase 2a)

smolagents' `LocalPythonExecutor` provides basic security without external dependencies:

```python
from smolagents.local_python_executor import LocalPythonExecutor

# Built-in restrictions:
# - No file I/O operations (open, write, etc.)
# - Restricted import list (safe modules only)
# - No subprocess/os.system calls
# - Execution timeout
```

**Trade-offs:**
- ✅ Ships with `pip install smolagents` — no extra setup
- ✅ Better than current regex allowlist approach
- ⚠️ Not a true sandbox (runs in same process)
- ⚠️ Determined attacker could potentially bypass

##### Future Enhancement: Docker Sandbox (Phase 2b)

For stronger isolation when available:

```python
from smolagents import DockerSandbox

# Strong isolation:
# - Separate container per execution
# - Network isolation
# - Resource limits
# - File system isolation
```

**Trade-offs:**
- ✅ True process isolation
- ✅ Works on macOS/Linux/Windows (with Docker)
- ⚠️ Requires Docker to be installed
- ⚠️ Slower execution (container startup)

##### Decision Matrix

| User Environment | Recommended Sandbox |
|------------------|---------------------|
| Docker available | Docker Sandbox (strongest) |
| Docker unavailable | LocalPythonExecutor (adequate) |
| Security-critical | Don't use smolagents, keep current tools |

#### Web Tools Consideration

**Decision:** ❌ **NOT adding web tools in Phase 1 or 2**

**Reasons:**
- **Security risk**: Data exfiltration, SSRF attacks, prompt injection from fetched content
- **Complexity**: URL validation, rate limiting, content sanitization
- **Scope creep**: Local Brain is for *local* codebase exploration
- **Dependencies**: Would add `httpx`, `beautifulsoup4`, `duckduckgo-search`

**If web tools are needed later (Phase 3+):**
- Consider **Smolagents with Docker sandbox** for safe web access
- Docker provides network isolation at container level
- See [RESEARCH_WEB_TOOLS.md](./RESEARCH_WEB_TOOLS.md) for implementation details

**Alternative for documentation lookup:**
- Claude Code already has web access
- Delegate web research to Claude, local execution to Local Brain

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
| Retry logic for Ollama calls | Low priority, Ollama is local and usually reliable |
| Streaming support | Nice-to-have for long responses |

---

## Model Discovery & Selection

Local Brain now includes smart model management:

### Model Discovery
```python
# Automatically detects installed Ollama models
ollama.list()  # Returns all installed models with metadata
```

### Recommended Models (Tool-Calling Capable)

| Model | Size | Tool Support | Best For |
|-------|------|--------------|----------|
| `qwen3:latest` | 4.4GB | ✅ Excellent | General purpose, default |
| `qwen2.5-coder:7b` | 4.7GB | ✅ Good | Code-focused tasks |
| `llama3.2:3b` | 2.0GB | ✅ Good | Fast, lightweight |
| `mistral:7b` | 4.1GB | ✅ Good | Balanced performance |
| `deepseek-coder-v2:16b` | 8.9GB | ✅ Good | Complex code analysis |

### Auto-Selection Logic
1. Check installed models against recommended list
2. If recommended model found → use it
3. If multiple found → prefer by capability tier
4. If none found → offer to pull recommended model

---

## Alternatives Considered

| Alternative | Verdict | Reason |
|-------------|---------|--------|
| **Aider** | ❌ Rejected | Interactive, not programmable |
| **LangChain** | ❌ Rejected | Too heavy (50+ deps), overkill |
| **LlamaIndex** | ❌ Rejected | RAG-focused, not tool-focused |
| **AutoGen** | ❌ Rejected | Multi-agent, overkill |
| **CrewAI** | ❌ Rejected | Multi-agent, overkill |
| [**Smolagents**](https://github.com/huggingface/smolagents) | 🔄 Evaluate Phase 2 | Code-as-tool + LocalPythonExecutor sandbox |
| [**MCP Bridge**](https://modelcontextprotocol.io/) | 🔮 Future Phase 3 | If standard gains traction |
| **Web Tools** | ❌ Rejected | Security risk, out of scope |
| **E2B Sandbox** | ❌ Rejected | Requires external service/API key |
| **RestrictedPython** | ⚠️ Considered | Bypassable, weaker than LocalPythonExecutor |

---

## Current Architecture (Approved)

```
Claude Code Skill
    │
    └──► local-brain CLI
            │
            ├──► models.py (model discovery)
            │       │
            │       └──► ollama.list() → smart model selection
            │
            ├──► agent.py (tool loop)
            │       │
            │       └──► ollama.chat(tools=[...])
            │
            └──► tools/
                    ├── file_tools.py   (read_file, list_directory, file_info) [JAILED]
                    ├── git_tools.py    (git_diff, git_status, git_log, git_changed_files)
                    └── shell_tools.py  (run_command with allowlist) [JAILED]
```

### Security Features
- **Path jailing**: All file operations restricted to project root
- **Command allowlist**: Only read-only shell commands permitted
- **No network access**: Prevents data exfiltration
- **Truncation limits**: Large outputs capped to prevent context overflow

### Strengths
- Direct `ollama-python` SDK usage
- ~500 lines of focused code
- 2 dependencies only
- Read-only security posture
- Smart model discovery

### Known Limitations
- Regex-based command allowlist (fragile, Phase 2 will evaluate Smolagents sandbox)
- Basic error handling
- No streaming support (yet)

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

**Keep Local Brain simple and focused.** It serves a specific purpose (Claude Code → Ollama delegation) that mature alternatives like Aider don't address. Improve incrementally, evaluate Smolagents when ready, and watch MCP adoption for future opportunities.

**No web tools** - Claude Code handles web research; Local Brain handles local execution.

---

*Decision approved: December 8, 2025*

