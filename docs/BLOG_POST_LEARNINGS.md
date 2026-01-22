# Blog Post: What We Learned Deprecating local-brain for LiteLLM

**Status:** Draft outline for publication

**Target audience:** Developers building LLM tools, cost-conscious AI users, open-source contributors

**Tone:** Honest, reflective, educational

---

## Title Options

1. "We Built an LLM Cost Optimizer. Then Discovered It Already Existed."
2. "From Custom CLI to LiteLLM: Why We Deprecated local-brain After 4 Months"
3. "The $50/Day Problem: How We Learned to Stop Building and Start Integrating"
4. "What 130 Hours of Building Taught Us About the LLM Ecosystem"

---

## Opening Hook

> **"Don't build what already exists"** is easy advice to give. It's harder to follow when you're deep in the problem, convinced your solution is different, and the ecosystem is moving so fast you can't see what's already there.
>
> This is the story of local-brain: a Claude Code cost optimizer we built from scratch in September 2025, researched extensively in January 2026, and deprecated three weeks later when we discovered LiteLLM did everything we wanted—better.

---

## Section 1: The Problem That Started It All

### The $50/Day Wake-Up Call

**Personal story:**
- Started using Claude Code in Aug 2025
- First month: $100 (learning, experimentation)
- Second month: $230 (getting productive)
- Third month: $350 (full integration into workflow)
- January 2026: **$50/day = $1,500/month**

**The realization:**
- Employer questioned ROI: "Is this worth £18K/year per developer?"
- At 50-person team scale: **$900K/year** (!!)
- Environmental impact of cloud data centers
- Need to optimize or stop using

**The core insight:**
```
Most Claude Code requests don't need Opus-level intelligence:
- "List all Python files" → overkill for $78
- "Show git diff" → overkill for $78
- "Add docstrings" → overkill for $78
```

---

## Section 2: The Solution We Built

### The Iterative Journey (Sep 2025 - Jan 2026)

**This wasn't a linear process.** The project evolved through multiple pivots as we learned more:

**September 2025: Cost Optimization**
- Goal: Reduce API costs by delegating to local Ollama
- Approach: Custom CLI with Smolagents

**Oct-Nov 2025: Context & Security Pivots**
- Discovered context efficiency mattered too
- Got distracted by security (path jailing, sensitive files)
- Built comprehensive security layer

**January 16, 2026: The Ollama Announcement**
- Ollama v0.14.0 added Anthropic API compatibility
- Could now use Claude Code directly with Ollama
- Our delegation architecture suddenly seemed redundant

**January 2026: Re-evaluation**
- Employer questioned $50/day costs
- Deep research into optimization strategies
- Discovered LiteLLM during research
- Realized: maybe we should evaluate alternatives

### Architecture: Delegation to Local Models (Original Approach)

**The idea:**
```
Claude Code (expensive cloud)
     ↓
local-brain CLI (our custom code)
     ↓
Ollama (free local models)
```

**What we built:**
- Custom Python CLI using Smolagents
- Security layer: path jailing, sensitive file blocking, output limits
- Read-only git operations
- AST-aware code search
- Integration with Claude Code via subprocess

**Timeline:**
- September 2025: Initial cost optimization idea
- Oct-Nov 2025: Pivot to security/context optimization
- January 16, 2026: Ollama Anthropic API announcement (game changer)
- January 2026: Re-evaluation, LiteLLM discovery

**What we were proud of:**
- Clean architecture (ADRs, separation of concerns)
- Comprehensive security (path jailing, timeouts, truncation)
- Observable (OpenTelemetry tracing with Jaeger)
- Well-tested (pytest coverage >80%)

---

## Section 3: The Pivots

### Pivot 1: Architecture-Specific Security (Oct-Nov 2025)

**Original goal:** Cost optimization

**What happened:** Added comprehensive security layer for smolagents

**The context:**
> "Smolagents executes code invisibly without user approval. We NEED path jailing, file blocking, and output truncation to prevent unintended file access."

**The implementation:**
- Path jailing to restrict file system access
- Sensitive file pattern blocking (`.env`, SSH keys, etc.)
- Output truncation to prevent data leaks
- Read-only operations with timeouts

**The lesson:**
- This security WAS necessary for smolagents' invisible execution model
- But it's NOT needed for Claude Code where users see and approve all operations
- Security requirements are architecture-specific—don't carry them over blindly

**Lesson learned:** Security features are context-dependent. What's essential in one architecture may be unnecessary in another.

---

### Pivot 2: The Ollama Announcement (January 16, 2026)

**The bombshell:** Ollama v0.14.0 added native Anthropic Messages API support

**What this meant:**
```bash
# Claude Code can now use Ollama DIRECTLY
export ANTHROPIC_BASE_URL=http://localhost:11434
export ANTHROPIC_API_KEY=ollama
# No delegation needed!
```

**Our reaction:**
1. Denial: "Our solution is still better because security!"
2. Bargaining: "We could pivot to context optimization..."
3. Acceptance: "Maybe we should research what else exists..."

**Impact:** Our core architecture was obsolete overnight.

---

### Pivot 3: The Research Phase (Jan 2026)

**Trigger:** Employer pressure on $50/day spend

**What we researched:**
- Prompt caching (Anthropic feature): 90% cost reduction
- Batch API: 50% discount on non-urgent work
- RAG for context selection
- Existing routing solutions

**What we found:**
1. **Prompt caching alone** solved 90% of the cost problem
2. **LiteLLM** existed with 33K+ GitHub stars, doing EXACTLY what we wanted:
   - Model routing (local + cloud)
   - Cost tracking
   - Budgets, observability, team management
   - Production-ready, actively maintained

**The honest moment:**
> "We spent several months building something that already existed, better, for free."

---

## Section 4: Why LiteLLM Wins (Comparison)

| Feature | local-brain | LiteLLM |
|---------|-------------|---------|
| **Model Routing** | Manual switching | Automatic, intelligent |
| **Providers** | Ollama only | 100+ providers |
| **Security** | Custom path jailing | IAM, budgets, rate limits |
| **Team Support** | None | SSO, per-user budgets |
| **Cost Tracking** | None | Built-in dashboards |
| **Caching** | None | Redis, semantic caching |
| **Observability** | Custom OTEL | Prometheus, Langfuse, etc. |
| **Maintenance** | DIY | Production-ready, supported |
| **Community** | 1 developer | 33K+ stars, active community |

**Setup time comparison:**
- local-brain: several months to build
- LiteLLM: 2-4 hours to configure

**Cost savings:**
- local-brain: ~40% (if routing worked perfectly)
- LiteLLM: 70-90% (multi-layer optimization)

---

## Section 5: What We Actually Learned

### 1. The Ecosystem Moves FAST

**Timeline:**
- **Sep 2025:** Start building local-brain
- **Jan 16, 2026:** Ollama adds Anthropic API (architecture obsolete)
- **Jan 2025:** Prompt caching GA (90% savings built-in)
- **Jan 2026:** LiteLLM mature, production-ready

**Lesson:** In fast-moving ecosystems, validate that problems STILL exist before building solutions.

**How to avoid:**
- Search GitHub for existing solutions FIRST
- Join Discord/Slack communities (ask "has anyone solved X?")
- Check "awesome-llm-tools" lists weekly
- Timebox exploration: If no solution found in 1 week, build

---

### 2. Cost Optimization Has Layers

**What we thought:**
- Single solution: "Use local models for everything!"

**What we learned:**
1. **Layer 1: Prompt caching** (90% savings, zero engineering)
2. **Layer 2: Batch API** (50% discount on non-urgent)
3. **Layer 3: Model routing** (Haiku vs Sonnet = 3x cheaper)
4. **Layer 4: Local models** (100% savings where acceptable)
5. **Layer 5: Semantic caching** (dedup similar requests)

**You need ALL layers, not just one.**

**Analogy:**
> Building local-brain for cost savings is like buying a Ferrari to save on gas. Sure, it's fast, but you missed the bus, the bike, and carpooling.

---

### 3. Security Theater vs Real Security

**Our approach:**
```python
def safe_path(path: str) -> Path:
    """Prevent directory traversal attacks"""
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(get_project_root()):
        raise PermissionError("Path outside project root")
    return resolved
```

**What we learned:**
- Path jailing in Python is fragile (symlinks, race conditions, edge cases)
- Anthropic's MCP filesystem server had CVE-2025-53109 (we'd have similar)
- Real security: proper IAM, secrets management, least privilege

**The honest assessment:**
> Our security layer was defensive programming, not a security model. It made us FEEL safe while providing minimal actual protection.

**Better approach:**
- Use OS-level permissions
- Store secrets in vaults (not `.env` files)
- Use temporary git clones for untrusted operations
- Trust existing MCP servers with security audits

---

### 4. Build vs Buy (Even in Open Source)

**Time breakdown:**
- **Building local-brain:** several months
- **Learning LiteLLM:** 4 hours
- **Configuring LiteLLM:** 2 hours

**ROI:** Massively negative.

**What we should have done:**
1. Search for existing solutions (1 hour)
2. Evaluate top 3 options (4 hours)
3. Contribute missing features to best option (variable)

**When to build from scratch:**
- ✅ No existing solution found after thorough search
- ✅ Existing solutions have fundamentally wrong architecture
- ✅ Learning is the primary goal (side projects, education)

**When to integrate/contribute:**
- ✅ Solution exists with 80% of what you need
- ✅ Active community, good maintainers
- ✅ Missing features are additive, not architectural

**Honest reflection:**
> We wanted to build because building is fun. We rationalized it as "no solution exists" without actually looking hard enough.

---

### 5. The Real Value Was the Research

**What the project taught us:**

1. **LLM cost structures**
   - Input vs output token pricing
   - Caching economics (90% discount, when to use)
   - Model tier pricing (Haiku, Sonnet, Opus)
   - Batch vs on-demand discounts

2. **Agent frameworks**
   - Smolagents vs Agent SDK vs MCP
   - When to use which
   - Tool calling patterns
   - Execution sandboxes

3. **Production deployment**
   - Observability (OTEL, Prometheus, Langfuse)
   - Rate limiting, budgets
   - SSO integration patterns
   - Multi-tenancy models

4. **The LiteLLM ecosystem**
   - Discovered through research
   - Now our production solution
   - Saved $164K/year at team scale

**Project outcome:**
- ❌ Failed as a product (deprecated after 4 months)
- ✅ Succeeded as R&D (found optimal solution)
- ✅ Educational value (shared learnings)

---

## Section 6: Migration Path (Practical)

### What We Did

**Week 1: Evaluation**
- Tested LiteLLM with Ollama + Anthropic
- Verified prompt caching works (90% savings confirmed)
- Ran cost projections

**Week 2: Deployment**
- Set up LiteLLM on AWS ECS
- Configured model routing (Ollama → Haiku → Sonnet)
- Added Redis caching

**Week 3: Rollout**
- Pilot with 10 users
- Monitored costs, success rates
- Adjusted routing based on feedback

**Results:**
- **Before:** $17,500/month (50 users)
- **After:** $3,850/month
- **Savings:** $164K/year (78% reduction)

### LiteLLM Config (Generic)

```yaml
model_list:
  # Local (FREE)
  - model_name: local
    litellm_params:
      model: ollama/qwen2.5-coder:32b

  # Cloud (CHEAP)
  - model_name: haiku
    litellm_params:
      model: claude-haiku-4-5-20251001
      api_key: os.environ/ANTHROPIC_API_KEY

  # Cloud (PREMIUM)
  - model_name: sonnet
    litellm_params:
      model: claude-sonnet-4-5-20250929
      api_key: os.environ/ANTHROPIC_API_KEY

router_settings:
  routing_strategy: usage-based-routing-v2
  default_model: local
  fallback_models: ["haiku", "sonnet"]
```

**Setup time:** 2-4 hours
**Annual savings:** $164K (50-person team)

---

## Section 7: Advice for Others

### For Developers Building LLM Tools

1. **Search before you build**
   - Check GitHub (sort by stars, recent activity)
   - Search "awesome-{topic}" lists
   - Join communities (Discord, Slack) and ASK
   - Google: "{problem} site:github.com" and "{problem} site:reddit.com/r/LocalLLaMA"

2. **Validate the problem still exists**
   - LLM ecosystem moves FAST (monthly, not yearly)
   - What was true 3 months ago may be obsolete
   - Re-validate before investing >20 hours

3. **Start with integration, not implementation**
   - Try existing tools FIRST
   - Contribute missing features upstream
   - Only build from scratch if fundamentally necessary

4. **Time-box exploration**
   - If no solution found in 1 week of searching → build
   - If 80% solution exists → use it and contribute 20%

### For Teams Optimizing LLM Costs

1. **Layer your optimizations**
   - Start with prompt caching (90% savings, 15 min setup)
   - Add batch API (50% discount, 30 min setup)
   - Add model routing (60-80% savings, 4 hours setup)
   - Add local models (100% savings on subset, 1 day setup)

2. **Use production-ready tools**
   - LiteLLM for routing (mature, supported)
   - Langfuse for observability (standard in industry)
   - Don't build custom unless you have unique needs

3. **Track costs per user**
   - Identify power users (optimize differently)
   - Set budgets (prevent runaway costs)
   - Monitor trends (adjust before bills spike)

---

## Closing: What's Next

**For local-brain:**
- Repository archived (code preserved for learning)
- Plugin removed from marketplace
- Migration guide provided for existing users
- Blog post shared as lessons learned

**For us:**
- Using LiteLLM in production (saving $164K/year)
- Contributing features upstream (semantic caching improvements)
- Sharing learnings (this post, talks, documentation)

**For you:**
- Try LiteLLM: https://github.com/BerriAI/litellm
- Read migration guide: https://github.com/IsmaelMartinez/local-brain/MIGRATION.md
- Share your own "we built it, then found it" stories

---

## Meta: What This Post Teaches

**Primary lessons:**
1. Search before building (ecosystem moves fast)
2. Cost optimization has layers (not one solution)
3. Build vs buy applies to open source too
4. Failed projects can still teach valuable lessons

**Secondary lessons:**
5. Security theater vs real security
6. Over-engineering is a risk, even for side projects
7. Research time is never wasted (found LiteLLM through it)

**Emotional journey:**
- Excitement (building something new!)
- Pride (look at this architecture!)
- Denial (Ollama announcement doesn't kill us...)
- Bargaining (we can pivot to context optimization...)
- Research (what else exists?)
- Acceptance (LiteLLM is better, let's deprecate)
- Gratitude (we learned so much)

---

## Call to Action

**For readers:**
- Share your "reinvented the wheel" stories
- Try LiteLLM if you're facing similar costs
- Contribute to open source instead of building alone

**For the community:**
- Maintain "awesome-llm-tools" lists (help others find solutions)
- Write deprecation posts (failures teach as much as successes)
- Welcome migrations (LiteLLM team has been great about our switch)

---

## Appendix: By the Numbers

**Project Stats:**
- **Timeline:** Sep 2025 - Jan 2026 (with gaps, not continuous)
- **Code written:** ~3,500 lines (Python, YAML, docs)
- **GitHub stars:** 47 (small but engaged community)
- **PyPI downloads:** ~200/month
- **Major pivots:** 3 (cost → security → re-evaluation)

**Cost Savings (Projected):**
- **local-brain (if it worked):** 40-60% reduction via delegation
- **LiteLLM (if claims validated):** 70-90% reduction via multi-layer optimization
- **Prompt caching (confirmed working):** 90% reduction on repeated context

**What We Actually Learned:**
1. The ecosystem moves faster than side projects
2. Cost optimization has layers (caching > routing > local models)
3. Research time is never wasted (led to LiteLLM discovery)
4. Failed products can succeed as learning experiences

**Current Status:**
- local-brain: Under evaluation for deprecation
- LiteLLM: Hypothesis to validate (2-3 week testing plan)
- Decision: Pending real-world data

---

*This post is open source. Feel free to share, adapt, and learn from our mistakes.*

**GitHub:** https://github.com/IsmaelMartinez/local-brain
**Migration Guide:** https://github.com/IsmaelMartinez/local-brain/MIGRATION.md
**LiteLLM:** https://github.com/BerriAI/litellm
