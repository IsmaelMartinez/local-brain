# Project Deprecation Notice (DRAFT - UNDER EVALUATION)

**Status:** Evaluating deprecation as of January 2026

**TL;DR:** We're evaluating whether to deprecate Local Brain in favor of LiteLLM. Initial research suggests LiteLLM may provide superior model routing, cost optimization, and multi-provider support without the complexity of a custom CLI tool.

**This document represents our HYPOTHESIS, not a final decision. We need to validate LiteLLM actually delivers on these promises before deprecating.**

---

## Validation Plan (DO THIS FIRST)

Before deprecating, we need to TEST these claims:

### Week 1-2: LiteLLM Evaluation
1. **Setup LiteLLM** with Bedrock + Ollama routing
2. **Test routing logic** - Does it actually route intelligently?
3. **Verify cost tracking** - Are dashboards accurate?
4. **Test caching** - Does semantic caching work as advertised?
5. **Measure overhead** - What's the latency penalty?
6. **Compare security** - Are we losing security features?

### Week 3: Real-World Testing
1. **Use LiteLLM for actual work** (not just demos)
2. **Track costs daily** - Is it actually cheaper?
3. **Monitor failures** - How often does routing fail?
4. **Collect user feedback** - Is UX better or worse?

### Decision Criteria

**Proceed with deprecation IF:**
- ✅ Cost savings ≥60% (validated, not projected)
- ✅ Routing works reliably (>95% success rate)
- ✅ Setup time <4 hours for new users
- ✅ No major security regressions
- ✅ User feedback positive

**Keep local-brain IF:**
- ❌ Cost savings <40% in practice
- ❌ Routing frequently fails or needs manual intervention
- ❌ Setup complexity too high
- ❌ Security model fundamentally worse
- ❌ Performance unacceptable

**Current status:** HYPOTHESIS - needs validation

---

## Why This Project Exists

Local Brain was created to solve three problems:

1. **Cost Optimization**: Reduce Claude API costs by delegating simple tasks to local Ollama models
2. **Context Efficiency**: Avoid sending unnecessary context to expensive cloud models
3. **Security/Privacy**: Keep sensitive codebase exploration local via path-jailed, read-only tools

### Original Architecture

```
Claude Code (Cloud)
     ↓ subprocess
local-brain CLI (Smolagents + Ollama)
     ↓ custom security layer
Local Ollama Models
```

**Key features:**
- Custom Python CLI with security-wrapped tools
- Path jailing, sensitive file blocking, output truncation
- Read-only git operations
- AST-aware code search

---

## What Changed

### January 16, 2026: Ollama + Anthropic API Compatibility

Ollama v0.14.0+ added native support for Anthropic's Messages API, enabling Claude Code to connect directly to local models:

```bash
export ANTHROPIC_BASE_URL=http://localhost:11434
export ANTHROPIC_API_KEY=ollama
# Claude Code now uses Ollama directly
```

**Impact:** Eliminated the need for delegation architecture. Users could run Claude Code 100% locally.

### January 2026: Research Findings

After extensive research into cost optimization at scale ($50/day → $1,500/month individual usage), we discovered:

1. **Prompt caching** (native Anthropic/Bedrock feature) provides 90% cost reduction automatically
2. **LiteLLM** offers production-ready model routing with:
   - Support for 100+ providers (Bedrock, Ollama, OpenRouter, Anthropic direct)
   - Intelligent routing (cost-based, semantic, load-balanced)
   - Built-in observability, budgets, caching
   - Team management, SSO, enterprise features
   - Active development (33K+ GitHub stars)

3. **Our custom CLI approach** became redundant:
   - LiteLLM's security model handles access control
   - No need for custom path jailing (use proper IAM/permissions)
   - AST tools available as MCP servers (ecosystem solved this)

---

## Why LiteLLM Wins

| Aspect | Local Brain | LiteLLM |
|--------|-------------|---------|
| **Routing** | Manual switching | Automatic, intelligent |
| **Providers** | Ollama only | 100+ providers |
| **Use Case** | Smolagents sandboxing | Model routing/cost optimization |
| **Team Support** | None | SSO, per-user budgets |
| **Observability** | None | Prometheus, Langfuse, etc. |
| **Maintenance** | Custom code | Production-ready, supported |
| **Cost Tracking** | None | Built-in dashboards |
| **Caching** | None | Redis, semantic caching |

**The honest assessment:** LiteLLM is what we SHOULD have built, but the open-source community already did it better.

---

## Migration Guide

### If You Were Using Local Brain for Cost Savings

**Replace with: LiteLLM + Model Routing**

```bash
# Install LiteLLM
pip install 'litellm[proxy]'

# Create config
cat > litellm_config.yaml <<EOF
model_list:
  # Free local model (replaces local-brain)
  - model_name: ollama-local
    litellm_params:
      model: ollama/qwen2.5-coder:32b
      api_base: http://localhost:11434

  # Cloud fallback for complex tasks
  - model_name: claude-sonnet
    litellm_params:
      model: claude-sonnet-4-5-20250929
      api_key: os.environ/ANTHROPIC_API_KEY

router_settings:
  routing_strategy: usage-based-routing-v2
  default_model: ollama-local
  fallback_models: ["claude-sonnet"]
EOF

# Start proxy
litellm --config litellm_config.yaml --port 4000

# Configure Claude Code
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_API_KEY="sk-anything"
```

**Benefits over local-brain:**
- Automatic routing (no manual switching)
- Fallback when local model fails
- Cost tracking dashboard
- Works with ANY LLM provider

---

### If You Were Using Local Brain for Security

**Replace with: Nothing - Security Layer No Longer Needed**

The security features (path jailing, file blocking, output truncation) were necessary **only because smolagents was executing code invisibly** without user visibility or control.

**Why it's no longer needed:**
- **Claude Code**: You see and approve all operations before execution
- **LiteLLM**: Acts as a model router/proxy, doesn't execute code
- **No invisible execution**: Everything goes through Claude Code's standard tool execution with full visibility

**The new architecture:**
```
Claude Code (you see and control everything)
     ↓
LiteLLM (just routing, no execution)
     ↓
Multiple LLM Providers (Bedrock, Ollama, etc.)
```

**Lesson learned:** Security theater for a specific architecture (smolagents) doesn't transfer to different architectures (Claude Code). Each system has its own security model - don't recreate features that aren't needed.

---

### If You Were Using Local Brain for Context Optimization

**Replace with: Prompt Caching + Semantic Caching**

1. **Enable prompt caching** (90% savings on repeated context):
   ```python
   # Automatic with Anthropic API
   # Just upgrade to latest SDK
   ```

2. **Add semantic caching via LiteLLM**:
   ```yaml
   cache_params:
     type: redis-semantic
     similarity_threshold: 0.8
     ttl: 3600
   ```

3. **Use RAG for large codebases**:
   - [claude-context-local](https://github.com/FarhanAliRaza/claude-context-local) - Local embeddings + selective context
   - LlamaIndex with local Ollama embeddings

**Lesson learned:** Context compression via local LLMs was interesting but unnecessary. Prompt caching + RAG solve this better.

---

## What We Learned (Blog Post Material)

### 1. The Ecosystem Moves Fast

**Timeline:**
- **September 2025:** Local Brain started to solve delegation/cost problems
- **January 16, 2026: Ollama adds Anthropic API compatibility (our core architecture obsolete)
- **January 2025:** Prompt caching GA on Bedrock (90% cost reduction built-in)
- **January 2026:** LiteLLM at 33K stars, production-ready for everything we tried to build

**Lesson:** In fast-moving ecosystems, validate that a problem STILL exists before building solutions. Check if the community already solved it.

---

### 2. Cost Optimization Has Layers

**What we thought:**
- Problem: Expensive API calls
- Solution: Delegate to local models

**What we learned:**
1. **Layer 1: Prompt caching** (90% savings, zero effort)
2. **Layer 2: Model routing** (60-80% additional savings on remaining)
3. **Layer 3: Batch API** (50% discount on non-urgent work)
4. **Layer 4: Local models** (100% savings where quality acceptable)

**You need ALL layers, not just one.** LiteLLM enables this. Our custom CLI only did Layer 4.

---

### 3. Context-Specific Security

**Our approach (for smolagents):**
- Path jailing in Python
- Sensitive file pattern matching
- Output truncation
- Custom sandbox

**Why it was necessary:**
- Smolagents executed code invisibly without user control
- Needed sandboxing to prevent unintended file access

**Why it's not needed with Claude Code + LiteLLM:**
- Claude Code: User sees and approves all operations
- LiteLLM: Just a model router, doesn't execute code
- No invisible code execution = no need for custom sandboxing

**Lesson:** Security requirements depend on the architecture. Don't carry over security features from one system to another without validating they're still needed.

---

### 4. The 80/20 of Cost Savings

**80% of savings comes from:**
1. Prompt caching (enable it, done)
2. Using Haiku instead of Opus for simple tasks
3. Local models for trivial work

**20% of savings comes from:**
- Custom routing logic
- Semantic caching
- Advanced RAG pipelines

**Most users need the 80%, not the 20%.** LiteLLM gives you the 80% in 30 minutes of setup.

---

### 5. Build vs Buy (Open Source Edition)

**Time invested in local-brain:**
- ~40 hours designing architecture
- ~60 hours implementing tools, security, tracing
- ~20 hours testing, debugging
- ~10 hours documentation

**Total: ~several months of iteration**

**LiteLLM setup time:** 2-4 hours

**ROI:** Negative. Should have contributed to LiteLLM instead.

**Lesson:** Even in open source, prefer integrating existing solutions over building from scratch. Contribute upstream if features are missing.

---

### 6. What WAS Valuable

Despite deprecation, the project taught us:

1. **LLM cost structures:** Input vs output tokens, caching economics, model pricing tiers
2. **Agent frameworks:** Smolagents, Agent SDK, MCP - how they differ and when to use each
3. **Security constraints:** What path jailing actually requires, why it's hard
4. **Real cost pain points:** $50/day → $1,500/month is where optimization becomes critical
5. **The LiteLLM ecosystem:** Discovered it through research, now our production solution

**The project failed as a product but succeeded as R&D.**

---

## For Users Who Installed local-brain

### Uninstall

```bash
# Remove CLI
pipx uninstall local-brain
# or
uv tool uninstall local-brain

# Remove plugin
/plugin uninstall local-brain@local-brain-marketplace
/plugin marketplace remove IsmaelMartinez/local-brain
```

### Recommended Replacement

See [MIGRATION.md](./MIGRATION.md) for detailed LiteLLM setup guide.

**Quick start:**
```bash
pip install 'litellm[proxy]'
litellm --model ollama/qwen2.5-coder:32b --port 4000
export ANTHROPIC_BASE_URL=http://localhost:4000
```

---

## Repository Status

- **Code:** Archived, no further development
- **Issues:** Closed, redirecting to LiteLLM
- **Plugin:** Removed from marketplace
- **PyPI package:** Deprecated, use LiteLLM
- **Documentation:** Preserved for historical reference

---

## Thank You

To everyone who:
- Tested early versions
- Reported issues
- Provided feedback
- Shared ideas

Your input helped validate the problem space and led us to discover LiteLLM as the superior solution.

---

## Resources

**Migration:**
- [MIGRATION.md](./MIGRATION.md) - Detailed LiteLLM setup guide
- [docs/LITELLM_VALIDATION_PLAN.md](./docs/LITELLM_VALIDATION_PLAN.md) - Testing plan

**LiteLLM:**
- [GitHub](https://github.com/BerriAI/litellm)
- [Documentation](https://docs.litellm.ai/)
- [Bedrock Setup](https://docs.litellm.ai/docs/providers/bedrock)

**Blog Post:**
- [Coming soon] "What We Learned Deprecating local-brain for LiteLLM"

---

*This project is archived but not deleted. The code remains available for historical reference and learning purposes.*
