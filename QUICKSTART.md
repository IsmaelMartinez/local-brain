# Quick Start Guide

Get up and running with local-brain in 5 minutes.

**Prerequisites**: Ensure you've completed [INSTALLATION.md](INSTALLATION.md) first.

## Your First Review

Let's review a file to see what local-brain can find:

```bash
# Review src/main.rs with the default model
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain | jq .
```

**What happens**:
1. local-brain reads `src/main.rs` from disk
2. Sends it to your local Ollama model
3. Returns structured JSON with findings

**Expected output**:
```json
{
  "spikes": [
    {
      "title": "Complex error handling pattern",
      "summary": "Multiple error contexts chained with .context() - good practice but review error messages",
      "lines": "110-120"
    }
  ],
  "simplifications": [
    {
      "title": "Repeated PathBuf conversion",
      "summary": "file_name() logic appears in multiple functions"
    }
  ],
  "defer_for_later": [],
  "other_observations": [
    "Well-structured with clear sections",
    "Good use of type safety with custom structs"
  ]
}
```

## Example 1: Review Git Changes

Before committing, review all your changes:

```bash
# Review staged or unstaged changes
./target/release/local-brain --git-diff --task quick-review
```

**What happens**:
1. Detects staged files (or falls back to unstaged)
2. Reviews each changed file
3. Aggregates results with filename context

**Output example**:
```json
{
  "spikes": [
    {
      "title": "[main.rs] Missing error handling",
      "summary": "Git command execution doesn't handle non-UTF8 output"
    }
  ],
  "simplifications": [
    {
      "title": "[main.rs] Duplicate file path handling",
      "summary": "Consider extracting filename logic to helper function"
    }
  ]
}
```

**Use case**: Pre-commit review to catch issues before they hit CI.

## Example 2: Choose Your Model

Use different models for different tasks:

### Fast Feedback (1-2 seconds)
```bash
# Quick syntax check with lightweight model
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain --model llama3.2:1b
```

**Best for**: Rapid iteration, quick sanity checks

### Balanced Review (5-10 seconds)
```bash
# General code review with medium model
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain --task quick-review
# Uses qwen2.5-coder:3b (defined in models.json)
```

**Best for**: Daily development, code smell detection

### Deep Analysis (20-30 seconds)
```bash
# Thorough security and architecture review
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain --task security
# Uses deepseek-coder-v2:16b (defined in models.json)
```

**Best for**: Security audits, pre-production reviews

## Example 3: Review Different File Types

Local-brain works with code, design docs, and tickets:

### Code Review
```bash
echo '{"file_path":"src/main.rs","meta":{"kind":"code","review_focus":"refactoring"}}' | ./target/release/local-brain --task quick-review
```

### Design Document Review
```bash
echo '{"file_path":"DESIGN.md","meta":{"kind":"design-doc","review_focus":"risk"}}' | ./target/release/local-brain --task design-review
```

### Ticket/Issue Review
```bash
echo '{"file_path":"TICKET-123.md","meta":{"kind":"ticket","review_focus":"general"}}' | ./target/release/local-brain --task triage
```

## Common Workflows

### Pre-Commit Hook
```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
./target/release/local-brain --git-diff --task quick-review | jq '.spikes | length' > /dev/null
if [ $? -eq 0 ]; then
    echo "✓ Code review passed"
fi
```

### CI/CD Integration
```bash
# In your CI script
./target/release/local-brain --git-diff --task security > review.json
jq '.spikes | length' review.json
# Fail build if critical issues found
```

### Interactive Development
```bash
# Review current file while editing
echo '{"file_path":"'$(pwd)'/src/lib.rs"}' | ./target/release/local-brain --model qwen2.5-coder:3b | jq .
```

## Understanding the Output

### Field Definitions

- **spikes**: Issues to investigate (complexity, bugs, security risks)
- **simplifications**: Refactoring opportunities (DRY violations, over-engineering)
- **defer_for_later**: Low-priority improvements (nice-to-haves)
- **other_observations**: General notes (good practices, patterns)

### Output Formats

**Pretty print with jq**:
```bash
./target/release/local-brain --git-diff | jq .
```

**Extract specific findings**:
```bash
# Show only spikes
./target/release/local-brain --git-diff | jq '.spikes'

# Count findings
./target/release/local-brain --git-diff | jq '.spikes | length'
```

**Save to file**:
```bash
./target/release/local-brain --git-diff > review-results.json
```

## Performance Expectations

| File Size | Model | Time | Quality |
|-----------|-------|------|---------|
| 100 lines | llama3.2:1b | ~2s | Quick scan |
| 300 lines | qwen2.5-coder:3b | ~5s | Good depth |
| 500 lines | deepseek-coder-v2:16b | ~20s | Thorough |

**Tip**: Use faster models for iteration, larger models for final review.

## Troubleshooting Quick Checks

### No output?
```bash
# Check for errors on stderr
./target/release/local-brain < input.json 2>&1
```

### Model too slow?
```bash
# Switch to faster model
./target/release/local-brain --model llama3.2:1b
```

### Invalid JSON error?
```bash
# Validate your input
echo '{"file_path":"src/main.rs"}' | python3 -m json.tool
```

## What's Next?

Now that you've completed the quickstart:

**Dive Deeper**:
- [MODELS.md](MODELS.md) - Choose the right model for each task
- [README.md](README.md) - Advanced features and integrations
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions

**Integration**:
- Claude Code skill: `.claude/skills/local-brain/SKILL.md`
- Pre-commit hooks: Add to `.git/hooks/`
- CI/CD pipelines: See [CONTRIBUTING.md](CONTRIBUTING.md)

**Need Help?**:
- [GitHub Issues](https://github.com/IsmaelMartinez/local-brain/issues) - Report bugs or request features
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Self-service debugging

Happy reviewing! 🎉
