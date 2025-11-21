# Quick Model Reference

## TL;DR - Model Selection

```bash
# Fastest (9s) - Quick reviews, CI/CD
./target/release/local-brain --model llama3.2:1b

# Best balance (11s) - Daily use, interactive
./target/release/local-brain --model phi3:mini

# Most detailed (27s) - Thorough code reviews
./target/release/local-brain --model qwen2.5-coder:3b

# General purpose (12s) - Documentation, mixed content
./target/release/local-brain --model qwen2.5:3b
```

## Test Results Summary

| Model | Status | Time | Quality |
|-------|--------|------|---------|
| qwen2.5-coder:3b | ✓ PASS | 27s | Excellent |
| llama3.2:1b | ✓ PASS | 9s | Good |
| phi3:mini | ✓ PASS | 11s | Very Good |
| qwen2.5:3b | ✓ PASS | 12s | Very Good |

## When to Use Each Model

### llama3.2:1b (Fastest)
- Pre-commit hooks
- CI/CD pipelines
- Quick file summaries
- Rapid iteration during development
- Low-resource environments

### phi3:mini (Recommended Default)
- Interactive development
- IDE integrations
- General code review
- Documentation checks
- Best speed/quality balance

### qwen2.5-coder:3b (Most Thorough)
- Pull request reviews
- Important code changes
- Security-critical code
- Complex refactoring
- Final review before merge

### qwen2.5:3b (Versatile)
- Requirements documents
- Design documents
- Mixed content
- Business logic
- Non-code reviews

## Usage Examples

```bash
# Test with test file
echo '{"file_path": "'$(pwd)'/tests/fixtures/code_smells.js", "meta": {"kind": "code"}}' | \
  ./target/release/local-brain --model llama3.2:1b | jq

# Use task-based selection (requires models.json)
echo '{"file_path": "'$(pwd)'/tests/fixtures/code_smells.js"}' | \
  ./target/release/local-brain --task quick-review | jq

# Review a real file
echo '{"file_path": "'$(pwd)'/src/main.rs"}' | \
  ./target/release/local-brain --model phi3:mini | jq
```

## Validation Details

All models validated on 2025-11-21:
- ✓ Successfully load from Ollama
- ✓ Return valid JSON
- ✓ Detect code smells correctly
- ✓ Follow expected output schema
- ✓ Reasonable response times

See detailed results in:
- `MODEL_VALIDATION_RESULTS.md` - Full test results with sample outputs
- `MODEL_COMPARISON_ANALYSIS.md` - Detailed performance comparison
- `validate_models.sh` - Automated validation script

## Re-running Validation

```bash
# Run validation script
./validate_models.sh

# Test a specific model manually
echo '{"file_path": "'$(pwd)'/tests/fixtures/code_smells.js", "meta": {"kind": "code"}}' | \
  ./target/release/local-brain --model qwen2.5-coder:3b | jq
```

## Next Steps

1. Choose appropriate model for your workflow
2. Consider automating model selection via task mappings
3. Test with your actual codebase files
4. Monitor performance with larger files
5. Adjust model choice based on real-world usage
