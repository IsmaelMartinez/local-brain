# Local Context Helper - Project Summary

## Overview

**Local Context Helper** is a tool that performs structured code and document reviews using local Ollama LLM models, integrated with Claude Code via Skills and subagents.

**Status**: Planning Complete - Ready for Implementation

---

## Problem Statement

When working with Claude Code, reviewing large files or multiple documents can consume significant context tokens in both the main conversation and subagents. This project solves this by:

1. **Offloading context** to a local Rust binary that handles file I/O
2. **Using local LLMs** (via Ollama) for review instead of consuming Claude API tokens
3. **Keeping conversations lightweight** by passing file paths instead of content

---

## Solution Architecture

### High-Level Flow

```
User Request
    ↓
Main Conversation (~100 tokens)
    ↓ [passes file path]
Subagent/Haiku (~500 tokens)
    ↓ [passes file path as JSON]
Rust Binary
    ↓ [reads file, calls Ollama]
Ollama/Local LLM
    ↓ [returns structured JSON review]
Rust Binary
    ↓ [outputs JSON to stdout]
Subagent
    ↓ [formats human-friendly response]
User Receives Review
```

### Key Innovation

**Binary reads files, not the subagent!**

- Traditional approach: Subagent reads file → loads into context → passes to tool
- Our approach: Subagent passes path → Binary reads file → Context stays minimal

### Context Savings

| Component | Traditional | Our Approach | Savings |
|-----------|-------------|--------------|---------|
| Main Conversation | 500+ tokens | ~100 tokens | 80%+ |
| Subagent | 5000+ tokens | ~500 tokens | 90%+ |
| Total | 5500+ tokens | ~600 tokens | 89%+ |

---

## Components

### 1. Rust Binary: `local-context-optimizer`

**Input** (via stdin):
```json
{
  "file_path": "/path/to/file.rs",
  "meta": {
    "kind": "code",
    "review_focus": "refactoring"
  }
}
```

**Output** (via stdout):
```json
{
  "spikes": [...],
  "simplifications": [...],
  "defer_for_later": [...],
  "other_observations": [...]
}
```

**Responsibilities**:
- Read file from disk
- Call Ollama API with review prompt
- Parse JSON response
- Return structured review

### 2. Claude Code Skill: `local-context-optimiser`

**Location**: `.claude/skills/local-context-optimiser/skill.md`

**Purpose**: Wrapper that subagents use to call the binary

**Usage**:
```bash
echo '{"file_path":"src/main.rs","meta":{"kind":"code","review_focus":"refactoring"}}' | local-context-optimizer
```

### 3. Subagent: `review-optimiser`

**Model**: Haiku 4.5 (cheap, fast)

**Responsibilities**:
- Receive file paths from main conversation
- Determine file metadata (kind, review focus)
- Build JSON payload
- Call binary via Skill
- Interpret JSON results
- Return human-friendly summary

---

## Review Categories

### Spikes
Hotspots, areas to investigate, potential issues or complexity that need attention.

**Example**: "Complex authentication logic in verify_token (lines 45-78)"

### Simplifications
Areas that could be simplified, refactored, or optimized.

**Example**: "Duplicate error handling patterns across login/logout/refresh"

### Defer for Later
Low-priority items that are safe to move to future iterations.

**Example**: "Add rate limiting (not critical now)"

### Other Observations
General notes, ideas, or observations that don't fit other categories.

**Example**: "Good use of type safety for tokens"

---

## Project Documents

### Planning Documents

1. **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** (701 lines)
   - Complete technical specification
   - Architecture and data structures
   - Rust implementation details
   - Ollama integration
   - Claude Code skill and subagent setup
   - Testing strategy
   - Success criteria
   - Timeline estimate (10-16 hours)

2. **[VALIDATION_EXPERIMENTS.md](VALIDATION_EXPERIMENTS.md)** (347 lines)
   - 6 critical spikes identified
   - Step-by-step validation experiments
   - Success criteria for each experiment
   - Go/No-Go decision points
   - Fallback strategies
   - Total validation time: ~2.5 hours

3. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** (this document)
   - High-level overview
   - Quick reference
   - Project status

### Implementation Files (to be created)

4. **Rust Binary** (`local-context-optimizer/`)
   - `Cargo.toml` - Dependencies and metadata
   - `src/main.rs` - Binary implementation
   - `README.md` - Usage and setup

5. **Claude Code Skill** (`.claude/skills/local-context-optimiser/`)
   - `skill.md` - Skill documentation

---

## Critical Validation Experiments

Before full implementation, we must validate:

### Phase 1: Foundation (30 min)
1. ✅ Check Ollama installation and available models
2. ✅ Test Ollama JSON output reliability
3. ✅ Test review structure generation

**Go/No-Go**: If JSON is unreliable, implement cleanup/extraction layer

### Phase 2: Integration (70 min)
4. ✅ Build test binary that reads files from paths
5. ✅ Test file error handling
6. ✅ Test model review quality

**Go/No-Go**: If binary can't read files, use fallback (subagent reads)

### Phase 3: E2E (45 min)
7. ✅ Create and test Skill
8. ✅ Test binary execution from Skill
9. ✅ Test with various file sizes

**Go/No-Go**: If E2E fails, adjust architecture

---

## Technology Stack

### Core
- **Rust** (1.70+): Binary implementation
- **Ollama**: Local LLM API
- **Claude Code**: Main interface and orchestration

### Rust Dependencies
- `serde` + `serde_json`: JSON handling
- `reqwest` (blocking): HTTP client for Ollama
- `anyhow`: Error handling

### Recommended Models
- `llama3.2`: Good general purpose
- `qwen2.5-coder`: Code-focused
- `mistral`: Alternative option
- `deepseek-coder`: Code specialist

---

## Success Criteria

### V1 Must Have
- ✅ Binary accepts file paths via JSON stdin
- ✅ Binary reads files and handles errors gracefully
- ✅ Ollama returns valid, structured JSON 90%+ of time
- ✅ Reviews are relevant and actionable
- ✅ Response time < 15s for typical files (< 500 lines)
- ✅ Works via Claude Code Skill
- ✅ Subagent integration working
- ✅ Context savings of 80%+ verified

### Quality Metrics
- Response time: < 10s for 500 line files
- Accuracy: 80%+ relevant insights
- JSON stability: 95%+ valid output
- No crashes on malformed input

---

## Implementation Phases

### Phase 1: Rust Binary (4-6 hours)
- [x] Create Cargo project
- [ ] Implement data structures
- [ ] Implement file reading
- [ ] Implement Ollama API client
- [ ] Implement response parsing
- [ ] Add error handling
- [ ] Manual testing

### Phase 2: Testing (2-3 hours)
- [ ] Test with various file types
- [ ] Test error scenarios
- [ ] Refine prompts for JSON stability
- [ ] Test different models
- [ ] Document results

### Phase 3: Claude Integration (1-2 hours)
- [ ] Create Skill directory
- [ ] Write skill.md
- [ ] Test from main conversation
- [ ] Configure subagent (if needed)

### Phase 4: Documentation (1-2 hours)
- [ ] Write binary README
- [ ] Document installation
- [ ] Create usage examples
- [ ] Write troubleshooting guide

---

## Risk Mitigation

### Known Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Ollama returns text instead of JSON | Medium | High | Add JSON extraction/cleanup |
| Model quality poor | Low | Medium | Try multiple models, refine prompts |
| File reading fails | Low | High | Graceful errors, fallback to subagent |
| Context size too small | Low | Medium | Chunk files, set size limits |
| Binary not accessible | Low | High | Test PATH, document installation |

---

## Future Enhancements (Post-V1)

### Features
- Batch processing (multiple files at once)
- Incremental reviews (only changed sections)
- Custom prompt templates
- Multiple output formats (Markdown, HTML)
- Review history tracking
- Multi-model comparison

### Performance
- Async I/O for concurrency
- Response streaming
- Result caching
- Distributed execution

---

## Getting Started (After Validation)

### Prerequisites
1. Rust toolchain installed (`rustup`)
2. Ollama installed and running
3. At least one LLM model pulled (`ollama pull llama3.2`)
4. Claude Code environment

### Quick Start
```bash
# 1. Build binary
cd local-context-optimizer
cargo build --release

# 2. Test manually
echo '{"file_path":"test.rs","meta":{"kind":"code"}}' | ./target/release/local-context-optimizer

# 3. Install (add to PATH)
cp target/release/local-context-optimizer /usr/local/bin/

# 4. Create Claude Code Skill
# (see IMPLEMENTATION_PLAN.md)

# 5. Test from Claude Code
# "Review src/main.rs for refactoring opportunities"
```

---

## Project Status

### ✅ Completed
- [x] Architecture design
- [x] Implementation plan (detailed)
- [x] Validation experiments defined
- [x] Risk assessment
- [x] Documentation structure
- [x] Project setup

### 🔄 In Progress
- [ ] Validation experiments
- [ ] Rust binary implementation

### 📋 Not Started
- [ ] Claude Code Skill creation
- [ ] Subagent configuration
- [ ] End-to-end testing
- [ ] Production deployment

---

## Timeline

| Phase | Tasks | Estimated | Status |
|-------|-------|-----------|--------|
| Planning | Architecture, docs | 4 hours | ✅ Complete |
| Validation | Experiments | 2.5 hours | 📋 Not Started |
| Implementation | Rust binary | 4-6 hours | 📋 Not Started |
| Testing | Manual + Integration | 2-3 hours | 📋 Not Started |
| Integration | Skill + Subagent | 1-2 hours | 📋 Not Started |
| Documentation | README, guides | 1-2 hours | 📋 Not Started |
| **Total** | | **15-20 hours** | **20% Complete** |

---

## Key Decisions Made

### Architecture Decisions
1. **Binary reads files** (not subagent) → Maximizes context savings
2. **JSON via stdin/stdout** → Simple, testable interface
3. **Ollama for LLM** → Local, free, no API costs
4. **Haiku subagent** → Cost-effective orchestration
5. **Rust for binary** → Fast, reliable, single executable

### Scope Decisions (V1)
- ✅ Single file at a time
- ✅ Blocking I/O (simpler)
- ✅ No caching
- ✅ Four review categories only
- ❌ No batch processing (future)
- ❌ No streaming (future)
- ❌ No custom prompts (future)

---

## Questions & Answers

### Why Rust?
- Fast compilation and execution
- Excellent error handling
- Single binary (easy distribution)
- Great JSON support (serde)
- Memory safe

### Why Ollama?
- Local execution (no API costs)
- Easy setup and use
- Multiple model support
- Good JSON generation
- Fast inference

### Why not just use Claude Code directly?
- Context token costs add up
- Local LLM is free for unlimited reviews
- Keeps main conversation focused
- Enables batch processing of large codebases

### Can I use different models?
Yes! Set `MODEL_NAME` environment variable to any Ollama model.

### What file types are supported?
Any text file. The `kind` metadata helps the model understand context:
- `code`: Source code files
- `design-doc`: Architecture/design documents
- `ticket`: Issue descriptions, requirements
- `other`: General text

---

## Contributing

This is a planning repository. Implementation PRs welcome after validation phase.

### Areas for Contribution
- Additional model testing
- Prompt refinement
- Error handling improvements
- Performance optimizations
- Documentation

---

## License

See [LICENSE](LICENSE) file.

---

## Contact & Support

- Issues: GitHub Issues

---

**Last Updated**: 2025-11-19
**Status**: Planning Complete - Ready for Validation
