# Model Selection Guide

Complete guide to choosing and using Ollama models with local-brain.

## Quick Reference

```bash
# Fastest (9s) - Quick reviews, CI/CD
./target/release/local-brain --model llama3.2:1b

# Best balance (11s) - Daily use, recommended default
./target/release/local-brain --model phi3:mini

# Most detailed (27s) - Thorough code reviews
./target/release/local-brain --model qwen2.5-coder:3b

# General purpose (12s) - Documentation, requirements
./target/release/local-brain --model qwen2.5:3b

# Default (20-30s) - Production-ready, security audits
./target/release/local-brain
```

## Performance Summary

| Model | Size | Speed | Quality | RAM | Best Use |
|-------|------|-------|---------|-----|----------|
| **llama3.2:1b** | 1.3 GB | 9s ⚡⚡⚡ | Good | 1.5 GB | Quick checks, CI/CD |
| **phi3:mini** | 2.2 GB | 11s ⚡⚡ | Very Good | 2.5 GB | Daily use, interactive |
| **qwen2.5:3b** | 1.9 GB | 12s ⚡⚡ | Very Good | 2.0 GB | Requirements, docs |
| **qwen2.5-coder:3b** | 1.9 GB | 27s ⚡ | Excellent | 2.0 GB | Code reviews, PRs |
| **deepseek-coder-v2:8k** | 8.9 GB | 20-30s ⚡ | Expert | 9.2 GB | Production, security |

**Validation Status:** All models tested and validated ✅ (100% pass rate)

---

## Available Models

### llama3.2:1b - Very Fast (1.3 GB)

**Best for:** Quick summaries and rapid triage

**Characteristics:**
- Smallest model (1B parameters)
- Fastest inference (< 10s for 300 lines)
- Lowest RAM usage (~1.5 GB)
- Basic text understanding

**Ideal Use Cases:**
- Pre-commit hooks for rapid feedback
- CI/CD pipelines where speed matters
- Quick file summaries during exploration
- Rapid iteration during development
- Low-resource environments

**Example:**
```bash
# Quick summary of all files in a directory
for file in src/*.rs; do
    echo "{\"file_path\": \"$file\"}" | local-brain --model llama3.2:1b
done
```

---

### phi3:mini - Balanced (2.2 GB) **[RECOMMENDED DEFAULT]**

**Best for:** General reviews and documentation

**Characteristics:**
- Efficient reasoning (3.8B parameters)
- Balanced speed/quality (10-20s for 300 lines)
- Good instruction following
- Microsoft-optimized

**Ideal Use Cases:**
- Interactive development and IDE integration
- Documentation quality checks
- General code review for daily work
- Medium-complexity tasks
- Best balance between speed and insight

**Example:**
```bash
# Review documentation files
echo '{"file_path": "README.md"}' | local-brain --model phi3:mini
```

---

### qwen2.5:3b - Reasoning (1.9 GB)

**Best for:** Requirements analysis and design review

**Characteristics:**
- General reasoning (3B parameters)
- Strong context awareness (15-20s for 300 lines)
- Multi-domain knowledge
- Good for non-code documents

**Ideal Use Cases:**
- Requirements prioritization
- Design document review
- Feature planning and roadmaps
- Business logic analysis
- Product strategy evaluation

**Example:**
```bash
# Prioritize requirements
echo '{"file_path": "requirements.md", "meta": {"review_focus": "prioritization"}}' | \
  local-brain --model qwen2.5:3b
```

---

### qwen2.5-coder:3b - Code Specialist (1.9 GB)

**Best for:** Pre-commit checks and code smell detection

**Characteristics:**
- Code-specialized (3B parameters)
- Fast inference (10-15s for 300 lines)
- Strong syntax understanding
- Detects obvious issues quickly

**Ideal Use Cases:**
- Pre-commit hooks for code quality
- Pull request reviews
- Syntax validation
- Quick refactoring suggestions
- CI/CD code checks

**Example:**
```bash
# Pre-commit check
git diff --name-only --cached | while read file; do
    echo "{\"file_path\": \"$file\"}" | local-brain --model qwen2.5-coder:3b
done
```

---

### deepseek-coder-v2:8k - Expert (8.9 GB) **[DEFAULT]**

**Best for:** Production code review and security audit

**Characteristics:**
- Code expert (16B parameters)
- Deep understanding (20-30s for 300 lines)
- Architectural insights
- Security analysis capabilities

**Ideal Use Cases:**
- Production-ready code review
- Security-critical analysis
- Complex refactoring planning
- Architectural decisions
- When quality matters most

**Example:**
```bash
# Thorough security review (uses default model)
echo '{"file_path": "auth.rs", "meta": {"review_focus": "risk"}}' | local-brain
```

---

## Decision Matrix

| Your Need | Model | Why |
|-----------|-------|-----|
| "Quick, what does this do?" | `llama3.2:1b` | Fastest summaries |
| "Pre-commit check" | `qwen2.5-coder:3b` | Code-focused, fast |
| "Daily code review" | `phi3:mini` | Best balance |
| "Review this doc" | `phi3:mini` | Good at documentation |
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

## Task-Based Selection

Use `--task` flag for automatic model selection:

```bash
# Automatically selects appropriate model
local-brain --task quick-review     # Uses qwen2.5-coder:3b
local-brain --task documentation    # Uses phi3:mini
local-brain --task security         # Uses deepseek-coder-v2:8k
local-brain --task summarize        # Uses llama3.2:1b
```

**Available Tasks:**
- `quick-review`, `syntax-check` → qwen2.5-coder:3b
- `summarize`, `triage` → llama3.2:1b
- `documentation`, `general-review` → phi3:mini
- `requirements`, `prioritization`, `design-review` → qwen2.5:3b
- `thorough-review`, `security`, `architecture` → deepseek-coder-v2:8k

See `models.json` for complete task mappings.

---

## Validation Results

**Test Date:** 2025-11-21
**Test File:** tests/fixtures/code_smells.js (121 lines, 5 known issues)
**Status:** All models PASSED ✅

### Quality Assessment

All models successfully detected:
- ✓ Deeply nested conditionals
- ✓ God function (doing too many things)
- ✓ Magic numbers
- ✓ Duplicate code
- ✓ Missing error handling

### Output Consistency

All models produced valid JSON with:
- 2 spikes (issues/hotspots)
- 2 simplifications
- 2 defer_for_later items
- 2 other_observations

### Quality Differences

**qwen2.5-coder:3b** (Most code-specific):
- Concrete suggestions (e.g., "switch case structure")
- Identified specific patterns like "early returns"
- Most detailed code-specific analysis

**llama3.2:1b** (Fastest, good quality):
- Clear, actionable suggestions
- Good general observations
- Excellent for rapid feedback

**phi3:mini** (Best balance):
- Good code-specific insights
- Clear prioritization
- Well-structured suggestions

**qwen2.5:3b** (Versatile):
- Solid general analysis
- Good for different document types
- Reliable baseline performance

---

## Resource Considerations

**System Requirements:**
- macOS with 16GB RAM (tested)
- Linux/Windows with similar specs should work
- Ollama installed and running

**Total Models:** ~16.2 GB (all 5 models)

**Practical Usage:**
- ✅ Can load all smaller models simultaneously (< 8 GB total)
- ✅ Can run 2-3 small models in parallel for batch processing
- ⚠️ Default model (8.9 GB) should run alone for best performance
- ⚠️ Keep ~6-7 GB free for OS and other applications

**Recommendations:**
- Use small models (1-3B) for iteration and exploration
- Reserve 8K model for final, thorough reviews
- Consider model size when running in CI/CD environments
- Start with `phi3:mini` for daily use

---

## Usage Examples

### Single File Review
```bash
# Use specific model
echo '{"file_path": "src/main.rs"}' | local-brain --model phi3:mini | jq

# Use task-based selection
echo '{"file_path": "src/main.rs"}' | local-brain --task code-review | jq

# Use default model
echo '{"file_path": "src/main.rs"}' | local-brain | jq
```

### Batch Processing
```bash
# Review all Rust files with fast model
for file in src/**/*.rs; do
    echo "{\"file_path\": \"$file\"}" | local-brain --model llama3.2:1b
done

# Review changed files (git)
git diff --name-only | while read file; do
    echo "{\"file_path\": \"$file\"}" | local-brain --model qwen2.5-coder:3b
done
```

### With Metadata
```bash
# Specify review focus
echo '{"file_path": "auth.rs", "meta": {"review_focus": "risk"}}' | \
  local-brain --model deepseek-coder-v2:8k

# Specify document kind
echo '{"file_path": "README.md", "meta": {"kind": "documentation"}}' | \
  local-brain --model phi3:mini
```

---

## Tips & Best Practices

1. **Start small:** Try `phi3:mini` for daily work
2. **Benchmark yourself:** Time your typical reviews with different models
3. **Match complexity:** Don't use the 8K model for trivial reviews
4. **Batch processing:** Use small models to review multiple files quickly
5. **Cost awareness:** All models are free (local inference), so experiment!
6. **Model rotation:** Use fast models for iteration, slow models for final review
7. **Task mappings:** Leverage `--task` flags for automatic selection
8. **Resource monitoring:** Watch RAM usage when running multiple models

---

## Troubleshooting

### Model not found
```bash
# Check installed models
ollama list

# Download missing model
ollama pull llama3.2:1b
```

### Slow performance
- Ensure Ollama is running: `ollama list`
- Check available RAM: Only use large models when you have headroom
- Use smaller models for faster results
- Consider `llama3.2:1b` for maximum speed

### Quality issues
- Try a larger model: `qwen2.5-coder:3b` or `deepseek-coder-v2:8k`
- Use `--task` flag for automatic selection
- Provide better metadata in JSON input

---

## Re-running Validation

```bash
# Run full validation suite
./validate_models.sh

# Test specific model manually
echo '{"file_path": "tests/fixtures/code_smells.js"}' | \
  ./target/release/local-brain --model phi3:mini | jq
```

---

## See Also

- **models.json** - Machine-readable model registry and task mappings
- **README.md** - Project overview and quick start
- **ARCHITECTURE.md** - Technical implementation details
- **ROADMAP.md** - Future features and improvements
