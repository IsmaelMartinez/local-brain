# Migration to Claude Agent SDK

## Executive Summary

**Status:** Feasible and recommended

The Ollama v0.14.0 announcement enabling Anthropic API compatibility allows us to **eliminate the CLI binary dependency** and integrate directly into Claude Code using the Claude Agent SDK.

## Why Migrate?

### Current Architecture (Smolagents + CLI)
```
Claude Code (Cloud)
     ↓ subprocess.run()
local-brain CLI (Python binary)
     ↓ LiteLLM
Ollama (localhost:11434)
```

**Problems:**
- ❌ Extra installation step (`uv pip install local-brain`)
- ❌ Subprocess coordination overhead
- ❌ Separate process boundary
- ❌ Not integrated with Claude Code's Task system

### Proposed Architecture (Agent SDK + Ollama)
```
Claude Code (Cloud)
     ↓ Task tool (native)
Custom Agent (Agent SDK)
     ↓ ANTHROPIC_BASE_URL=localhost:11434
Ollama (Local)
```

**Benefits:**
- ✅ No binary dependency (just plugin install)
- ✅ Native Task integration
- ✅ In-process tool execution
- ✅ Proper progress indicators
- ✅ Same security guarantees

## Security Model Comparison

### What Stays the Same

All security logic from `local_brain/security.py` is **preserved identically**:

| Security Feature | Current | Migrated | Notes |
|-----------------|---------|----------|-------|
| Path jailing | ✅ | ✅ | Same `safe_path()` function |
| Sensitive file blocking | ✅ | ✅ | Same `is_sensitive_file()` |
| Output truncation | ✅ | ✅ | Same `truncate_output()` |
| Per-call timeouts | ✅ | ✅ | Same `@with_timeout` decorator |
| Read-only operations | ✅ | ✅ | Same tool implementations |
| Project root jailing | ✅ | ✅ | Same `set_project_root()` |

### What Changes

| Aspect | Current | Migrated |
|--------|---------|----------|
| Execution sandbox | LocalPythonExecutor (Smolagents) | In-process (Agent SDK) |
| Tool registration | `@tool` (Smolagents) | `@tool` (Agent SDK MCP) |
| Process boundary | Subprocess | Same process |

**The key insight:** Your security is in the **tool implementations**, not the framework. The migration preserves all security code.

## Implementation Steps

### Phase 1: Port Tools to Agent SDK Format

**Current (Smolagents):**
```python
from smolagents import tool

@tool
def read_file(path: str) -> str:
    resolved = safe_path(path)
    if is_sensitive_file(resolved):
        return f"Error: Access denied"
    return resolved.read_text()
```

**Migrated (Agent SDK):**
```python
from claude_agent_sdk import tool
from typing import Any

@tool("read_file", "Read a file", {"path": str})
async def read_file(args: dict[str, Any]) -> dict[str, Any]:
    resolved = safe_path(args["path"])
    if is_sensitive_file(resolved):
        return {
            "content": [{"type": "text", "text": "Error: Access denied"}],
            "isError": True
        }
    content = resolved.read_text()
    return {"content": [{"type": "text", "text": content}]}
```

**Key differences:**
1. Return format: `dict[str, Any]` instead of `str`
2. Arguments: `args: dict` instead of typed parameters
3. Async: `async def` required
4. Content wrapper: `{"content": [{"type": "text", "text": "..."}]}`

### Phase 2: Create MCP Server

```python
from claude_agent_sdk import create_sdk_mcp_server

# All your ported tools
tools_server = create_sdk_mcp_server(
    name="local-brain",
    version="0.9.0",
    tools=[
        read_file,
        list_directory,
        file_info,
        git_diff,
        git_status,
        git_log,
        git_changed_files,
        search_code,
        list_definitions,
    ]
)
```

### Phase 3: Configure Agent Options

```python
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    system_prompt=(
        "You are a codebase exploration assistant. "
        "Use the provided tools to analyze code, review changes, "
        "and explore repositories. All operations are read-only "
        "and path-jailed to the project root."
    ),
    model="qwen3-coder:30b",  # Or user-selected model
    mcp_servers={"tools": tools_server},
    allowed_tools=[
        "mcp__tools__read_file",
        "mcp__tools__list_directory",
        "mcp__tools__file_info",
        "mcp__tools__git_diff",
        "mcp__tools__git_status",
        "mcp__tools__git_log",
        "mcp__tools__git_changed_files",
        "mcp__tools__search_code",
        "mcp__tools__list_definitions",
    ],
    cwd="/path/to/project",
)
```

### Phase 4: Update Plugin to Use Task

**Current plugin (skill):**
```bash
# SKILL.md just documents the CLI
local-brain "Analyze the codebase"
```

**Migrated plugin:**
The skill would invoke the agent using Claude Code's Task API, passing the Ollama configuration.

## Environment Configuration

Users will need to configure Ollama as their Anthropic API backend:

```bash
# ~/.bashrc or ~/.zshrc
export ANTHROPIC_BASE_URL=http://localhost:11434
export ANTHROPIC_API_KEY=ollama
```

Then the plugin automatically uses this configuration.

## Code Organization

### Files to Migrate

| Current File | Migrated Purpose |
|-------------|------------------|
| `local_brain/security.py` | ✅ Keep as-is (no changes) |
| `local_brain/smolagent.py` | 🔄 Rewrite as `agent_sdk.py` |
| `local_brain/models.py` | ⚠️ May need for model selection |
| `local_brain/cli.py` | ❓ Keep for standalone CLI? |
| `local_brain/tracing.py` | 🔄 Adapt for Agent SDK if possible |

### Files to Create

- `local_brain/agent_sdk.py` - Agent SDK integration
- `local_brain/mcp_tools.py` - Tool definitions in MCP format
- `docs/MIGRATION_AGENT_SDK.md` - This document

## Tool Migration Checklist

Port all 9 tools to Agent SDK format:

- [ ] `read_file` - File reading with path jailing
- [ ] `list_directory` - Directory listing with filtering
- [ ] `file_info` - File metadata
- [ ] `git_diff` - Git diff output
- [ ] `git_status` - Git status
- [ ] `git_log` - Commit history
- [ ] `git_changed_files` - Changed file list
- [ ] `search_code` - AST-aware code search
- [ ] `list_definitions` - Extract class/function signatures

## Testing Strategy

1. **Unit tests** - Verify each tool works with Agent SDK
2. **Integration tests** - Test full agent with Ollama
3. **Security tests** - Verify path jailing still works
4. **Performance tests** - Compare to Smolagents version

## Rollout Plan

### Option A: Hard Cut-Over
1. Migrate all tools
2. Release v1.0.0 with Agent SDK
3. Deprecate CLI entirely
4. Update all documentation

**Pros:** Clean break, simpler codebase
**Cons:** Breaking change for existing users

### Option B: Dual Support
1. Keep existing CLI for standalone use
2. Add new Agent SDK plugin variant
3. Support both paths initially
4. Gradually deprecate CLI

**Pros:** Backward compatible
**Cons:** More complexity, two code paths

### Recommendation: **Option A**

The plugin is experimental (v0.9.0), user base is small, and the migration provides clear benefits. A clean cut-over is justified.

## New Positioning

### Before (Hybrid Architecture)
> "Local Brain delegates codebase exploration to local Ollama models via a CLI tool"

**Problem:** Competes with "just use Claude Code + Ollama"

### After (Security Layer)
> "Local Brain provides security-constrained read-only tools for Claude Code agents running on Ollama. Path jailed, timeout-protected, no web access."

**Value:** Security guarantees for local model execution

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|---------|------------|
| Agent SDK API changes | Medium | High | Pin version, monitor releases |
| Ollama API incompatibility | Low | High | Test thoroughly, document requirements |
| Breaking change for users | High | Low | Good docs, clear migration guide |
| Performance regression | Low | Medium | Benchmark before/after |
| Security gaps | Low | Critical | Reuse existing security.py, add tests |

## Success Criteria

Migration is successful when:

1. ✅ All 9 tools ported and working
2. ✅ Security tests pass (path jailing, timeouts, etc.)
3. ✅ Works with Ollama v0.14.0+
4. ✅ No subprocess overhead
5. ✅ Native Task integration in Claude Code
6. ✅ Documentation updated
7. ✅ Performance is comparable or better

## Open Questions

1. **Model selection** - How to expose model choice to users?
   - Via environment variable?
   - Via plugin configuration?
   - Let Claude Code choose?

2. **Standalone CLI** - Keep it or remove it?
   - If removed: Plugin-only
   - If kept: Dual mode (CLI + plugin)

3. **Tracing/observability** - Can we preserve OTEL tracing?
   - Agent SDK may have its own telemetry
   - Need to investigate integration

4. **Error handling** - How do Agent SDK errors surface?
   - Need to test error propagation
   - Ensure user-friendly messages

## Next Steps

1. Create POC with one tool (read_file) ✅ **DONE** (see `poc_agent_sdk.py`)
2. Test POC against Ollama
3. Port all 9 tools
4. Update plugin skill to use agent
5. Update documentation
6. Release v1.0.0

## References

- [Claude Agent SDK Documentation](https://platform.claude.com/docs/en/agent-sdk/python)
- [Ollama Anthropic API Compatibility](https://ollama.com/blog/claude)
- [POC Implementation](../poc_agent_sdk.py)
- [Current Smolagents Implementation](../local_brain/smolagent.py)
- [Security Module (unchanged)](../local_brain/security.py)
