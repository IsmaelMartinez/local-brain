# Updated Investigation: Claude Code Skill Delegation Use Case

## Critical Context Change

The original research assumed Local Brain was a **standalone CLI tool** competing with Aider et al. 

**Actual Use Case:**
> Claude Code delegates tasks to Local Brain → Local Brain uses Ollama models → Results return to Claude Code

This is fundamentally different from a user-facing CLI tool.

```
┌─────────────┐     delegates      ┌─────────────┐     calls      ┌─────────┐
│ Claude Code │ ──────────────────►│ Local Brain │ ──────────────►│ Ollama  │
│   (Cloud)   │                    │   (Local)   │                │ (Local) │
│             │◄────────────────── │             │◄────────────── │         │
└─────────────┘     returns        └─────────────┘    responds    └─────────┘
                    results                           with tools
```

---

## Re-Evaluation of Alternatives

### ❌ Aider - NO LONGER FITS

**Why it was recommended:** Interactive CLI for code editing with Ollama support.

**Why it DOESN'T fit now:**
- Aider is **interactive** - designed for human users in a terminal
- No programmatic API for delegation
- Expects user input/confirmation loops
- Can't be called as a subprocess and return structured results

**Verdict:** Aider is for humans, not for Claude Code delegation.

---

### ✅ Smolagents - STRONG CANDIDATE

**Why it's interesting:**
- **Code-as-tool pattern** - model writes Python instead of calling fixed tools
- Sandboxed execution (more secure than regex allowlists)
- Lightweight library from Hugging Face

**Ollama Support:**
Smolagents can use Ollama via LiteLLM integration:

```python
from smolagents import CodeAgent, LiteLLMModel

# Ollama via LiteLLM
model = LiteLLMModel(model_id="ollama/qwen3:latest")

agent = CodeAgent(
    tools=[],  # No predefined tools needed!
    model=model,
    additional_authorized_imports=["os", "git", "pathlib"]
)

# Agent writes Python code to accomplish task
result = agent.run("List all Python files and show git status")
```

**Pros for your use case:**
- ✅ No need to maintain `local_brain/tools/` - agent writes code
- ✅ Sandboxed execution = better security than current approach
- ✅ Can return structured results to Claude Code
- ✅ Supports local models via LiteLLM→Ollama
- ✅ Flexible - any Python library becomes a "tool"

**Cons:**
- ⚠️ Requires capable model (Qwen-Coder, DeepSeek-Coder work well)
- ⚠️ LiteLLM adds a dependency layer
- ⚠️ Code execution is powerful but needs careful sandboxing

**Verdict:** **Best fit** if you want to eliminate tool maintenance entirely.

---

### ⚠️ MCP-Ollama - CLARIFICATION NEEDED

**What MCP is:**
Model Context Protocol is a **standard** for connecting LLMs to data/tools. It defines:
- How tools are described (JSON schemas)
- How tools are invoked
- Transport protocols (stdio, HTTP)

**MCP Servers exist for:**
- Filesystem (read/write files)
- Git operations
- Shell commands
- Databases, etc.

**The Question: Does MCP-Ollama exist?**

There are community projects attempting this, but the key issue is:

| Component | Status |
|-----------|--------|
| MCP Server (filesystem, git) | ✅ Exist (TypeScript) |
| MCP Client for Claude | ✅ Built-in |
| MCP Client for Ollama | ⚠️ **Not native** |

**The Gap:**
- MCP servers exist and work great
- Ollama doesn't natively speak MCP
- You'd need to build a **bridge** that:
  1. Receives tool schemas from MCP servers
  2. Translates them to Ollama's tool format
  3. Calls Ollama with tools
  4. Returns results via MCP protocol

**This is exactly what Local Brain could become!**

```
┌─────────────┐      MCP       ┌─────────────┐    Ollama API   ┌─────────┐
│ Claude Code │ ──────────────►│ Local Brain │ ───────────────►│ Ollama  │
│   (Cloud)   │                │ (MCP Bridge)│                 │         │
└─────────────┘                └─────────────┘                 └─────────┘
                                     │
                                     ▼
                              ┌─────────────┐
                              │ MCP Servers │
                              │ (fs, git)   │
                              └─────────────┘
```

**Verdict:** MCP-Ollama as a full solution doesn't exist yet. Local Brain could **become** this bridge.

---

## Updated Comparison for Claude Code Skill

| Feature | Local Brain (Current) | Smolagents | MCP Bridge (Future) |
|---------|----------------------|------------|---------------------|
| **Programmatic API** | ✅ Can wrap | ✅ Native | ✅ MCP protocol |
| **Ollama Support** | ✅ Native | ✅ Via LiteLLM | ✅ Would build |
| **Tool Maintenance** | ❌ Manual | ✅ None (code-as-tool) | ✅ Use MCP servers |
| **Security** | ⚠️ Regex lists | ✅ Sandbox | ✅ MCP permissions |
| **Structured Output** | ⚠️ Text | ✅ Python objects | ✅ MCP format |
| **Read-Only Mode** | ✅ Current | ✅ Configurable | ✅ Configurable |
| **Write Mode (Future)** | 🔨 Add tools | ✅ Just authorize | ✅ Use MCP fs server |
| **Effort to Implement** | Done | Medium | High |
| **Standards Compliance** | ❌ Custom | ❌ Custom | ✅ MCP Standard |

---

## Recommended Path Forward

### Phase 1: Keep Current + Improve (Now)

**Rationale:** Current implementation works for read-only delegation.

**Actions:**
1. Wrap `run_agent()` for programmatic use (return structured data)
2. Add path jailing (restrict to project root)
3. Keep read-only posture

```python
# Example: Make it callable from Claude Code skill
from local_brain import run_agent

result = run_agent(
    prompt="List changed files and summarize the diff",
    model="qwen3:latest",
    tools=["git_status", "git_diff", "read_file"],
    output_format="json"  # NEW: structured output
)
```

### Phase 2: Evaluate Smolagents (Short-term)

**Rationale:** Code-as-tool eliminates tool maintenance.

**Experiment:**
1. Create a branch with Smolagents integration
2. Test with Qwen-Coder via Ollama
3. Compare: Does code generation work reliably?

```python
# Potential new architecture
from smolagents import CodeAgent, LiteLLMModel

def delegate_to_local(prompt: str, allowed_libs: list[str]) -> dict:
    model = LiteLLMModel(model_id="ollama/qwen3:latest")
    agent = CodeAgent(
        model=model,
        additional_authorized_imports=allowed_libs
    )
    return agent.run(prompt)
```

**If it works:** Delete `local_brain/tools/`, use Smolagents
**If it doesn't:** Keep current tools, Smolagents needs better models

### Phase 3: Consider MCP Bridge (Future)

**Rationale:** If MCP becomes the standard, being the Ollama bridge is valuable.

**When to pursue:**
- MCP adoption increases
- Claude Code adds more MCP features
- Community needs Ollama↔MCP connectivity

---

## Specific Answers to Your Questions

### Does Aider still fit?

**No.** Aider is for interactive human use, not programmatic delegation. It:
- Requires terminal interaction
- Has no API for calling from code
- Expects user confirmations

For Claude Code delegation, you need something callable programmatically.

### What about Smolagents?

**Yes, it's promising.** Key benefits:
- Eliminates need to write/maintain tools
- Model writes Python code to accomplish tasks
- Sandboxed execution
- Works with Ollama via LiteLLM

**But:** Requires a capable coding model (Qwen-Coder, DeepSeek-Coder). Test before committing.

### Will MCP-Ollama provide tool-calling?

**Not directly.** MCP is a protocol, not an implementation. You'd need:

1. **MCP Servers** (exist) - provide the tools
2. **MCP Client** (need to build) - talks to servers
3. **Ollama Bridge** (need to build) - translates MCP↔Ollama tool format

Local Brain could evolve into this bridge, but it's significant work.

---

## The New Recommendation

Given the Claude Code skill use case:

| Priority | Recommendation |
|----------|----------------|
| **Now** | Keep Local Brain, add structured output API |
| **Next** | Experiment with Smolagents branch |
| **Later** | Consider MCP bridge if standard gains traction |

**Why not just use Smolagents now?**
- Current implementation works
- Smolagents requires LiteLLM dependency
- Need to validate code generation quality with local models
- Phased approach reduces risk

**Why Smolagents is the likely future:**
- No tool maintenance
- Better security model
- More flexible
- Aligns with "just use Python libraries" philosophy

---

## Appendix: Quick Reference

### Current Architecture (Keep for now)
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
                    ├── file_tools.py
                    ├── git_tools.py
                    └── shell_tools.py
```

### Smolagents Architecture (Evaluate next)
```
Claude Code Skill
    │
    └──► smolagents wrapper
            │
            └──► CodeAgent
                    │
                    └──► LiteLLM → Ollama
                            │
                            └──► Writes & executes Python
                                 (os, git, pathlib, etc.)
```

### MCP Bridge Architecture (Future possibility)
```
Claude Code Skill
    │
    └──► MCP Client (new)
            │
            ├──► MCP Filesystem Server
            ├──► MCP Git Server
            │
            └──► Ollama Bridge (new)
                    │
                    └──► Ollama (with translated tools)
```

---

*Updated: December 7, 2025*
*Context: Claude Code skill delegation use case*

