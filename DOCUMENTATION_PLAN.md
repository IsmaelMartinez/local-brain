# Documentation Improvement Plan

## Executive Summary

**Health Score**: 75/100 (Strong foundation, needs restructuring)
**Timeline**: 8-10 hours total
**Priority**: Critical for distribution readiness

## Key Findings

### Strengths
- Excellent technical depth in MODELS.md
- Comprehensive troubleshooting coverage
- Good integration examples
- Clear model selection documentation

### Critical Gaps
1. **No installation guide** - Major blocker for new users
2. **No quickstart tutorial** - Missing 5-minute onboarding
3. **README too technical** - 187 lines, overwhelming for beginners
4. **No contribution guide** - Barrier for open source engagement
5. **Internal vs user docs mixed** - PRIORITIZATION_ANALYSIS.md is user-facing but shouldn't be

### Specific Issues from Reviews

**README.md**:
- Model selection priority system too complex (4 levels)
- Performance expectations unclear (what's "fast"?)
- Git diff examples need more context
- Should be 40-50 lines, not 187

**MODELS.md**:
- Too technical for beginners
- Missing real-world workflow examples
- Excellent technical depth but needs beginner bridge

**TROUBLESHOOTING.md**:
- Missing --task flag documentation
- Missing --git-diff mode troubleshooting
- Well-organized otherwise

**PRIORITIZATION_ANALYSIS.md**:
- Good internal document
- Should not be user-facing
- Move to internal/ folder

## Proposed Structure

```
/
├── README.md                    # 40-50 lines - elevator pitch, links
├── INSTALLATION.md              # Platform-specific setup (NEW)
├── QUICKSTART.md                # 5-minute tutorial (NEW)
├── MODELS.md                    # Keep but simplify intro
├── TROUBLESHOOTING.md           # Update with missing sections
├── CONTRIBUTING.md              # Development guide (NEW)
├── LICENSE
├── internal/                    # Internal docs (NEW)
│   ├── PRIORITIZATION_ANALYSIS.md
│   └── VALIDATION_EXPERIMENTS.md
└── .claude/
    └── skills/local-brain/SKILL.md
```

## Implementation Tasks

### Phase 1: Critical User-Facing Docs (6-7 hours)

#### 1. Create INSTALLATION.md (2-3 hours)
**Content**:
- System requirements (16GB RAM recommended, 8GB minimum, 20GB disk)
- Prerequisites:
  - Rust 1.70+ installation (platform-specific: rustup.rs)
  - Ollama setup (platform-specific: ollama.ai/download)
  - Model downloads (`ollama pull deepseek-coder-v2:16b`)
- Installation options:
  - Pre-built binary (when available)
  - Build from source
- Verification steps
- First-run test commands
- Link to QUICKSTART.md

**Priority**: P0 - Blocking distribution

#### 2. Create QUICKSTART.md (1-2 hours)
**Content**:
- 5-minute tutorial
- Three examples:
  1. Review a single file
  2. Review git changes
  3. Use different models for different tasks
- Expected output with screenshots/examples
- "What's next?" section linking to:
  - MODELS.md for model selection
  - TROUBLESHOOTING.md for issues
  - README.md for advanced features

**Priority**: P0 - Critical for onboarding

#### 3. Refactor README.md (2 hours)
**Target**: Reduce from 187 lines to 40-50 lines

**Structure**:
```markdown
# Local Brain

One-line elevator pitch

## What It Does
- Offloads context to local LLMs
- 3-4 key use cases with one-liners

## Quick Start
👉 See [INSTALLATION.md](INSTALLATION.md) for setup
👉 See [QUICKSTART.md](QUICKSTART.md) for 5-minute tutorial

## Key Features
- Model specialization (brief)
- Git diff integration (brief)
- Claude Code integration (brief)

## Documentation
- [Installation Guide](INSTALLATION.md)
- [Quick Start Tutorial](QUICKSTART.md)
- [Model Selection Guide](MODELS.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Contributing](CONTRIBUTING.md)

## License
MIT
```

**Priority**: P0 - Entry point must be simple

#### 4. Create CONTRIBUTING.md (1-2 hours)
**Content**:
- Development setup
- Architecture overview
- Code structure (src/main.rs organization)
- How to add new models to registry
- Testing guidelines
- PR process
- Style guide (Rust conventions)

**Priority**: P1 - Enables community contribution

### Phase 2: Updates to Existing Docs (2-3 hours)

#### 5. Update MODELS.md (1 hour)
**Changes**:
- Add "Getting Started" section at top
- Add workflow examples:
  - "I want fast feedback" → qwen2.5-coder:3b
  - "I need security review" → deepseek-coder-v2:16b
  - "I'm low on RAM" → llama3.2:1b
- Simplify model selection priority explanation
- Keep technical depth but move to bottom

**Priority**: P1 - Improves discoverability

#### 6. Update TROUBLESHOOTING.md (1 hour)
**Add sections**:
- Task flag issues
  - "Unknown task type" error
  - How to list available tasks
- Git diff mode issues
  - No files found
  - Permission errors
  - Binary file handling
- Model selection debugging
  - Which model was selected?
  - Override priority not working

**Priority**: P1 - Closes documentation gaps

#### 7. Reorganize Internal Docs (30 minutes)
**Actions**:
- Create internal/ directory
- Move PRIORITIZATION_ANALYSIS.md to internal/
- Update any references

**Priority**: P2 - Nice to have

## Success Metrics

1. **New user can install in <10 minutes** (INSTALLATION.md)
2. **New user completes first review in <5 minutes** (QUICKSTART.md)
3. **README is <50 lines** (refactored)
4. **Zero unanswered questions in issues** (comprehensive docs)
5. **Community PRs increase** (CONTRIBUTING.md)

## Timeline

**Week 1** (6-7 hours):
- Day 1-2: INSTALLATION.md + QUICKSTART.md (3-5h)
- Day 3: README.md refactor (2h)
- Day 4: CONTRIBUTING.md (1-2h)

**Week 2** (2-3 hours):
- Day 5: Update MODELS.md + TROUBLESHOOTING.md (2h)
- Day 6: Reorganize internal docs (30m)
- Day 7: Review and polish (1h)

## Next Steps

1. ✅ Create this plan
2. ⏳ Create INSTALLATION.md
3. ⏳ Create QUICKSTART.md
4. ⏳ Refactor README.md
5. ⏳ Create CONTRIBUTING.md
6. ⏳ Update existing docs
7. ⏳ Final review and polish
