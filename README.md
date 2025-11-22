# Local Brain

[![CI](https://github.com/IsmaelMartinez/local-brain/actions/workflows/ci.yml/badge.svg)](https://github.com/IsmaelMartinez/local-brain/actions/workflows/ci.yml)

Offload context to local Ollama LLMs for code reviews and document analysis—optimized for Claude Code integration.

## What It Does

- Review code for bugs, complexity, and refactoring opportunities
- Review git changes with `--git-diff`
- Review directories with `--dir` and `--pattern`
- Review multiple files with `--files`
- Analyze design docs and tickets
- Auto-select models by task (1B-16B)

## Installation

### Option 1: Pre-built Binaries (Recommended)
Download from [GitHub Releases](https://github.com/IsmaelMartinez/local-brain/releases) for your platform:
- macOS (Intel/Apple Silicon)
- Linux (x86_64)
- Windows (x86_64)

Extract and add to PATH.

### Option 2: Cargo Install
```bash
cargo install local-brain
```

### Option 3: Cargo Binstall (Fast)
```bash
cargo binstall local-brain
```

### Option 4: Build from Source
```bash
git clone https://github.com/IsmaelMartinez/local-brain
cd local-brain
cargo build --release
```

### Option 5: Claude Code Plugin
```bash
# Add as a marketplace
/plugin marketplace add IsmaelMartinez/local-brain

# Install the plugin
/plugin install local-brain
```

Claude will automatically use local-brain to offload routine tasks (code review, doc analysis, planning) to local models.

See [INSTALLATION.md](INSTALLATION.md) for detailed setup.

## Quick Start

```bash
# Verify installation
local-brain --version

# Review a file
echo '{"file_path":"src/main.rs"}' | local-brain

# Review git changes
local-brain --git-diff --task quick-review

# Review directory
local-brain --dir src --pattern "*.rs"

# Review specific files
local-brain --files src/main.rs,src/lib.rs
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
