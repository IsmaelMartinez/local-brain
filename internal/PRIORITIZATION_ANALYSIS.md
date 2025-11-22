# Exploration Ideas Prioritization Analysis

**Analysis Date:** November 21, 2025
**Context:** Solo developer, 5 hours/week, 2-week personal workflow goal, 1-month community distribution goal
**Constraints:** 16GB RAM (models ≤9GB, prefer ≤7GB), macOS, Ollama installed

---

## ✅ Completed Features

### 1. **Model Specialization** ✅ (4-6 hours) - COMPLETE
- Downloaded and tested multiple models (qwen2.5-coder:3b, llama3.2:1b, phi3:mini, deepseek-coder-v2:16b)
- Created models.json registry with task mappings
- All models validated with 100% test pass rate
- **Fixed model registry mismatch** (deepseek-coder-v2:8k → deepseek-coder-v2-8k)

### 2. **Targeted Model Selection** ✅ (3-4 hours) - COMPLETE
- Implemented `--task` flag for automatic model selection
- Implemented `--model` flag for explicit model override
- Priority system: CLI --model > JSON > --task > default

### 3. **Git Diff Integration** ✅ (3-4 hours) - COMPLETE
- Implemented `--git-diff` flag
- Staged files with fallback to unstaged
- Aggregated results with filename context

### 4. **Distribution Guide** ✅ (4-6 hours) - COMPLETE
- Created INSTALLATION.md, QUICKSTART.md, CONTRIBUTING.md
- Refactored README.md (60 lines)
- Simplified all docs using KISS/DRY principles
- **Updated for binary distribution**

### 5. **Directory & File Walking** ✅ (8-12h) - COMPLETE
- Implemented `--dir` and `--pattern` flags
- Implemented `--files` flag for comma-separated lists
- Recursive traversal with pattern matching (*.rs, *.{js,ts})
- Auto-skip hidden dirs and common ignores

### 6. **GitHub Actions CI/CD Pipeline** ✅ (2-3 hours) - COMPLETE
- Implemented CI workflow (test on Ubuntu, macOS, Windows)
- Implemented release workflow with cross-platform builds
- Automated binary distribution via GitHub Releases
- Added cargo-binstall support
- Optimized binary size (strip + panic=abort)
- Created RELEASE.md documentation
- Updated Claude Code skill for distributed binary

---

## 🎯 Next Priorities

### 1. **First Release** (1 hour) - HIGH PRIORITY
**Status**: Ready to release
**Reasoning**:
- All distribution infrastructure complete
- GitHub Actions tested and working
- Documentation updated for binary distribution
- Need to create first tag (v0.1.0) to trigger release workflow

**Steps**:
1. Update Cargo.toml version to 0.1.0
2. Create tag: `git tag -a v0.1.0 -m "Release v0.1.0"`
3. Push tag: `git push origin v0.1.0`
4. Monitor GitHub Actions for release completion
5. Test installation from released binaries

### 2. **Community Validation** (0 hours coding, HIGH VALUE)
**Status**: Ready after first release
**Reasoning**:
- Share with community, gather feedback
- Discover what's missing vs what was assumed
- Validates distribution system works

### 3. **Technical Task Prioritization** (5-7 hours) - MEDIUM-HIGH RISK
**Status**: Ready to implement (unlocked by Directory Walking)
**Reasoning**:
- Enables "prioritize all TODOs in src/" workflow
- Requires validation: Will model prioritization be useful?
- Cheap validation: Extract TODOs, test manual prompt, evaluate results

---

## ⚡ Quick Wins (< 2 hours each)

### **Code Quality Improvements** (~2-3 hours each)
- **Extract aggregation logic** - Remove 150+ lines of duplication in src/main.rs
- **Add test coverage** - Core logic tests (model selection, file walking, response parsing)
- **Enhanced pattern matching** - Support for `**/*.rs` recursive patterns

---

## 📦 Defer for Later Validation

### **Multi-Call Consensus Strategy** (6-8 hours)
- **Why defer**: 3x slower with uncertain quality improvement; validation risk is high
- **What to validate first**: Run manual experiments (3 calls at different temps) to see if consensus actually catches issues single-call misses
- **Validation approach**: Pick 5 complex code files, run at temp=0.0 and temp=0.4, compare outputs - do they differ meaningfully?
- **Timeline**: Post-1-month; consider as "power user" feature after core workflow validated

### **Requirements Prioritization** (5-7 hours)
- **Why defer**: Less applicable to solo developer; more valuable for teams
- **What to validate first**: Technical Task Prioritization (6a) - if that works well, requirements mode becomes more attractive
- **Validation approach**: Try manual prompts with your product roadmap docs - does model provide useful insights?
- **Timeline**: Month 2+; focus on Technical Task Prioritization first

### **Semantic Search** (10-15 hours)
- **Why defer**: High complexity; requires embedding storage architecture decisions
- **What to validate first**: Directory Walking with simple text search - does that solve 80% of "find the file" needs?
- **Validation approach**: Track how often you wish you had semantic search vs grep being sufficient
- **Timeline**: Month 3+; requires architectural investment (vector DB)

### **Code Metrics Tracking** (8-10 hours)
- **Why defer**: Requires persistence layer (database); uncertain value for solo developer
- **What to validate first**: One-time metric reports - do you actually look at them and make decisions?
- **Validation approach**: Generate metrics manually once a week for a month; if unused, deprioritize permanently
- **Timeline**: Month 3+; only if metrics prove decision-useful

---

## 🔄 Dependencies & Sequencing

### ✅ Critical Path (COMPLETED):
```
✅ Week 1-2:  Model Specialization (4-6h)
             ↓
✅ Week 2-3:  Targeted Model Selection (3-4h)
             ↓
✅ Week 3:    Git Diff Integration (3-4h)
             ↓
✅ Week 4:    Distribution Guide Priority 1 (4-6h)
             ↓
✅ Week 5:    Directory & File Walking (8-12h)
```

### Ready to Implement:
- **Technical Task Prioritization** (5-7h) - Unlocked by Directory Walking
  - Prioritize TODOs/tasks across codebase
  - Requires validation first (1h manual test)

- **Anytime (no dependencies)**:
  - Documentation improvements
  - Bug fixes
  - Test coverage improvements

### Key Unlocks:
- **Model Specialization unlocks**: Everything else (it's the foundation)
- **Targeted Selection + Directory Walking unlock**: Technical Task Prioritization (enables "prioritize all TODOs in src/")
- **Distribution Guide unlocks**: Community feedback loop (enables iteration based on real usage)

---

## ⚠️ Risk Assessment

### High Uncertainty Items:

**Multi-Call Consensus** (HIGHEST RISK)
- **Uncertainty**: Does consensus actually improve output quality enough to justify 3x slowdown?
- **Cheap validation**:
  1. Pick 5 complex files from your codebase
  2. Run `ollama run deepseek-coder-v2:8k` manually with same prompt at temp=0.0, 0.2, 0.4
  3. Compare outputs - do they differ in meaningful ways?
  4. Cost: 30 minutes; if outputs are identical, skip feature entirely
- **Decision criteria**: If <20% of outputs show meaningful differences, defer indefinitely

**Technical Task Prioritization** (MEDIUM-HIGH RISK)
- **Uncertainty**: Will model prioritization be useful, or will you override it constantly?
- **Cheap validation**:
  1. Extract all TODOs from local-brain codebase (grep "TODO" -r)
  2. Manually write a prompt asking for prioritization
  3. Run through current model and evaluate results
  4. Cost: 1 hour; if results are poor, reconsider feature
- **Decision criteria**: If model's ordering matches your intuition <60% of the time, defer

**Directory Walking Output Design** (MEDIUM RISK)
- **Uncertainty**: How to present 50+ file summaries coherently without overwhelming user?
- **Cheap validation**:
  1. Manually run reviews on 10 files in a directory
  2. Try organizing outputs different ways (tree view, table, grouped by insights)
  3. See what feels most useful
  4. Cost: 1 hour; informs UX design before coding
- **Decision criteria**: Pick simplest presentation that passes "would I use this weekly?" test

### Lower Risk Items (proceed with confidence):
- **Model Specialization**: LOW RISK - can validate cheaply, models are free, switching is easy
- **Targeted Model Selection**: LOW RISK - straightforward engineering, backwards compatible
- **Git Diff Integration**: LOW RISK - well-understood problem space, clear use case
- **Distribution Guide**: LOW RISK - documentation is iterative, can improve over time

---

## ✅ Execution Summary (COMPLETED)

**Total Time Invested**: ~32-40 hours across 6 weeks

**Completed Features**:
1. ✅ Model Specialization (4-6h)
2. ✅ Targeted Model Selection (3-4h)
3. ✅ Git Diff Integration (3-4h)
4. ✅ Distribution Guide (4-6h)
5. ✅ Directory & File Walking (8-12h)
6. ✅ Documentation Simplification (2-3h)
7. ✅ GitHub Actions CI/CD Pipeline (2-3h)
8. ✅ Model Registry Fix (0.5h)

**Status**: All critical path items complete. CI/CD pipeline implemented. Ready for first release (v0.1.0).

---

## 🎯 What's Next

**Immediate Actions** (Highest Priority):

1. **Create first release (v0.1.0)** (~1h)
   - Tag and push to trigger automated release
   - Test installation on multiple platforms
   - Verify binary distribution works

2. **Validate with real users** (0h coding, HIGH VALUE)
   - Share release with community
   - Gather feedback on distribution experience
   - Discover what's missing vs what was assumed

3. **Code quality improvements** (3-6h total)
   - Extract duplicated aggregation logic
   - Add test coverage
   - Address code smells identified in analysis

**Future Features** (After community validation):

4. **Technical Task Prioritization** (5-7h, medium-high risk)
   - Requires 1h validation first
   - Extract TODOs, test manual prompt, evaluate usefulness

5. **Enhanced pattern matching** (3-4h)
   - Support for `**/*.rs` recursive patterns
   - `.gitignore` integration

**Recommendation**: Create first release immediately. Validate distribution system with real users. Address code quality issues. Then evaluate future features based on community feedback rather than assumptions.

---

## 🚀 Distribution Infrastructure

**Completed**:
- ✅ GitHub Actions CI (multi-platform testing)
- ✅ GitHub Actions Release (automated binary builds)
- ✅ Cross-platform support (macOS Intel/ARM, Linux, Windows)
- ✅ cargo-binstall support
- ✅ Updated documentation for binary distribution
- ✅ Claude Code skill updated for distributed binary
- ✅ Installation instructions for 4 methods
- ✅ Release process documented
- ✅ Claude Code plugin structure (.claude-plugin/)
- ✅ Integration tests with --dry-run mode

**Ready for**:
- First tagged release (v0.1.0)
- Community distribution
- User feedback collection

### Plugin Distribution Consideration

**Question**: Can skills be distributed with the Rust binary, or should we move to Python/TS?

**Finding**: Current approach works well:
- **Binary**: Rust compiles to standalone executable (fast, no runtime deps)
- **Plugin files**: `.claude-plugin/plugin.json` and `SKILL.md` must be separate files
- **Installation**: Users add repo as marketplace, plugin files are discovered automatically
- **No migration needed**: Rust binary + plugin files in same repo is the intended pattern

**Why not Python/TS**:
- Would add runtime dependencies (Python/Node)
- No benefit for plugin discovery (still needs separate SKILL.md files)
- Current Rust binary is faster and more portable

**Recommendation**: Keep Rust. The separation of binary (tool) and plugin files (Claude instructions) is by design.
