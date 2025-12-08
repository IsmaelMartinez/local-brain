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

| Task | Priority |
|------|----------|
| Add path jailing (restrict to project root) | High |
| Add structured JSON output option | High |
| Add tests for allowlist/denylist behavior | Medium |
| Add retry logic for Ollama calls | Low |

### Phase 2: Next - Evaluate Smolagents

**What:** Code-as-tool pattern where model writes Python instead of calling fixed tools.

**Why consider:**
- Eliminates tool maintenance entirely
- Sandboxed execution (better than regex allowlists)
- Model writes `import os; os.listdir('.')` instead of calling `list_directory` tool

**Experiment:**
1. Create `feature/smolagents` branch
2. Test with Qwen-Coder via Ollama
3. Validate code generation quality
4. If works: Replace `local_brain/tools/`
5. If doesn't: Keep current approach

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

---

## Alternatives Considered

| Alternative | Verdict | Reason |
|-------------|---------|--------|
| **Aider** | ❌ Rejected | Interactive, not programmable |
| **LangChain** | ❌ Rejected | Too heavy (50+ deps), overkill |
| **LlamaIndex** | ❌ Rejected | RAG-focused, not tool-focused |
| **AutoGen** | ❌ Rejected | Multi-agent, overkill |
| **CrewAI** | ❌ Rejected | Multi-agent, overkill |
| [**Smolagents**](https://github.com/huggingface/smolagents) | 🔄 Evaluate | Promising code-as-tool pattern |
| **MCP Bridge** | 🔮 Future | If standard gains traction |

---

## Current Architecture (Approved)

```
Claude Code Skill
    │
    └──► local-brain CLI
            │
            ├──► agent.py (tool loop)
            │       │
            │       └──► ollama.chat(tools=[...])
            │
            └──► tools/
                    ├── file_tools.py   (read_file, list_directory, file_info)
                    ├── git_tools.py    (git_diff, git_status, git_log, git_changed_files)
                    └── shell_tools.py  (run_command with allowlist)
```

### Strengths
- Direct `ollama-python` SDK usage
- ~450 lines of focused code
- 2 dependencies only
- Read-only security posture

### Known Limitations
- Regex-based command allowlist (fragile)
- No path jailing
- No structured output format
- Basic error handling

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

---

*Decision approved: December 8, 2025*

