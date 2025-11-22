# Contributing to Local Brain

Thank you for your interest in contributing! This guide covers development setup, architecture, and contribution guidelines.

## Development Setup

### Prerequisites

- Rust 1.70+ (`rustup`)
- Ollama with at least one model (`ollama pull deepseek-coder-v2:16b`)
- Git

### Clone and Build

```bash
# Clone repository
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain

# Build debug version
cargo build

# Build release version
cargo build --release

# Run tests
cargo test

# Run with verbose logging
RUST_LOG=debug cargo run
```

## Architecture Overview

### Core Components

```
src/main.rs
├── CLI Arguments (clap)
├── Model Selection (models.json registry)
├── Input Processing (stdin or git diff)
├── Ollama API Integration (reqwest)
└── Output Formatting (structured JSON)
```

### Data Flow

1. **Input**: JSON via stdin or `--git-diff` flag
2. **Model Selection**: Priority system (CLI > JSON > task > default)
3. **File Reading**: Read file content from disk
4. **Prompt Building**: Construct system + user prompts
5. **Ollama Call**: POST to `/api/chat` endpoint
6. **Response Parsing**: Extract JSON, handle markdown fences
7. **Output**: Structured JSON to stdout

### Key Structures

**InputPayload** (src/main.rs:60-69):
```rust
struct InputPayload {
    file_path: PathBuf,           // Required: file to review
    meta: Option<Meta>,           // Optional: kind, review_focus
    ollama_model: Option<String>, // Optional: model override
}
```

**OutputPayload** (src/main.rs:81-91):
```rust
struct OutputPayload {
    spikes: Vec<ReviewItem>,              // Issues to investigate
    simplifications: Vec<ReviewItem>,     // Refactoring opportunities
    defer_for_later: Vec<ReviewItem>,     // Low priority items
    other_observations: Vec<String>,      // General notes
}
```

**ModelRegistry** (models.json):
```json
{
  "task_mappings": {
    "quick-review": "qwen2.5-coder:3b",
    "security": "deepseek-coder-v2:16b"
  },
  "default_model": "deepseek-coder-v2:16b"
}
```

## Code Organization

### File Structure

```
src/
└── main.rs                 # Single-file implementation
    ├── CLI Arguments       # Lines 18-34
    ├── Data Structures     # Lines 40-91
    ├── Main Flow           # Lines 97-124
    ├── Model Selection     # Lines 267-336
    ├── Prompt Building     # Lines 343-403
    ├── Ollama API          # Lines 409-463
    ├── Response Parsing    # Lines 469-504
    └── Tests               # Lines 510-537

.claude/skills/local-brain/
└── SKILL.md               # Claude Code integration

tests/
├── integration_test.sh    # End-to-end testing
└── fixtures/
    └── code_smells.js     # Test file with known issues

models.json                # Model registry
```

### Key Functions

- `main()` (97-124): Entry point, CLI parsing, mode selection
- `review_file()` (127-150): Core review logic
- `handle_git_diff()` (153-229): Git integration mode
- `select_model()` (268-291): Model selection priority
- `build_prompt()` (343-403): Prompt construction
- `call_ollama()` (421-463): HTTP request to Ollama
- `parse_ollama_response()` (471-482): JSON extraction
- `extract_json_from_markdown()` (486-504): Cleanup utility

## Making Changes

### Adding New Models

1. Test model with Ollama:
```bash
ollama pull new-model:tag
ollama run new-model:tag "Test prompt"
```

2. Add to `models.json`:
```json
{
  "models": {
    "new-model:tag": {
      "size_gb": 3.5,
      "ram_required_gb": 4,
      "speed_tier": "fast"
    }
  },
  "task_mappings": {
    "new-task": "new-model:tag"
  }
}
```

3. Test integration:
```bash
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain --model new-model:tag
```

### Adding New CLI Flags

1. Update `Cli` struct (src/main.rs:22-34):
```rust
#[derive(Parser, Debug)]
struct Cli {
    #[arg(long)]
    new_flag: Option<String>,
}
```

2. Handle flag in `main()` or appropriate function

3. Update README.md and QUICKSTART.md

4. Add tests

### Modifying Output Structure

1. Update `OutputPayload` struct (src/main.rs:81-91)
2. Update system prompt (src/main.rs:349-379) to include new field
3. Update parsing logic if needed
4. Update `.claude/skills/local-brain/SKILL.md`
5. Run integration tests

## Testing

### Unit Tests

```bash
# Run all tests
cargo test

# Run specific test
cargo test test_input_deserialization

# Run with output
cargo test -- --nocapture
```

### Integration Tests

```bash
# Run all integration tests (uses --dry-run, no Ollama needed)
cargo test --test integration

# End-to-end test with fixtures (requires Ollama)
./tests/integration_test.sh

# Manual test with dry-run
./target/release/local-brain --dry-run --files src/main.rs

# Manual test with real files (requires Ollama)
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain | jq .

# Test git diff mode
./target/release/local-brain --git-diff --task quick-review
```

### Testing Checklist

- [ ] Unit tests pass (`cargo test`)
- [ ] Integration test passes (`./tests/integration_test.sh`)
- [ ] Manual smoke test with real file
- [ ] Git diff mode works (if modified)
- [ ] Error cases handled gracefully
- [ ] Output JSON is valid (`| jq .`)

## Code Style

### Rust Conventions

- Follow [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- Use `rustfmt` for formatting: `cargo fmt`
- Use `clippy` for linting: `cargo clippy`
- Add doc comments for public functions
- Use meaningful variable names
- Keep functions under 50 lines when possible

### Error Handling

Use `anyhow` for error propagation:

```rust
fn example() -> Result<()> {
    let file = std::fs::read_to_string(path)
        .context("Failed to read file")?;
    Ok(())
}
```

### Logging

Use `eprintln!` for user-facing messages:

```rust
eprintln!("Reviewing {} changed file(s)...", count);
```

Keep stdout clean for JSON output.

## Pull Request Process

### Before Submitting

1. **Test thoroughly**:
   ```bash
   cargo test
   cargo clippy
   cargo fmt
   ./tests/integration_test.sh
   ```

2. **Update documentation**:
   - README.md if adding features
   - QUICKSTART.md if changing usage
   - TROUBLESHOOTING.md if fixing bugs

3. **Write clear commit messages**:
   ```
   Add --parallel flag for concurrent file reviews

   - Implement ThreadPool for parallel processing
   - Add --parallel CLI flag with thread count
   - Update README with usage examples
   ```

### Submitting PR

1. Fork repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes and commit
4. Push to your fork: `git push origin feature/your-feature`
5. Open PR against `main` branch

### PR Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Code formatted (`cargo fmt`)
- [ ] No clippy warnings
```

## Review Process

1. Maintainers will review within 1-2 weeks
2. Address feedback in new commits
3. Once approved, maintainer will merge
4. PR will be included in next release

## Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes (e.g., output structure change)
- **MINOR**: New features (e.g., new CLI flag)
- **PATCH**: Bug fixes (e.g., JSON parsing fix)

### Automated Release Pipeline

Releases are automated via GitHub Actions. When you push a version tag from the `main` branch:

1. **Tests run first** - `cargo test --all-features` and `cargo clippy`
2. **Main branch check** - Releases only happen from tags on `main`
3. **Cross-platform builds** - Binaries built for macOS (Intel/ARM), Linux, and Windows
4. **GitHub Release created** - Binaries uploaded automatically

### Creating a Release

```bash
# 1. Ensure you're on main with latest changes
git checkout main
git pull origin main

# 2. Update version in Cargo.toml
# version = "0.2.0"

# 3. Commit version bump
git add Cargo.toml Cargo.lock
git commit -m "Bump version to 0.2.0"

# 4. Create and push tag
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin main
git push origin v0.2.0

# 5. Monitor GitHub Actions for release completion
```

### Testing Without Ollama

Use `--dry-run` to test the full pipeline without calling Ollama:

```bash
# Test file review
./target/release/local-brain --dry-run --files src/main.rs

# Test directory review
./target/release/local-brain --dry-run --dir src --pattern "*.rs"

# Output shows what would be sent to Ollama
```

### Release Checklist

- [ ] All tests pass (`cargo test --all-features`)
- [ ] No clippy warnings (`cargo clippy -- -D warnings`)
- [ ] Version bumped in Cargo.toml
- [ ] CHANGELOG updated (if maintained)
- [ ] Tag created from `main` branch
- [ ] GitHub Actions release completed successfully
- [ ] Binaries downloadable from GitHub Releases

## Getting Help

- **Questions**: Open a [GitHub Discussion](https://github.com/IsmaelMartinez/local-brain/discussions)
- **Bugs**: Open a [GitHub Issue](https://github.com/IsmaelMartinez/local-brain/issues)
- **Features**: Open a [GitHub Issue](https://github.com/IsmaelMartinez/local-brain/issues) with "Feature Request" label

## Areas for Contribution

Looking for ideas? Check these areas:

**High Priority**:
- Directory walking support (review multiple files)
- Performance optimization (parallel processing)
- More model integrations (Claude, OpenAI)

**Good First Issues**:
- Add more task types to models.json
- Improve error messages
- Add more unit tests
- Documentation improvements

**Experimental**:
- Streaming output support
- Web UI for results
- IDE integrations (VS Code, JetBrains)

## Code of Conduct

Be respectful and constructive. We're all here to learn and improve.

Thank you for contributing! 🎉
