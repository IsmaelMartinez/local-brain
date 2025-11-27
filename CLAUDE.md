# CLAUDE.md

Guidance for Claude Code when working with the local-brain codebase.

## Project Overview

Local Brain is a Rust CLI tool that performs structured code reviews using local Ollama LLM models. It minimizes context usage while providing high-quality Markdown reviews.

**Single-file design:** All code lives in `src/main.rs` (~800 lines)

## When Working WITH Code (Development Tasks)

For development, architecture, testing, or refactoring work:

1. **Architecture Context** → See [tech/ARCHITECTURE.md](tech/ARCHITECTURE.md)
   - System design and data flow
   - Component structure and responsibilities
   - Parsing and validation logic

2. **Setup & Testing** → See [tech/SETUP.md](tech/SETUP.md) and [tech/TESTING.md](tech/TESTING.md)
   - Build commands: `cargo build --release`
   - Test commands: `cargo test`
   - Manual testing and verification

3. **Contributing Guidelines** → See [CONTRIBUTING.md](CONTRIBUTING.md)
   - Code style (Rust conventions)
   - Pull request process
   - Release process (in [tech/RELEASE.md](tech/RELEASE.md))

## When USING Local Brain (Routine Tasks)

For using the tool for code reviews:

1. **Skill Usage** → See [local-brain/skills/local-brain/SKILL.md](local-brain/skills/local-brain/SKILL.md)
   - Primary reference for tool usage patterns
   - Tiered architecture (hooks → binary → subagent)
   - When to invoke vs. when to delegate

2. **Common Patterns** → Quick reference below

## Common Usage Patterns

### Run a Single File Review

```bash
./target/release/local-brain --files "src/main.rs"
```

### Review With Specific Model

```bash
# Fast model
./target/release/local-brain --model "qwen2.5-coder:3b" --files "src/main.rs"

# Security-focused
./target/release/local-brain --task security --files "auth.rs"
```

### Dry Run (No Ollama Needed)

```bash
./target/release/local-brain --dry-run --files "src/main.rs"
```

### Review Git Changes

```bash
./target/release/local-brain --git-diff
```

### Batch Review (Multiple Files)

```bash
./target/release/local-brain --files "src/main.rs,src/lib.rs,tests/test.rs"
```

## Important Patterns

### Adding a New CLI Flag

1. Add to `Cli` struct (lines 60-99)
2. Handle in appropriate function (main, mode handlers, or review functions)
3. Add tests
4. Update documentation

### Adding a New Model

1. Pull with Ollama: `ollama pull model:tag`
2. Add to `models.json` with metadata
3. Test: `./target/release/local-brain --model model:tag --files test.rs`

### Handling Errors

Pattern: Use `anyhow::Result` with `.context()`

```rust
let content = std::fs::read_to_string(&path)
    .context(format!("Failed to read: {}", path.display()))?;
```

Messages go to stderr via `eprintln!`, Markdown output to stdout.

### Output Format

All reviews produce structured Markdown:
```markdown
## Issues Found
- **Title**: Description (lines: X-Y)

## Simplifications
- **Title**: Description

## Consider Later
- **Title**: Description

## Other Observations
- General note
```

## Key Implementation Details

### Model Selection Priority

1. `--model` flag (explicit override)
2. `--task` mapping (from models.json)
3. `MODEL_NAME` environment variable
4. Default model (deepseek-coder-v2-8k)

### Input Modes

- `--files`: Comma-separated list
- `--git-diff`: Git staged/modified files
- `--dir` + `--pattern`: Pattern matching in directory

### Ollama Integration

- HTTP POST to `localhost:11434/api/chat`
- 120s default timeout
- Response validation (non-empty content)
- Markdown pass-through (no JSON parsing)

### Error Handling

- User-friendly messages to stderr
- Markdown output only to stdout
- Context added at each error point
- Clear guidance for common issues (Ollama not running, model not found, etc.)

## Testing Checklist

Before committing:
```bash
cargo build --release
cargo test
cargo fmt --all
cargo clippy
./target/release/local-brain --dry-run --files src/main.rs
```

## Quick Reference

| Task | Command |
|------|---------|
| Build | `cargo build --release` |
| Test | `cargo test` |
| Format | `cargo fmt --all` |
| Lint | `cargo clippy` |
| Review file | `./target/release/local-brain --files src/main.rs` |
| Dry run | `./target/release/local-brain --dry-run --files src/main.rs` |
| Git diff | `./target/release/local-brain --git-diff` |
| Check Ollama | `ollama ps` |

## External Requirements

- Ollama running locally (http://localhost:11434)
- At least one model available

## Dependencies

- `clap` - CLI argument parsing
- `serde`/`serde_json` - JSON/config parsing
- `reqwest` - HTTP client for Ollama
- `anyhow` - Error handling/context

---

**For full architecture details:** See [tech/ARCHITECTURE.md](tech/ARCHITECTURE.md)

**For development setup:** See [tech/SETUP.md](tech/SETUP.md)

**For testing guidance:** See [tech/TESTING.md](tech/TESTING.md)
