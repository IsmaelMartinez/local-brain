# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Local Brain is a Rust CLI tool that performs structured code reviews using local Ollama LLM models. It's designed to offload routine review tasks from Claude Code to local models, minimizing context usage while providing Markdown-formatted output.

## Development Commands

### Building and Testing
```bash
# Build release binary
cargo build --release

# Run tests
cargo test

# Run specific test
cargo test test_name

# Integration tests (requires Ollama)
./tests/integration_test.sh

# Lint
cargo clippy

# Format
cargo fmt

# Dry run (no Ollama needed)
./target/release/local-brain --dry-run --files src/main.rs
```

### Running Local Brain
```bash
# Review specific files
./target/release/local-brain --files "src/main.rs"

# Review git changes
./target/release/local-brain --git-diff

# Review multiple files
./target/release/local-brain --files "src/main.rs,src/lib.rs"

# Review directory
./target/release/local-brain --dir src --pattern "*.rs"

# With specific model
./target/release/local-brain --model "qwen2.5-coder:3b" --files "src/main.rs"

# With document type and review focus
./target/release/local-brain --files "src/auth.rs" --kind code --review-focus security
```

## Architecture

### Single-File Structure
All code lives in `src/main.rs`:
- CLI Arguments: clap-based CLI with multiple modes
- Data Structures: ModelRegistry (for model configuration)
- Main Flow: Entry point and mode selection
- Model Selection: Priority: CLI flag > task > default
- Prompt Building: System/user prompt construction for Markdown output
- Ollama API: HTTP POST to /api/chat endpoint
- Response: Pass-through Markdown from LLM

### Key Components

**Input Modes** (all via CLI flags):
1. `--files`: Comma-separated list of files
2. `--git-diff`: Reviews all changed files in git
3. `--dir` + `--pattern`: Directory walking with glob pattern

**CLI Metadata Flags**:
- `--kind`: Document type (code, design-doc, ticket, other)
- `--review-focus`: Review focus (refactoring, readability, performance, risk, general)
- `--model`: Override model selection
- `--task`: Task-based model selection

**Output Structure** (Markdown):
```markdown
# Code Review

### filename.ext

## Issues Found
- **Title**: Description (lines: X-Y)

## Simplifications
- **Title**: Description

## Consider Later
- **Title**: Description

## Other Observations
- General note
```

**Model Selection** (`models.json`):
- Task mappings: `--task quick-review` → `qwen2.5-coder:3b`
- Default model: `deepseek-coder-v2-8k`
- Override via `--model` flag

### Error Handling
- Uses `anyhow::Result` throughout
- Context added with `.context("message")?`
- User-facing messages via `eprintln!`
- Markdown output to stdout, diagnostics to stderr

## Claude Code Integration

### Skill System
Located in `.claude/skills/local-brain/SKILL.md`:
- Triggered when user requests code review
- Launches haiku subagent to run local-brain
- Formats structured output for presentation
- Minimizes context usage by offloading to local LLM

### Usage Pattern
When user asks "review this file":
1. Verify file exists
2. Run local-brain with appropriate flags: `local-brain --files path/to/file`
3. Add metadata flags if known: `--kind code --review-focus security`
4. Parse Markdown output and present categorized findings

## Important Patterns

### Adding New Models
1. Test with Ollama: `ollama pull model:tag`
2. Add to `models.json` with metadata (size, RAM, speed tier)
3. Optionally add task mapping
4. Test: `./target/release/local-brain --model model:tag --files test.rs`

### Adding CLI Flags
1. Update `Cli` struct in main.rs
2. Handle in `main()` or appropriate function
3. Update README.md help text
4. Add test coverage

### Modifying Output Structure
1. Update system prompt to modify Markdown section headings
2. Update `.claude/skills/local-brain/SKILL.md` documentation
3. Update test expectations for new format
4. Run integration tests

## Testing Strategy

- Unit tests at bottom of main.rs
- Integration test: `tests/integration_test.sh`
- Use `--dry-run` to test without Ollama
- Manual verification: check Markdown structure and sections

## Release Process

Automated via GitHub Actions on version tags from `main`:
1. Update version in Cargo.toml
2. Commit: `git commit -m "Bump version to X.Y.Z"`
3. Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
4. Push: `git push origin main && git push origin vX.Y.Z`
5. CI builds cross-platform binaries and creates GitHub release

## Dependencies

- `serde`/`serde_json`: Configuration (models.json) parsing
- `reqwest`: HTTP client for Ollama API
- `anyhow`: Error handling
- `clap`: CLI parsing

## External Requirements

- Ollama running locally (default: http://localhost:11434)
- At least one model pulled: `ollama pull qwen2.5-coder:3b`
