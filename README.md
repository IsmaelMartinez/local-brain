# Local Brain

[![CI](https://github.com/IsmaelMartinez/local-brain/actions/workflows/ci.yml/badge.svg)](https://github.com/IsmaelMartinez/local-brain/actions/workflows/ci.yml)

Offload context to local Ollama LLMs for code reviews and document analysis—outputs structured Markdown, optimized for Claude Code integration.

## What It Does

- Review code for bugs, complexity, and refactoring opportunities
- Review git changes with `--git-diff`
- Review directories with `--dir` and `--pattern`
- Review multiple files with `--files`
- Analyze design docs and tickets
- Auto-select models by task (1B-16B)

## Installation

**Requirements**: Ollama running locally with at least one model pulled.

```bash
# Quick install (macOS/Linux)
curl -L https://github.com/IsmaelMartinez/local-brain/releases/latest/download/local-brain-$(uname -m)-$(uname -s | tr '[:upper:]' '[:lower:]').tar.gz | tar xz
sudo mv local-brain /usr/local/bin/

# Or via Cargo
cargo install local-brain

# Install as Claude Code plugin
/plugin marketplace add IsmaelMartinez/local-brain
/plugin install local-brain
```

See [INSTALLATION.md](INSTALLATION.md) for detailed platform-specific instructions, Ollama setup, and model recommendations.

## Quick Start

```bash
# Verify installation
local-brain --version

# Review a file
local-brain --files src/main.rs

# Review git changes
local-brain --git-diff --task quick-review

# Review directory
local-brain --dir src --pattern "*.rs"

# Review specific files
local-brain --files src/main.rs,src/lib.rs

# Specify review type and focus
local-brain --files src/auth.rs --kind code --review-focus security
```

## Use Cases

**Pre-commit Review**
```bash
# Review staged changes before committing
local-brain --git-diff --kind code --review-focus refactoring
```

**Security Audit**
```bash
# Focus on security concerns in authentication code
local-brain --files src/auth.rs,src/session.rs --review-focus security
```

**Documentation Quality Check**
```bash
# Review all markdown docs for clarity
local-brain --dir docs --pattern "*.md" --kind other --review-focus readability
```

**CI/CD Integration**
```yaml
# .github/workflows/review.yml
- name: Code Review with Local Brain
  run: |
    ollama pull qwen2.5-coder:3b
    local-brain --git-diff > review.md
    cat review.md >> $GITHUB_STEP_SUMMARY
```

## Models

Optimized for 16GB RAM systems:

- `llama3.2:1b` - Fast, simple tasks (2s)
- `qwen2.5-coder:3b` - Balanced, code-focused (5s)
- `phi3:mini` - Good quality, low memory (8s)

See [MODELS.md](MODELS.md) for details.

## Documentation

- [INSTALLATION.md](INSTALLATION.md) - Setup
- [QUICKSTART.md](QUICKSTART.md) - Tutorial
- [MODELS.md](MODELS.md) - Model guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Issues
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development

## License

MIT
