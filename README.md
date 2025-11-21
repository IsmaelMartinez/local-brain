# Local Brain

Offload context to local Ollama LLMs for code reviews and document analysis—optimized for Claude Code integration.

## What It Does

- Review code for bugs, complexity, and refactoring opportunities
- Review git changes with `--git-diff`
- Analyze design docs and tickets
- Auto-select models by task (1B-16B)

## Quick Start

```bash
# Install
See INSTALLATION.md for setup

# Review a file
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain

# Review git changes
./target/release/local-brain --git-diff --task quick-review
```

## Models

- `llama3.2:1b` - Fast (2s)
- `qwen2.5-coder:3b` - Balanced (5s)
- `deepseek-coder-v2:16b` - Thorough (20s)

See [MODELS.md](MODELS.md) for details.

## Documentation

- [INSTALLATION.md](INSTALLATION.md) - Setup
- [QUICKSTART.md](QUICKSTART.md) - Tutorial
- [MODELS.md](MODELS.md) - Model guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Issues
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development

## License

MIT
