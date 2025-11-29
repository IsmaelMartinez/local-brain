# Local Brain

[![CI](https://github.com/IsmaelMartinez/local-brain/actions/workflows/ci.yml/badge.svg)](https://github.com/IsmaelMartinez/local-brain/actions/workflows/ci.yml)

Offload code reviews to local Ollama LLMs for high-quality, fast feedback—optimized for Claude Code integration.

## What It Does

Perform AI code reviews locally using LLMs:
- Review code for bugs, complexity, and refactoring opportunities
- Review git changes, directories, or specific files
- Analyze design docs, tickets, and other documents
- Auto-select appropriate models based on review type
- Output structured Markdown (no JSON parsing needed)

## Get Started

### Option 1: Claude Code Plugin (Easiest)

```bash
/plugin marketplace add IsmaelMartinez/local-brain
/plugin install local-brain
```

Then in Claude Code: "Review this file"

### Option 2: Standalone Binary

```bash
# Pre-built binaries
curl -L https://github.com/IsmaelMartinez/local-brain/releases/latest/download/local-brain-$(uname -m)-$(uname -s | tr '[:upper:]' '[:lower:]').tar.gz | tar xz

# Or via Cargo
cargo install local-brain

# Your first review
local-brain --files src/main.rs
```

## Quick Commands

```bash
# Single file
local-brain --files src/main.rs

# Multiple files
local-brain --files src/main.rs,src/lib.rs

# Git changes
local-brain --git-diff

# Directory
local-brain --dir src --pattern "*.rs"

# With specific model
local-brain --model qwen2.5-coder:3b --files src/main.rs

# Security review
local-brain --task security --files auth.rs
```

## Documentation

### For Users
- **[Quick Start](docs/QUICK_START.md)** — 5-minute setup
- **[Usage Guide](docs/USAGE_GUIDE.md)** — Common patterns and options
- **[Models](docs/MODELS.md)** — Model selection guide
- **[Installation](docs/INSTALLATION.md)** — Detailed platform setup
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** — Common issues & solutions

### For Contributors
- **[Setup Guide](tech/SETUP.md)** — Development environment
- **[Architecture](tech/ARCHITECTURE.md)** — System design & code structure
- **[Testing](tech/TESTING.md)** — Test strategy
- **[Contributing](CONTRIBUTING.md)** — Development workflow
- **[Release](tech/RELEASE.md)** — Release process

## Requirements

- Ollama running locally (default: http://localhost:11434)
- At least one model: `ollama pull qwen2.5-coder:3b`

## Why Local Brain?

- **Fast** — 10-30 second reviews (no Claude API calls)
- **Offline** — Works without internet
- **Cheap** — No per-request costs
- **Private** — Code never leaves your machine
- **Integrated** — Works seamlessly with Claude Code

## Architecture

- Single-file Rust CLI (~800 lines)
- HTTP client for local Ollama API
- Structured Markdown output
- Zero external API calls

See [Architecture Guide](tech/ARCHITECTURE.md) for details.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Quick start for developers:
```bash
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain
cargo build --release
./target/release/local-brain --files src/main.rs
```

## License

MIT License - see LICENSE file

## Links

- **GitHub** — https://github.com/IsmaelMartinez/local-brain
- **Issues** — https://github.com/IsmaelMartinez/local-brain/issues
- **Releases** — https://github.com/IsmaelMartinez/local-brain/releases
