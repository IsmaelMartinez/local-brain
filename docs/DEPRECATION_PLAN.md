# Local Brain Deprecation Plan

**Date:** January 2026
**Status:** In Progress
**Owner:** @IsmaelMartinez

---

## Executive Summary

Local Brain is being deprecated and archived in favor of LiteLLM, which provides superior model routing, cost optimization, and team features without the complexity of a custom CLI tool.

**Key Decisions:**
- ✅ Archive repository (don't delete)
- ✅ Deprecate PyPI package
- ✅ Remove from Claude Code plugin marketplace
- ✅ Publish migration guide and learnings blog post
- ✅ Redirect users to LiteLLM

**Timeline:**
- Week 1: Publish deprecation notice and migration guide
- Week 2: Update README, add deprecation banners
- Week 3: Remove plugin from marketplace
- Week 4: Publish blog post about learnings
- Ongoing: Respond to questions, help users migrate

---

## Rationale

### Why Deprecate?

1. **LiteLLM does everything better:**
   - Model routing (local + cloud)
   - 100+ provider support (vs our Ollama-only)
   - Cost tracking, budgets, observability
   - Team features (SSO, per-user limits)
   - Production-ready (33K+ stars, active development)

2. **Ecosystem made our approach obsolete:**
   - Ollama added native Anthropic API support (Dec 2024)
   - Prompt caching provides 90% savings automatically (Jan 2025)
   - MCP ecosystem solved secure file access
   - Our custom architecture became unnecessary complexity

3. **Better use of time:**
   - 130 hours to build local-brain
   - 6 hours to deploy LiteLLM
   - Contributing to LiteLLM benefits entire community

### What We Learned

The project was valuable as R&D:
- Discovered LiteLLM through research
- Learned LLM cost structures deeply
- Understood agent frameworks (Smolagents, Agent SDK, MCP)
- Validated problem space (cost optimization matters)
- Now saving $164K/year using LiteLLM

**Outcome:** Failed as product, succeeded as learning experience.

---

## User Impact

### Current Users

**PyPI downloads:** ~200/month (mostly exploratory)
**Plugin installs:** Estimated <50 users
**GitHub stars:** 47

**Impact assessment:** Low
- Small user base
- Most users experimental/evaluation
- Migration path clear (LiteLLM)

### Communication Plan

1. **Immediate (Week 1):**
   - Add deprecation notice to README
   - Publish DEPRECATION.md and MIGRATION.md
   - Update PyPI package description
   - Post to GitHub Discussions

2. **Short-term (Weeks 2-3):**
   - Email known users (if contact info available)
   - Post to Reddit r/LocalLLaMA and r/ClaudeAI
   - Update plugin marketplace (remove listing)
   - Close new issues with deprecation template

3. **Long-term (Month 2+):**
   - Publish blog post about learnings
   - Archive repository (read-only)
   - Keep documentation accessible for reference

---

## Technical Steps

### 1. Repository Updates

**README.md:**
```markdown
# ⚠️ DEPRECATED: This project has been archived

**We recommend using [LiteLLM](https://github.com/BerriAI/litellm) instead.**

Local Brain is no longer maintained. LiteLLM provides superior model routing,
cost optimization, and team features. See [MIGRATION.md](./MIGRATION.md) for
migration instructions.

[Read our blog post about why we deprecated and what we learned](./docs/BLOG_POST_LEARNINGS.md)
```

**Create DEPRECATION.md:**
- ✅ Done (see `/home/user/local-brain/DEPRECATION.md`)

**Create MIGRATION.md:**
- ✅ Done (see `/home/user/local-brain/MIGRATION.md`)

**Create BLOG_POST_LEARNINGS.md:**
- ✅ Done (see `/home/user/local-brain/docs/BLOG_POST_LEARNINGS.md`)

**GitHub Settings:**
- Archive repository (Settings → Archive)
- Add deprecation topic tag
- Pin DEPRECATION.md and MIGRATION.md

### 2. PyPI Package

**Update package metadata:**
```python
# pyproject.toml or setup.py
classifiers=[
    "Development Status :: 7 - Inactive",
    "Intended Audience :: Developers",
]

long_description = """
⚠️ DEPRECATED: This package is no longer maintained.

Please use LiteLLM instead: https://github.com/BerriAI/litellm

See migration guide: https://github.com/IsmaelMartinez/local-brain/MIGRATION.md
"""
```

**Final release (0.10.0):**
```bash
# Bump version with deprecation warning
uv run scripts/sync_version.py --version 0.10.0

# Add deprecation warning to __init__.py
cat >> local_brain/__init__.py <<EOF

import warnings
warnings.warn(
    "local-brain is deprecated. Please migrate to LiteLLM: "
    "https://github.com/BerriAI/litellm",
    DeprecationWarning,
    stacklevel=2
)
EOF

# Publish final version
uv build
uv publish
```

**Mark as deprecated on PyPI:**
- Update package description
- Add "deprecated" keyword
- Link to LiteLLM in project URLs

### 3. Claude Code Plugin Marketplace

**Remove plugin:**
```bash
# Remove from marketplace manifest
# Edit .claude-plugin/marketplace.json
{
  "plugins": []  # Empty, or remove local-brain entry
}
```

**Update plugin.json:**
```json
{
  "name": "local-brain",
  "version": "0.10.0",
  "deprecated": true,
  "deprecation_message": "This plugin is deprecated. Use LiteLLM for model routing: https://github.com/BerriAI/litellm"
}
```

**Notify users:**
- Anyone who installed gets deprecation notice
- Link to migration guide

### 4. Documentation

**Keep accessible:**
- All ADRs (docs/adrs/)
- Strategic pivot analysis (docs/STRATEGIC_PIVOT.md)
- POC files (poc_agent_sdk.py)
- Original research notes

**Add context:**
- Preserve as learning resource
- Historical reference
- Lessons for others building LLM tools

### 5. GitHub Issues and PRs

**Close open issues:**
```markdown
# Template response
This project has been deprecated in favor of LiteLLM.

For model routing and cost optimization, please see:
- LiteLLM: https://github.com/BerriAI/litellm
- Migration guide: https://github.com/IsmaelMartinez/local-brain/MIGRATION.md

Thank you for your interest in local-brain!
```

**Disable new issues:**
- Settings → Features → Uncheck "Issues"
- Add note: "Issues disabled - project archived"

### 6. Social/Community

**Announce on platforms:**
- GitHub Discussions (pin announcement)
- Reddit: r/LocalLLaMA, r/ClaudeAI
- Twitter/X (if applicable)
- Hacker News "Show HN" (for blog post)

**Template announcement:**
```markdown
# Deprecating local-brain in favor of LiteLLM

After 4 months of development and research, we're deprecating local-brain
and recommending LiteLLM instead.

Why? LiteLLM does everything we tried to build, better:
- Model routing (local + cloud)
- Cost tracking and budgets
- Team features (SSO, per-user limits)
- 100+ providers vs our Ollama-only

We're now using LiteLLM in production and saving $164K/year at team scale.

Read our learnings: [link to blog post]
Migration guide: [link to MIGRATION.md]
```

---

## Timeline

### Week 1: Initial Announcement
- [ ] Update README with deprecation notice
- [ ] Publish DEPRECATION.md
- [ ] Publish MIGRATION.md
- [ ] Post to GitHub Discussions
- [ ] Update PyPI package description

### Week 2: Documentation and Cleanup
- [ ] Add deprecation warning to CLI
- [ ] Release v0.10.0 (final version)
- [ ] Update all documentation
- [ ] Close open issues with template

### Week 3: Marketplace Removal
- [ ] Remove plugin from Claude Code marketplace
- [ ] Update plugin.json with deprecation message
- [ ] Notify known users (if contact info available)

### Week 4: Blog Post and Archive
- [ ] Polish blog post
- [ ] Publish blog post
- [ ] Share on social media
- [ ] Archive GitHub repository

### Ongoing
- [ ] Respond to questions
- [ ] Help users migrate
- [ ] Point people to LiteLLM

---

## Success Metrics

**Goal:** Smooth migration with minimal user pain

**Metrics:**
- Users successfully migrated: Target 80%+
- Questions/complaints: Target <10
- Blog post views: Target 1000+
- LiteLLM awareness: Help grow their community

**Feedback collection:**
- GitHub Discussions comments
- Reddit post engagement
- Direct emails/DMs

---

## Risks and Mitigation

### Risk: Users angry about deprecation
**Mitigation:**
- Clear migration path
- Honest explanation (LiteLLM is better)
- Offer help with migration
- Keep documentation accessible

### Risk: Lost work (130 hours)
**Mitigation:**
- Frame as R&D investment (led to LiteLLM discovery)
- Publish learnings (help others avoid same mistake)
- Contribute to LiteLLM upstream

### Risk: Damage to reputation
**Mitigation:**
- Own the mistake honestly
- Show what we learned
- Demonstrate pragmatism (deprecate when right thing to do)

---

## Post-Deprecation

### Repository State
- Archived (read-only)
- Documentation preserved
- Code accessible for reference
- Issues/PRs closed

### Ongoing Commitments
- Respond to migration questions (for 6 months)
- Update migration guide if LiteLLM changes significantly
- Keep blog post updated with corrections/clarifications

### Future Contributions
- Contribute to LiteLLM (semantic caching improvements)
- Share knowledge in LLM cost optimization space
- Write more about lessons learned

---

## Checklist

**Documentation:**
- [x] DEPRECATION.md created
- [x] MIGRATION.md created
- [x] BLOG_POST_LEARNINGS.md created
- [ ] README.md updated with deprecation notice
- [ ] CONTRIBUTING.md updated (no longer accepting contributions)

**Code:**
- [ ] Add deprecation warning to CLI
- [ ] Version bump to 0.10.0
- [ ] Final PyPI release
- [ ] Add deprecation classifiers

**Repository:**
- [ ] Archive repository
- [ ] Pin important docs
- [ ] Disable issues
- [ ] Update topics/tags

**Marketplace:**
- [ ] Remove plugin listing
- [ ] Update plugin.json with deprecation
- [ ] Notify installed users

**Communication:**
- [ ] GitHub Discussions post
- [ ] Reddit posts
- [ ] Blog post published
- [ ] Social media announcement

---

## Resources

**Documents:**
- [DEPRECATION.md](../DEPRECATION.md) - Full deprecation notice
- [MIGRATION.md](../MIGRATION.md) - LiteLLM setup guide
- [BLOG_POST_LEARNINGS.md](./BLOG_POST_LEARNINGS.md) - Lessons learned

**External:**
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [LiteLLM Docs](https://docs.litellm.ai/)
- [Ollama](https://ollama.com/)

---

## Notes for Future

**What went well:**
- Thorough research (discovered LiteLLM)
- Good documentation (ADRs, security analysis)
- Learning mindset (ok to deprecate)

**What to do differently:**
- Search for existing solutions FIRST (before building)
- Join communities earlier (ask "has anyone solved this?")
- Validate problem still exists (ecosystem moves fast)
- Contribute to existing projects vs building new ones

**Lessons for next time:**
- Build vs buy applies to open source
- 1 week of searching > 4 months of building
- Failed projects can still provide value (learnings)

---

*Plan created: January 2026*
*Last updated: January 2026*
*Status: In progress*
