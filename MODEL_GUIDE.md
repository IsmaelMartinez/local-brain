# Model Selection Guide

This guide helps you choose the right Ollama model for your code review needs.

## Available Models

### 1. llama3.2:1b (Very Fast - 1.3 GB)
**Best for:** Quick summaries and rapid triage

**Characteristics:**
- Smallest model (1B parameters)
- Fastest inference (< 10s for 300 lines)
- Lowest RAM usage (~1.5 GB)
- Basic text understanding

**Use Cases:**
- Quick file summaries
- Rapid codebase exploration
- Basic documentation review
- When you need speed over depth

**Example Workflow:**
```bash
# Quick summary of all files in a directory
for file in src/*.rs; do
    echo "{\"file_path\": \"$file\"}" | local-brain --model llama3.2:1b
done
```

---

### 2. qwen2.5-coder:3b (Fast - 1.9 GB)
**Best for:** Pre-commit checks and code smell detection

**Characteristics:**
- Code-specialized (3B parameters)
- Fast inference (10-15s for 300 lines)
- Strong syntax understanding
- Detects obvious issues quickly

**Use Cases:**
- Pre-commit hooks
- Simple code reviews
- Syntax validation
- Quick refactoring suggestions
- CI/CD fast checks

**Example Workflow:**
```bash
# Pre-commit check
git diff --name-only --cached | while read file; do
    echo "{\"file_path\": \"$file\"}" | local-brain --model qwen2.5-coder:3b
done
```

---

### 3. phi3:mini (Balanced - 2.2 GB)
**Best for:** General reviews and documentation

**Characteristics:**
- Efficient reasoning (3.8B parameters)
- Balanced speed/quality (10-20s for 300 lines)
- Good instruction following
- Microsoft-optimized

**Use Cases:**
- Documentation quality checks
- General code review
- Medium-complexity tasks
- Balance between speed and insight

**Example Workflow:**
```bash
# Review documentation files
echo '{"file_path": "README.md"}' | local-brain --model phi3:mini
```

---

### 4. qwen2.5:3b (Reasoning - 1.9 GB)
**Best for:** Requirements analysis and design review

**Characteristics:**
- General reasoning (3B parameters)
- Strong context awareness (15-20s for 300 lines)
- Multi-domain knowledge
- Good for non-code documents

**Use Cases:**
- Requirements prioritization
- Design document review
- Feature planning
- Business logic analysis
- Product roadmap evaluation

**Example Workflow:**
```bash
# Prioritize requirements
echo '{"file_path": "requirements.md", "meta": {"review_focus": "prioritization"}}' | local-brain --model qwen2.5:3b
```

---

### 5. deepseek-coder-v2:8k (Thorough - 8.9 GB) [DEFAULT]
**Best for:** Production code review and security audit

**Characteristics:**
- Code expert (16B parameters)
- Deep understanding (20-30s for 300 lines)
- Architectural insights
- Security analysis capabilities

**Use Cases:**
- Production-ready code review
- Security-critical analysis
- Complex refactoring planning
- Architectural decisions
- When quality matters most

**Example Workflow:**
```bash
# Thorough security review
echo '{"file_path": "auth.rs", "meta": {"review_focus": "risk"}}' | local-brain
```

---

## Decision Matrix

| Your Need | Model | Why |
|-----------|-------|-----|
| "Quick, what does this do?" | `llama3.2:1b` | Fastest summaries |
| "Pre-commit check" | `qwen2.5-coder:3b` | Code-focused, fast |
| "Review this doc" | `phi3:mini` | Balanced, good at docs |
| "Prioritize these features" | `qwen2.5:3b` | Reasoning about requirements |
| "Is this production-ready?" | `deepseek-coder-v2:8k` | Thorough, expert-level |

---

## Recommended Workflows

### Development Loop
1. **Initial exploration:** `llama3.2:1b` - Quick summaries of unfamiliar code
2. **While coding:** `qwen2.5-coder:3b` - Fast feedback on changes
3. **Before PR:** `deepseek-coder-v2:8k` - Thorough review

### Team Review Process
1. **Triage:** `llama3.2:1b` - Quick assessment of all PRs
2. **Standard review:** `qwen2.5-coder:3b` - Most PRs
3. **Critical paths:** `deepseek-coder-v2:8k` - Security, core logic

### Documentation Workflow
1. **Quick check:** `llama3.2:1b` - Grammar/completeness
2. **Quality review:** `phi3:mini` - Clarity and structure
3. **Technical accuracy:** `qwen2.5-coder:3b` - Code examples

---

## Performance Comparison

| Model | Size | Speed | RAM | Best Use |
|-------|------|-------|-----|----------|
| llama3.2:1b | 1.3 GB | ⚡⚡⚡ | 1.5 GB | Summaries |
| qwen2.5-coder:3b | 1.9 GB | ⚡⚡ | 2.0 GB | Code smell |
| phi3:mini | 2.2 GB | ⚡⚡ | 2.5 GB | Docs |
| qwen2.5:3b | 1.9 GB | ⚡⚡ | 2.0 GB | Requirements |
| deepseek-coder-v2:8k | 8.9 GB | ⚡ | 9.2 GB | Thorough |

---

## Resource Considerations

**System:** macOS with 16GB RAM

**Total Models:** ~16.2 GB (all models loaded)

**Practical Usage:**
- ✅ Can load all smaller models simultaneously (< 8 GB total)
- ✅ Can run 2-3 small models in parallel for batch processing
- ⚠️ Default model (8.9 GB) should run alone for best performance
- ⚠️ Keep ~6-7 GB free for OS and other applications

**Recommendations:**
- Use small models (1-3B) for iteration and exploration
- Reserve 8K model for final, thorough reviews
- Consider model size when running in CI/CD environments

---

## Future: Automated Model Selection

**Coming Soon:** CLI flags for automatic model selection

```bash
# Proposed usage (not yet implemented)
local-brain --task quick-review file.rs    # Uses qwen2.5-coder:3b
local-brain --task thorough-review file.rs # Uses deepseek-coder-v2:8k
local-brain --task summarize file.rs       # Uses llama3.2:1b
```

See `PRIORITIZATION_ANALYSIS.md` for implementation roadmap.

---

## Model Validation Status

| Model | Downloaded | Tested | Validated |
|-------|------------|--------|-----------|
| llama3.2:1b | ✅ | 🔄 | Pending |
| qwen2.5-coder:3b | ✅ | 🔄 | Pending |
| phi3:mini | ✅ | 🔄 | Pending |
| qwen2.5:3b | ✅ | 🔄 | Pending |
| deepseek-coder-v2:8k | ✅ | ✅ | ✅ (100% test pass) |

**Note:** Full validation testing will be completed as part of targeted model selection implementation.

---

## Tips

1. **Start small:** Try `qwen2.5-coder:3b` for daily work
2. **Benchmark yourself:** Time your typical reviews with different models
3. **Match complexity:** Don't use the 8K model for trivial reviews
4. **Batch processing:** Use small models to review multiple files quickly
5. **Cost awareness:** All models are free (local inference), so experiment!

---

## References

- Model specifications: `models.json`
- Implementation plan: `IMPLEMENTATION_PLAN.md`
- Prioritization: `PRIORITIZATION_ANALYSIS.md`
