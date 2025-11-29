# Usage Guide

Learn how to use local-brain for different review scenarios.

## Basic Reviews

### Review a single file
```bash
local-brain --files src/main.rs
```

### Review multiple files
```bash
local-brain --files src/main.rs,src/lib.rs,tests/integration.rs
```

### Review git changes
```bash
# Reviews staged files (or all unstaged if nothing staged)
local-brain --git-diff
```

### Review a directory
```bash
# All Rust files in src/
local-brain --dir src --pattern "*.rs"

# All JavaScript/TypeScript files
local-brain --dir app --pattern "*.{js,ts}"

# All files in directory
local-brain --dir lib
```

---

## Output Format

All reviews produce structured Markdown with these sections:

- **Issues Found** - Bugs, complexity, potential problems (with line numbers)
- **Simplifications** - Refactoring opportunities
- **Consider Later** - Low priority improvements
- **Other Observations** - General notes and suggestions

### Example Output
```markdown
# Code Review

### main.rs

## Issues Found
- **Unused variable**: Variable `x` is declared but never used (lines: 42)
- **Complex function**: Function `process_data` has high cyclomatic complexity

## Simplifications
- **Extract method**: Lines 100-150 could be extracted into separate function

## Consider Later
- **Add caching**: Frequently called function could benefit from memoization

## Other Observations
- Code is well-documented
- Consider adding more unit tests
```

---

## Choosing a Model

### Quick review (fast, 2-10 seconds)
```bash
local-brain --task quick-review --files src/main.rs
# Uses: qwen2.5-coder:3b or llama3.2:1b
```

### Balanced review (5-15 seconds, default)
```bash
local-brain --files src/main.rs
# Uses: deepseek-coder-v2-8k
```

### Thorough review (10-30 seconds)
```bash
local-brain --task thorough-review --files src/main.rs
# Uses: deepseek-coder-v2-8k
```

### Security review
```bash
local-brain --task security --files auth.rs
# Uses: deepseek-coder-v2-8k
```

### Specific model
```bash
local-brain --model llama3.2:1b --files src/main.rs
```

For detailed model information, see [MODELS.md](MODELS.md).

---

## Advanced Options

### Document type (improves context)
```bash
# Code review
local-brain --files auth.rs --kind code

# Design document review
local-brain --files architecture.md --kind design-doc

# Ticket/issue review
local-brain --files issue.md --kind ticket

# Other document types
local-brain --files config.json --kind other
```

### Review focus (narrows scope)
```bash
# Focus on code organization
local-brain --files main.rs --review-focus refactoring

# Focus on clarity
local-brain --files main.rs --review-focus readability

# Focus on efficiency
local-brain --files main.rs --review-focus performance

# Focus on security
local-brain --files main.rs --review-focus risk

# General review (default)
local-brain --files main.rs --review-focus general
```

### Combine options
```bash
# Security-focused review of authentication code
local-brain --files auth.rs --kind code --review-focus risk

# Performance-focused review of database code
local-brain --files db.rs --kind code --review-focus performance --task thorough-review

# Architecture review of design document
local-brain --files architecture.md --kind design-doc --review-focus general
```

---

## CLI Flags Reference

### Input Modes (choose one)

| Flag | Usage | Example |
|------|-------|---------|
| `--files` | Comma-separated files | `--files "src/main.rs,src/lib.rs"` |
| `--git-diff` | Git changes only | `--git-diff` |
| `--dir` + `--pattern` | Directory with glob | `--dir src --pattern "*.rs"` |

### Model Selection

| Flag | Usage | Example |
|------|-------|---------|
| `--task` | Task-based selection | `--task quick-review` |
| `--model` | Explicit model | `--model qwen2.5-coder:3b` |

**Available tasks:** quick-review, thorough-review, security, documentation, architecture, refactoring

### Review Context

| Flag | Usage | Options |
|------|-------|---------|
| `--kind` | Document type | code, design-doc, ticket, other |
| `--review-focus` | Focus area | refactoring, readability, performance, risk, general |

### Multi-Run Validation (Statistical Consistency)

| Flag | Usage | Example |
|------|-------|---------|
| `--runs N` | Run review N times | `--runs 3` |
| `--validation-mode` | Show validation report | `--validation-mode` |
| `--show-metrics` | Include timing metrics | `--show-metrics` |

**Note:** Multi-run validation is useful to check if an expensive model's findings are statistically consistent:
```bash
# Get validation report with 3 runs
local-brain --runs 3 --validation-mode --files security-critical.rs

# Show timing for each run
local-brain --runs 5 --validation-mode --show-metrics --files auth.rs
```

### Performance Options

| Flag | Usage | Example |
|------|-------|---------|
| `--timeout` | Set request timeout in seconds | `--timeout 180` |
| `--dry-run` | Validate without calling Ollama | `--dry-run` |

---

## Common Patterns

### Code review for security audit
```bash
local-brain --task security --review-focus risk --files auth.rs,crypto.rs
```

### Quick design document feedback
```bash
local-brain --task quick-review --kind design-doc --files architecture.md
```

### Performance optimization check
```bash
local-brain --review-focus performance --files database.rs,cache.rs
```

### Refactoring suggestions
```bash
local-brain --review-focus refactoring --files complex_module.rs
```

### Review all changes before commit
```bash
local-brain --git-diff --kind code
```

### Review new feature code
```bash
local-brain --dir src/features --pattern "*.rs" --review-focus readability
```

### Validate security-critical code with multiple runs
```bash
# Run 3 times to check consistency of findings
local-brain --runs 3 --validation-mode --task security --files critical_auth.rs

# Show timing and validation report
local-brain --runs 5 --validation-mode --show-metrics --files payment_handler.rs
```

### Quick validation of multiple files
```bash
# Auto-switches to faster model for 5 files
local-brain --files "src/api.rs,src/db.rs,src/cache.rs,src/auth.rs,src/utils.rs"

# Explicitly request fast model to speed up multi-file review
local-brain --task quick-review --files "file1.rs,file2.rs,file3.rs,file4.rs"
```

### Dry-run testing (no Ollama needed)
```bash
# Test setup without calling Ollama
local-brain --dry-run --files src/main.rs

# Validate multi-run setup
local-brain --dry-run --runs 3 --validation-mode --files test.rs
```

### Timeout adjustment for slow connections
```bash
# Increase timeout to 5 minutes for slow Ollama or large files
local-brain --timeout 300 --files large_codebase.rs
```

---

## Testing Without Ollama

### Dry run mode
```bash
local-brain --dry-run --files src/main.rs
```

Shows what would be sent to Ollama without making the actual request. Useful for:
- Validating file paths
- Checking input preparation
- Testing without Ollama running

---

## Environment Variables

### Ollama Host
```bash
# Use custom Ollama server
export OLLAMA_HOST="http://192.168.1.100:11434"
local-brain --files src/main.rs
```

### Default Model
```bash
# Set default model
export MODEL_NAME="qwen2.5-coder:3b"
local-brain --files src/main.rs
```

---

## Troubleshooting

### Ollama Not Running
```
Error: Failed to send request to Ollama
```
**Solution:** Start Ollama with `ollama serve`

### Model Not Found
```
Error: model 'xyz' not found
```
**Solution:** Pull the model with `ollama pull model-name`

### Timeout Error
```
Error: Failed to send request to Ollama. Timeout
```
**Solution:** Increase timeout with `--timeout 180` (seconds)

### No Output
**Solution:** Check Ollama is running with `ollama ps` and has enough RAM for the model

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more help.

---

## Performance Tips

1. **Use fast models for multiple files**: Multi-file reviews with smaller models are faster
2. **Set timeout appropriately**: Larger models need more time (increase `--timeout`)
3. **Check Ollama memory**: Use `ollama ps` to see which models are loaded
4. **Unload heavy models**: Use `ollama ps` and stop models you're not using

---

## Integration with Claude Code

If using the Claude Code skill:

```
In Claude Code, just ask:
"Review this file"
"Security audit of auth.rs"
"Refactor suggestions for main.rs"
```

The skill automatically:
- Detects file context
- Chooses appropriate model
- Formats output for readability
- Handles all Ollama interaction
