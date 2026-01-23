# LiteLLM Validation Plan

**Goal:** Determine if LiteLLM is a superior alternative to local-brain for cost optimization and model routing.

**Timeline:** 2-3 weeks of testing before making deprecation decision

**Current Status:** Research complete, validation in progress

---

## Hypothesis

LiteLLM can provide:
1. **Better cost savings** (70-90% vs our theoretical 40%)
2. **Easier setup** (2-4 hours vs months of iterative development)
3. **More features** (team management, observability, caching)
4. **Equivalent or better security**
5. **Production-ready reliability**

**This needs to be PROVEN, not assumed.**

---

## Phase 1: Setup and Initial Testing (Week 1)

### 1.1 Install LiteLLM
```bash
pip install 'litellm[proxy]'
```

**Success criteria:**
- ✅ Installs without errors
- ✅ Compatible with our Python version
- ✅ Documentation clear and complete

### 1.2 Basic Configuration
Create config for:
- Bedrock Claude Sonnet (current expensive model)
- Bedrock Claude Haiku (cheap alternative)
- Ollama qwen2.5-coder (local, free)

**Success criteria:**
- ✅ Config syntax makes sense
- ✅ Can connect to all three providers
- ✅ Authentication works (Bedrock IAM, Ollama local)

### 1.3 Claude Code Integration
```bash
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_API_KEY="test-key"
```

**Success criteria:**
- ✅ Claude Code connects successfully
- ✅ Requests route to LiteLLM
- ✅ Tool calling still works
- ✅ No functionality lost

### 1.4 Test Routing Logic
Send 20 test queries:
- 10 simple (should go to Ollama)
- 10 complex (should go to Claude)

**Success criteria:**
- ✅ Simple queries use Ollama
- ✅ Complex queries use Claude
- ✅ Fallback works when Ollama fails
- ✅ No manual intervention needed

---

## Phase 2: Real-World Usage (Week 2)

### 2.1 Daily Work Testing
Use LiteLLM for ALL Claude Code work for 5 days:
- Code generation
- Debugging
- Architecture discussions
- Code review

**Track:**
- Total API cost per day
- Number of requests
- Model distribution (Ollama vs Haiku vs Sonnet)
- Failures/fallbacks
- Subjective quality

**Success criteria:**
- ✅ Cost <$10/day (vs current ~$50/day baseline = 80% savings target)
- ✅ Quality acceptable for 95%+ of tasks
- ✅ Failures <5% of requests
- ✅ No frustrating UX issues

### 2.2 Cost Tracking Validation
Use LiteLLM dashboard to track costs.

**Verify:**
- Costs match AWS bill
- Per-model breakdown accurate
- Can export data for analysis

**Success criteria:**
- ✅ Dashboard shows accurate costs (±5%)
- ✅ Can track daily/weekly trends
- ✅ Can identify expensive queries

### 2.3 Caching Testing
Configure Redis caching, send duplicate/similar queries.

**Test:**
- Exact duplicates (should 100% cache hit)
- Similar queries (semantic caching)
- Cache invalidation (after TTL)

**Success criteria:**
- ✅ Cache hit rate >50% in practice
- ✅ Cached responses fast (<100ms)
- ✅ Semantic caching works (80% similarity threshold)
- ✅ Additional 20-30% cost savings from caching

### 2.4 Performance Testing
Measure latency overhead:
- Direct Bedrock call (baseline)
- Via LiteLLM proxy

**Success criteria:**
- ✅ Overhead <100ms (acceptable)
- ❌ Overhead >500ms (too slow)

### 2.5 Security Comparison

| Feature | local-brain | LiteLLM | Status |
|---------|-------------|---------|--------|
| Path jailing | Custom | IAM policies | ? |
| Sensitive files | Pattern matching | IAM + .gitignore | ? |
| Read-only ops | Tool design | IAM roles | ? |
| Output limits | Truncation | Token limits | ? |
| Timeouts | Per-call | Global config | ? |

**Success criteria:**
- ✅ No security regressions
- ✅ Can achieve equivalent protection via IAM
- ⚠️ Document any gaps

---

## Phase 3: Team Evaluation (Week 3, Optional)

If Phase 1-2 successful, test with 2-3 other team members.

**Goals:**
- Validate setup time (<4 hours per person)
- Test team features (per-user budgets)
- Collect diverse feedback

**Success criteria:**
- ✅ Others can set up in <4 hours
- ✅ No blockers for their workflows
- ✅ Positive feedback (would recommend)

---

## Decision Matrix

| Criterion | Weight | Current Score | Notes |
|-----------|--------|---------------|-------|
| **Cost Savings** | 40% | TBD | Target: >60% reduction |
| **Reliability** | 25% | TBD | Target: >95% success rate |
| **Setup Time** | 15% | TBD | Target: <4 hours |
| **Security** | 10% | TBD | No regressions |
| **UX Quality** | 10% | TBD | Subjective, positive feedback |

**Scoring:**
- 5 = Exceeds expectations
- 4 = Meets expectations
- 3 = Acceptable
- 2 = Below expectations
- 1 = Unacceptable

**Decision rule:**
- Weighted score ≥4.0 → **Deprecate local-brain, adopt LiteLLM**
- Weighted score 3.0-3.9 → **Keep both, reassess in 3 months**
- Weighted score <3.0 → **Keep local-brain, LiteLLM not ready**

---

## Risks and Mitigations

### Risk: LiteLLM routing doesn't work well in practice
**Mitigation:** Test thoroughly before committing. Can revert easily.

### Risk: Hidden costs (infrastructure, maintenance)
**Mitigation:** Factor in EC2, Redis costs. Compare total TCO, not just API costs.

### Risk: Security gaps we didn't notice
**Mitigation:** Security-focused testing. Get second opinion from security engineer.

### Risk: Team adoption issues
**Mitigation:** Pilot with volunteers first. Don't force migration.

### Risk: LiteLLM development stalls
**Mitigation:** Check commit frequency, issue response time, community health.

---

## What We're Testing (Specific Claims)

### Claim 1: "70-90% cost savings"
**Test:** Track actual costs for 2 weeks, compare to baseline.
**Threshold:** Must achieve ≥60% savings.

### Claim 2: "2-4 hour setup"
**Test:** Time yourself setting up from scratch.
**Threshold:** Must be <4 hours for basic config.

### Claim 3: "Intelligent routing"
**Test:** Send 100 queries, check model distribution.
**Threshold:** 70%+ should use cheaper models appropriately.

### Claim 4: "Production-ready"
**Test:** Check uptime, error rates, community support.
**Threshold:** >99% uptime, <1% error rate, active community.

### Claim 5: "Better than local-brain"
**Test:** Compare features, cost, UX side-by-side.
**Threshold:** Must be better in ≥3 of 5 categories.

---

## Data Collection

### Daily Log Template
```markdown
**Date:** YYYY-MM-DD
**Cost:** $X.XX
**Requests:** XX total
**Distribution:**
- Ollama: XX (free)
- Haiku: XX ($X.XX)
- Sonnet: XX ($X.XX)

**Issues:**
- [List any problems]

**Notes:**
- [Subjective observations]
```

### Weekly Summary Template
```markdown
**Week:** X
**Total Cost:** $X.XX (baseline: $350)
**Savings:** XX%

**Success Rate:**
- Successful: XX%
- Failed: XX%
- Fallbacks: XX%

**Key Findings:**
- [What worked well]
- [What didn't]
- [Surprises]

**Recommendation:** Continue / Stop / Adjust
```

---

## Go/No-Go Decision (End of Week 2)

### GO (Proceed with Deprecation) if:
1. ✅ Cost savings ≥60% validated
2. ✅ Reliability >95%
3. ✅ No showstopper issues
4. ✅ Setup time acceptable
5. ✅ Team feedback positive (if tested)

### NO-GO (Keep local-brain) if:
1. ❌ Cost savings <40%
2. ❌ Reliability <90%
3. ❌ Critical security gap identified
4. ❌ Setup too complex (>8 hours)
5. ❌ Team strongly prefers local-brain

### DEFER (More Testing) if:
- Results unclear
- Need more data
- Edge cases found
- Team feedback mixed

---

## Current Status

**Phase:** 1 (Setup and Initial Testing)
**Progress:** Research complete, validation starting
**Blockers:** None identified yet
**Next Step:** Install LiteLLM and configure basic setup

**Last Updated:** 2026-01-22

---

## Questions to Answer

Before deprecating, we need clear answers to:

1. **Does routing actually work?** Or does it require constant manual override?
2. **Are costs ACTUALLY lower?** Or are there hidden fees (infra, bandwidth)?
3. **Is it reliable enough?** Can we depend on it for production work?
4. **Is setup really easy?** Or does the 2-4 hour claim hide complexity?
5. **Do we lose anything?** Features, security, control?

**These are testable questions. Let's test them.**

---

## Appendix: Comparison Checklist

| Feature | local-brain | LiteLLM | Winner |
|---------|-------------|---------|--------|
| **Cost (daily)** | $? (with routing) | $? (measured) | TBD |
| **Setup time** | 0 (already built) | ? hours | TBD |
| **Model routing** | Manual | Automatic | TBD |
| **Cost tracking** | None | Built-in | LiteLLM |
| **Caching** | None | Redis/semantic | LiteLLM |
| **Security** | Path jailing | IAM | TBD |
| **Providers** | Ollama only | 100+ | LiteLLM |
| **Team features** | None | SSO, budgets | LiteLLM |
| **Maintenance** | DIY | Community | LiteLLM |
| **Control** | Full | Depends on config | TBD |

**Final Decision:** TBD (after validation)
