# Development Setup

Get your local-brain development environment ready.

## Prerequisites

- **Rust** 1.70+ (via [rustup](https://rustup.rs/))
- **Ollama** running locally (default: http://localhost:11434)
- **Git**
- **At least one Ollama model** for testing

### Install Rust
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Install/Update Ollama
```bash
# macOS
brew install ollama

# Or download from https://ollama.ai

# Start Ollama
ollama serve
```

### Pull a test model
```bash
# Fast model for quick testing
ollama pull qwen2.5-coder:3b

# Or use the default model
ollama pull deepseek-coder-v2-8k
```

---

## Clone and Build

```bash
# Clone the repository
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain

# Build debug version (faster compilation)
cargo build

# Build release version (optimized)
cargo build --release

# Run tests
cargo test
```

---

## Development Commands

### Build

```bash
# Debug build (~30s)
cargo build

# Release build (~22s, optimized)
cargo build --release

# Clean build
cargo clean && cargo build --release
```

### Test

```bash
# Run all tests
cargo test

# Run specific test
cargo test test_build_prompt

# Run with output
cargo test -- --nocapture

# No-capture for debugging
cargo test test_name -- --nocapture --test-threads=1
```

### Lint & Format

```bash
# Check formatting
cargo fmt --all -- --check

# Auto-format code
cargo fmt --all

# Lint with clippy
cargo clippy

# Clippy with all targets
cargo clippy --all-targets
```

### Run

```bash
# Run dry-run test (no Ollama needed)
./target/release/local-brain --dry-run --files src/main.rs

# Run real review
./target/release/local-brain --files src/main.rs

# Review git changes
./target/release/local-brain --git-diff

# With specific model
./target/release/local-brain --files src/main.rs --model qwen2.5-coder:3b

# With verbose logging
RUST_LOG=debug ./target/release/local-brain --files src/main.rs
```

---

## Debugging

### Check Ollama Status

```bash
# Is Ollama running?
ollama ps

# What models are available?
ollama list

# Test API directly
curl http://localhost:11434/api/tags
```

### View All Available Models

```bash
# See every installed model
ollama ls
```

### Check System Info

```bash
# Rust version
rustc --version
cargo --version

# System info
uname -a
```

---

## Common Development Tasks

### Add a New CLI Flag

1. Add to `Cli` struct (around line 60)
2. Parse in `main()` function
3. Use in appropriate handler
4. Test with `--help` to verify

### Change Error Handling

Use `anyhow::Result` and `.context()`:

```rust
let content = std::fs::read_to_string(&path)
    .context(format!("Failed to read: {}", path.display()))?;
```

### Test Without Ollama

Use `--dry-run` flag:

```bash
./target/release/local-brain --dry-run --files src/main.rs
```

### Update Models

Edit `models.json`:
```json
{
  "models": [
    {"name": "new-model:tag", "size_gb": 5.0, "speed": "moderate"}
  ],
  "default_model": "new-model:tag"
}
```

---

## Environment Variables

### Ollama Host

```bash
# Use custom Ollama server
export OLLAMA_HOST="http://192.168.1.100:11434"
cargo run -- --files src/main.rs
```

### Default Model

```bash
# Override default model
export MODEL_NAME="qwen2.5-coder:3b"
cargo run -- --files src/main.rs
```

### Rust Logging

```bash
# Debug logging
RUST_LOG=debug cargo run -- --files src/main.rs

# Trace logging (very verbose)
RUST_LOG=trace cargo run -- --files src/main.rs
```

---

## Performance Tips

1. **Debug builds are faster to compile**: Use `cargo build` while developing
2. **Release builds run faster**: Use `cargo build --release` for testing performance
3. **Use small models for testing**: qwen2.5-coder:3b instead of deepseek-coder-v2-8k
4. **Dry-run mode is instant**: Use `--dry-run` to test without Ollama

---

## Troubleshooting

### Cargo Build Fails

```bash
# Update Rust
rustup update

# Clean build
cargo clean
cargo build

# Check Rust version (requires 1.70+)
rustc --version
```

### Tests Fail

```bash
# Run tests with output
cargo test -- --nocapture

# Run single test
cargo test specific_test_name -- --nocapture

# Make sure Ollama is running
ollama ps
```

### Ollama Connection Issues

```bash
# Is Ollama running?
ollama ps

# Start Ollama
ollama serve

# Check if port 11434 is available
lsof -i :11434

# Use custom host if needed
export OLLAMA_HOST="http://localhost:11434"
```

### Model Not Found

```bash
# List installed models
ollama list

# Pull missing model
ollama pull qwen2.5-coder:3b

# Check model exists
ollama show qwen2.5-coder:3b
```

---

## IDE Setup

### VS Code

Install Rust Analyzer extension for best experience:
- `rust-analyzer` - Language server
- `CodeLLDB` - Debugger (optional)

### Other Editors

Most modern editors support Rust via rust-analyzer.

---

## Next Steps

- See [TESTING.md](TESTING.md) for test strategy
- See [ARCHITECTURE.md](ARCHITECTURE.md) for code overview
- See ../CONTRIBUTING.md for contribution guidelines
