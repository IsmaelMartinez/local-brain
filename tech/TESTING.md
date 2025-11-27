# Testing Guide

Testing strategy for local-brain development.

## Test Types

### Unit Tests

Located at bottom of `src/main.rs` (lines 752+)

Test individual functions:
- Prompt building with different inputs
- Model registry loading
- CLI argument parsing

```bash
# Run all unit tests
cargo test

# Run specific test
cargo test test_build_prompt

# Run with output
cargo test -- --nocapture --test-threads=1
```

### Integration Tests

End-to-end tests with real file processing

```bash
# Run integration tests (uses dry-run, no Ollama)
cargo test --test integration

# Manual integration test
./target/release/local-brain --dry-run --files src/main.rs
```

### Smoke Tests

Quick validation that everything works

```bash
# Dry run (no Ollama needed)
./target/release/local-brain --dry-run --files src/main.rs

# Real review (needs Ollama running)
./target/release/local-brain --files src/main.rs

# Git diff mode
./target/release/local-brain --git-diff

# Directory review
./target/release/local-brain --dir src --pattern "*.rs"
```

---

## Running Tests

### All Tests

```bash
# Standard test run
cargo test

# With output printed
cargo test -- --nocapture

# Single-threaded (for debugging)
cargo test -- --test-threads=1 --nocapture
```

### Specific Test

```bash
# Run one test
cargo test test_name

# Run tests matching pattern
cargo test prompt
```

### Debug Test

```bash
# Print debug info
cargo test test_name -- --nocapture

# Keep output between tests
cargo test -- --nocapture --test-threads=1
```

---

## Test Coverage

Current test coverage includes:

- [ ] **Prompt Building**: Various input combinations
- [ ] **Model Registry**: Loading and parsing
- [ ] **CLI Argument Parsing**: Flag combinations
- [ ] **File Reading**: Single/multiple files
- [ ] **Git Diff**: Staged and unstaged changes
- [ ] **Directory Pattern**: Glob matching
- [ ] **Ollama Integration**: API calls (with mocks)
- [ ] **Error Handling**: Graceful failures
- [ ] **Output Format**: Valid Markdown structure

---

## Manual Testing Checklist

Before submitting changes, verify:

### Build & Compilation
- [ ] `cargo build` succeeds (debug)
- [ ] `cargo build --release` succeeds
- [ ] `cargo fmt --all` shows no changes
- [ ] `cargo clippy` shows no warnings
- [ ] `cargo test` passes

### Dry-Run (No Ollama needed)
- [ ] `local-brain --dry-run --files src/main.rs` works
- [ ] `local-brain --dry-run --files a.rs,b.rs` works
- [ ] `local-brain --dry-run --dir src --pattern "*.rs"` works

### Single File Review (Requires Ollama)
- [ ] `local-brain --files src/main.rs` produces valid Markdown
- [ ] Output contains all sections (Issues, Simplifications, etc.)
- [ ] Timeout works: file completes in < 120s

### Multiple Files
- [ ] `local-brain --files a.rs,b.rs` reviews both files
- [ ] Output shows separate reviews per file
- [ ] Process doesn't hang or timeout

### Git Diff Mode
- [ ] `local-brain --git-diff` with staged changes works
- [ ] `local-brain --git-diff` with unstaged changes works
- [ ] Correctly identifies changed files

### Directory Review
- [ ] Pattern matching works: `--dir src --pattern "*.rs"`
- [ ] Pattern filtering works: glob syntax accepted
- [ ] Large directories (10+ files) handle correctly

### Model Selection
- [ ] `--task quick-review` uses fast model
- [ ] `--task security` uses appropriate model
- [ ] `--model explicit-model` overrides defaults
- [ ] `MODEL_NAME=xyz` env var works

### Error Handling
- [ ] Invalid file path: clear error message
- [ ] Ollama not running: helpful error
- [ ] Invalid model: informative error
- [ ] Timeout triggered: caught and reported
- [ ] Empty response: handled gracefully

### Output Quality
- [ ] Markdown is valid (can render)
- [ ] Markdown sections match expected format
- [ ] Line numbers present in Issues Found
- [ ] No JSON in output (should be pure Markdown)

---

## Continuous Integration

GitHub Actions tests:
- Rust 1.70+
- Linux, macOS, Windows
- Release build
- All tests pass

See `.github/workflows/*.yml` for CI configuration.

---

## Performance Testing

### Benchmarking

```bash
# Time a single review
time ./target/release/local-brain --files src/main.rs

# Time multiple reviews
time ./target/release/local-brain --dir src --pattern "*.rs"

# Profile with release build
cargo build --release
perf record -g ./target/release/local-brain --files src/main.rs
perf report
```

### Expected Performance

| Scenario | Model | Time |
|----------|-------|------|
| Single file (300 lines) | qwen2.5-coder:3b | 10-15s |
| Single file (300 lines) | deepseek-coder-v2-8k | 20-30s |
| 5 files (300 lines each) | qwen2.5-coder:3b | 50-75s |
| Dry run | N/A | <1s |

---

## Testing New Features

### Before Adding a Feature

1. Write unit tests for new functions
2. Write integration tests for new modes
3. Add to smoke test checklist
4. Document expected behavior

### Feature Testing Template

```bash
# Build with feature
cargo build --release

# Basic test
./target/release/local-brain --new-flag --files test.rs

# Error cases
./target/release/local-brain --new-flag --files nonexistent.rs

# Integration
./target/release/local-brain --new-flag --git-diff

# Performance
time ./target/release/local-brain --new-flag --files large_file.rs
```

---

## Debugging Failed Tests

### Get More Information

```bash
# Show all output
cargo test failed_test -- --nocapture

# With logging
RUST_LOG=debug cargo test failed_test

# Single threaded for reproducibility
cargo test failed_test -- --test-threads=1
```

### Check Dependencies

```bash
# Verify Ollama is running
ollama ps

# Verify models are available
ollama list

# Check network connectivity
curl http://localhost:11434/api/tags
```

### Common Issues

**Test hangs**
- Check if Ollama is running
- Increase timeout: `--timeout 180`
- Try with fast model: `--model qwen2.5-coder:3b`

**Test fails with "Empty response"**
- Model may have crashed
- Check Ollama logs
- Try again with different model

**Formatting test fails**
- Run `cargo fmt --all` to auto-fix
- Check for trailing whitespace
- Verify line endings (LF not CRLF)

---

## Test Maintenance

### Updating Tests

When changing behavior:
1. Update relevant tests
2. Add new tests for new behavior
3. Verify all tests pass
4. Update this documentation

### Deprecating Tests

Mark old tests as ignored:
```rust
#[test]
#[ignore]  // Deprecated: Feature removed in v0.3.0
fn old_test() {
    // ...
}
```

Run ignored tests:
```bash
cargo test -- --ignored
```

---

## Resources

- [Rust Testing Documentation](https://doc.rust-lang.org/book/ch11-00-testing.html)
- [Cargo Test Guide](https://doc.rust-lang.org/cargo/commands/cargo-test.html)

See [SETUP.md](SETUP.md) for environment setup and [ARCHITECTURE.md](ARCHITECTURE.md) for code overview.
