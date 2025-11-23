# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Local Brain is a Rust CLI tool that performs structured code reviews using local Ollama LLM models. It's designed to offload routine review tasks from Claude Code to local models, minimizing context usage while providing JSON-structured output.

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
# Review file via stdin
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain

# Review git changes
./target/release/local-brain --git-diff

# Review specific files
./target/release/local-brain --files "src/main.rs,src/lib.rs"

# Review directory
./target/release/local-brain --dir src --pattern "*.rs"

# With specific model
./target/release/local-brain --model "qwen2.5-coder:3b" --files "src/main.rs"
```

## Architecture

### Single-File Structure
All code lives in `src/main.rs` (~600 lines):
- CLI Arguments (lines 18-90): clap-based CLI with multiple modes
- Data Structures (lines 96-150): InputPayload, OutputPayload, ModelRegistry
- Main Flow (lines ~97-124): Entry point and mode selection
- Model Selection (lines ~267-336): Priority: CLI flag > JSON > task > default
- Prompt Building (lines ~343-403): System/user prompt construction
- Ollama API (lines ~409-463): HTTP POST to /api/chat endpoint
- Response Parsing (lines ~469-504): JSON extraction from markdown

### Key Components

**Input Modes**:
1. stdin: JSON with `file_path` and optional `meta` (kind, review_focus)
2. `--git-diff`: Reviews all changed files in git
3. `--files`: Comma-separated list of files
4. `--dir` + `--pattern`: Directory walking with glob pattern

**Output Structure**:
```json
{
  "spikes": [
    { "title": "string", "summary": "string", "lines": "optional string" }
  ],
  "simplifications": [
    { "title": "string", "summary": "string" }
  ],
  "defer_for_later": [
    { "title": "string", "summary": "string" }
  ],
  "other_observations": ["string", "string"]
}
```

**Model Selection** (`models.json`):
- Task mappings: `--task quick-review` → `qwen2.5-coder:3b`
- Default model: `deepseek-coder-v2-8k`
- Override via `--model` flag or JSON `ollama_model` field

### Error Handling
- Uses `anyhow::Result` throughout
- Context added with `.context("message")?`
- User-facing messages via `eprintln!`
- JSON output to stdout, diagnostics to stderr

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
2. Build JSON input with file_path and metadata
3. Pipe to local-brain: `echo '[JSON]' | local-brain`
4. Parse and present categorized findings

## Important Patterns

### Adding New Models
1. Test with Ollama: `ollama pull model:tag`
2. Add to `models.json` with metadata (size, RAM, speed tier)
3. Optionally add task mapping
4. Test: `./target/release/local-brain --model model:tag --files test.rs`

### Adding CLI Flags
1. Update `Cli` struct in main.rs:18-90
2. Handle in `main()` or appropriate function
3. Update README.md help text
4. Add test coverage

### Modifying Output Structure
1. Update `OutputPayload` struct
2. Update system prompt to include new field
3. Update `.claude/skills/local-brain/SKILL.md`
4. Run integration tests

## Testing Strategy

- Unit tests at bottom of main.rs (lines ~510+)
- Integration test: `tests/integration_test.sh`
- Use `--dry-run` to test without Ollama
- Manual verification: pipe to `jq` to validate JSON

## Release Process

Automated via GitHub Actions on version tags from `main`:
1. Update version in Cargo.toml
2. Commit: `git commit -m "Bump version to X.Y.Z"`
3. Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
4. Push: `git push origin main && git push origin vX.Y.Z`
5. CI builds cross-platform binaries and creates GitHub release

## Dependencies

- `serde`/`serde_json`: JSON serialization
- `reqwest`: HTTP client for Ollama API
- `anyhow`: Error handling
- `clap`: CLI parsing

## External Requirements

- Ollama running locally (default: http://localhost:11434)
- At least one model pulled: `ollama pull qwen2.5-coder:3b`
