# Strategic Pivot: Post-Ollama Announcement

## Context

**Announcement:** Ollama v0.14.0+ now supports the Anthropic Messages API, enabling Claude Code to run directly on Ollama models without cloud API calls.

**Link:** https://ollama.com/blog/claude

**Impact:** This changes the competitive landscape for Local Brain.

## Current State

**Local Brain v0.9.0:**
- Plugin that delegates tasks to local Ollama via CLI subprocess
- Hybrid architecture: Claude (cloud) + Ollama (local for specific tasks)
- Custom security layer (path jailing, timeouts, read-only tools)
- Requires `uv pip install local-brain` as prerequisite

## The Competition

### Option 1: Claude Code + Ollama (Direct)
```bash
export ANTHROPIC_BASE_URL=http://localhost:11434
export ANTHROPIC_API_KEY=ollama
# Now Claude Code uses Ollama for everything
```

**Pros:**
- ✅ 100% local operation
- ✅ Zero extra dependencies
- ✅ Simpler setup (just env vars)
- ✅ Full privacy

**Cons:**
- ❌ Limited to Ollama model quality
- ❌ No hybrid "best tool for the job"
- ❌ No security constraints (full file access)
- ❌ No specialized read-only tools

### Option 2: Local Brain (Current)
```bash
/plugin install local-brain
uv pip install local-brain
# Delegate specific tasks via CLI
```

**Pros:**
- ✅ Hybrid: Claude for reasoning, Ollama for reads
- ✅ Security constraints (path jailing, read-only)
- ✅ Custom tools optimized for code exploration

**Cons:**
- ❌ Extra installation complexity
- ❌ Subprocess overhead
- ❌ Unclear value prop vs. Option 1

## The Pivot

### New Architecture: Agent SDK Integration

**Local Brain v1.0.0 (Proposed):**
- Native Claude Code agent using Agent SDK
- Connects to Ollama via ANTHROPIC_BASE_URL
- In-process tool execution (no subprocess)
- Same security guarantees (path jailing, etc.)
- No CLI binary dependency

**Installation:**
```bash
/plugin install local-brain
# Configure Ollama endpoint
export ANTHROPIC_BASE_URL=http://localhost:11434
export ANTHROPIC_API_KEY=ollama
```

**Usage:**
```
# Claude Code spawns Local Brain agent via Task tool
# Agent runs on Ollama with secure read-only tools
```

## Value Proposition (Before vs. After)

### Before: "Hybrid Delegation"
> "Local Brain delegates codebase exploration to local Ollama models, keeping reads local while Claude handles complex reasoning"

**Problem:** Users can now just run Claude Code entirely on Ollama. Why delegate?

### After: "Secure Tool Layer for Local Models"
> "Local Brain provides security-constrained read-only tools for Claude Code agents running on Ollama. Path jailed, timeout-protected, no web access—safe local execution."

**Value:**
1. **Security guarantees** - Path jailing prevents escaping project root
2. **Read-only constraints** - No accidental file modifications
3. **Sensitive file blocking** - .env, .pem, SSH keys automatically blocked
4. **Output limits** - Prevents token exhaustion from huge files
5. **No web access** - Prevents data exfiltration and prompt injection

**Target audience:**
- Users who want 100% local operation (Ollama)
- But need security guarantees for agent execution
- And want optimized read-only code exploration tools

## Competitive Positioning

| Feature | Claude Code + Ollama | Local Brain v1.0 |
|---------|---------------------|------------------|
| 100% local | ✅ | ✅ |
| No installation | ✅ | ❌ (plugin install) |
| Path jailing | ❌ | ✅ |
| Sensitive file protection | ❌ | ✅ |
| Read-only enforcement | ❌ | ✅ |
| Output size limits | ❌ | ✅ |
| Custom code tools | ❌ | ✅ (AST search, etc.) |
| Web access blocked | ❌ | ✅ |

**The pitch:** "If you're running Claude Code on Ollama, add Local Brain for security-constrained code exploration."

## What Changes

### Code
- ✅ Keep: All of `security.py` (unchanged)
- ✅ Keep: Tool implementations (logic unchanged)
- 🔄 Rewrite: `smolagent.py` → `agent_sdk.py`
- 🔄 Adapt: Tool return format for Agent SDK
- ❓ TBD: Keep `cli.py` for standalone use?

### Documentation
- 🔄 README: Rewrite value prop
- 🔄 SKILL.md: Update usage instructions
- ➕ Add: Migration guide
- ➕ Add: Security benefits explainer

### Installation
- ❌ Remove: `uv pip install` requirement
- ➕ Add: Environment variable configuration
- ✅ Keep: Ollama prerequisite

### Positioning
- ❌ Remove: "Hybrid cloud + local architecture"
- ➕ Add: "Security layer for local model execution"
- ✅ Keep: "Read-only code exploration tools"

## Migration Path

### Phase 1: Proof of Concept ✅ **DONE**
- [x] Research Agent SDK documentation
- [x] Create POC with one tool (`poc_agent_sdk.py`)
- [x] Document migration strategy

### Phase 2: Port All Tools
- [ ] Port 9 tools to Agent SDK format
- [ ] Preserve all security.py logic
- [ ] Test path jailing, timeouts, etc.
- [ ] Verify output truncation works

### Phase 3: Integration
- [ ] Create agent definition for Claude Code
- [ ] Test with Ollama v0.14.0+
- [ ] Verify Task tool spawning
- [ ] Test error handling

### Phase 4: Documentation
- [ ] Update README with new positioning
- [ ] Rewrite SKILL.md usage guide
- [ ] Add security benefits explainer
- [ ] Create migration guide for users

### Phase 5: Release
- [ ] Version 1.0.0 (breaking change)
- [ ] Deprecate CLI (or keep for standalone use?)
- [ ] Announce pivot
- [ ] Update marketplace

## Timeline

**Complexity:** Medium (mostly porting, security logic stays same)

**Estimated Effort:**
- Porting tools: 1-2 days
- Integration testing: 1 day
- Documentation: 1 day
- Testing & polish: 1 day

**Total:** ~5 days of focused work

## Risk Analysis

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|---------|------------|
| Ollama API incomplete | Low | High | Test thoroughly with all tools |
| Agent SDK limitations | Medium | High | POC validates feasibility |
| Performance regression | Low | Medium | Benchmark subprocess vs. in-process |
| Security gaps in Agent SDK | Low | Critical | Rely on tool-layer security |

### Product Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|---------|------------|
| Users prefer plain Ollama | High | Medium | Emphasize security value |
| Market too niche | Medium | Medium | Focus on security-conscious users |
| Breaking change backlash | Low | Low | Clear migration guide, v1.0 signals change |

### Strategic Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|---------|------------|
| Agent SDK changes API | Medium | High | Pin versions, monitor releases |
| Ollama drops Anthropic API | Low | Critical | Would kill entire approach |
| Claude Code adds own security | Low | Medium | Our tools still provide value |

## Decision Criteria

### Go Forward If:
1. ✅ POC works with Ollama
2. ✅ All 9 tools port successfully
3. ✅ Security guarantees preserved
4. ✅ Performance is acceptable
5. ✅ Agent SDK stable enough

### Abort If:
1. ❌ Agent SDK can't register custom tools
2. ❌ Ollama API incompatible with critical features
3. ❌ Security model fundamentally broken
4. ❌ Performance unacceptably slow

## Recommendation

**PROCEED WITH PIVOT**

**Reasoning:**
1. **Validates core value** - Security is the real differentiator, not the plumbing
2. **Simplifies architecture** - No subprocess, no CLI binary
3. **Better UX** - Native Task integration
4. **Clear positioning** - "Security layer" vs. "hybrid delegation"
5. **Feasible migration** - Tools port cleanly, security logic unchanged

**The Ollama announcement doesn't invalidate Local Brain—it clarifies its purpose.**

You're not competing with "local vs. cloud." You're providing **security guardrails for local model execution**.

## Next Actions

1. **Validate POC** - Test `poc_agent_sdk.py` against Ollama
2. **Port tools** - Migrate all 9 tools to Agent SDK format
3. **Test security** - Verify path jailing, timeouts, blocking all work
4. **Update docs** - Rewrite README with new positioning
5. **Release v1.0** - Clean break, new architecture

## Open Questions

1. **Standalone CLI** - Keep for non-plugin users, or remove entirely?
   - **Recommendation:** Remove. Plugin-only simplifies maintenance.

2. **Model selection** - How do users choose Ollama models?
   - **Option A:** Environment variable `OLLAMA_MODEL`
   - **Option B:** Plugin configuration file
   - **Option C:** Let Claude Code choose (via Task args)
   - **Recommendation:** Option A for simplicity

3. **Observability** - Can we preserve OTEL tracing?
   - Need to investigate Agent SDK telemetry
   - May need to adapt or drop this feature

4. **Backward compatibility** - Support old CLI during transition?
   - **Recommendation:** No. Clean v1.0 break.

## Conclusion

The Ollama announcement is an **opportunity, not a threat**.

Your original insight—"local models + security constraints + custom tools"—is validated. The implementation just needs to evolve from "CLI subprocess" to "native agent."

**The tools are the value. The framework is just plumbing.**

Make the pivot. Simplify the architecture. Focus on the security story.

**Local Brain v1.0: Secure tools for local model execution.**
