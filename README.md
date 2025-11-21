# Local Brain

Offload context and logic to local Ollama LLM models for code reviews, documentation analysis, and more—optimized for Claude Code with minimal context usage.

## What It Does

- **Code Reviews**: Detect bugs, complexity, and refactoring opportunities
- **Git Integration**: Review all changed files before committing
- **Documentation Analysis**: Evaluate design docs, tickets, and technical writing
- **Model Specialization**: Automatic model selection based on task type (1B-16B models)

## Quick Start

```bash
# Install: See detailed instructions
👉 [INSTALLATION.md](INSTALLATION.md)

# First review: 5-minute tutorial
👉 [QUICKSTART.md](QUICKSTART.md)

# Quick example
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain --task quick-review
```

## Key Features

**Model Selection**: Choose the right model for each task
- Fast feedback: `llama3.2:1b` (1-2 seconds)
- Balanced review: `qwen2.5-coder:3b` (5 seconds)
- Deep analysis: `deepseek-coder-v2:16b` (20 seconds)

**Git Diff Integration**: Review changed files with one command
```bash
./target/release/local-brain --git-diff --task quick-review
```

**Claude Code Integration**: Lightweight subagent keeps context minimal (~600 tokens vs 5500+)

**Structured Output**: Returns actionable JSON with spikes, simplifications, and observations

## Documentation

- [Installation Guide](INSTALLATION.md) - System setup and prerequisites
- [Quick Start Tutorial](QUICKSTART.md) - 5-minute walkthrough with examples
- [Model Selection Guide](MODELS.md) - Choose the right model for your task
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
- [Contributing](CONTRIBUTING.md) - Development guide and architecture

## Performance

| File Size | Model | Time | Use Case |
|-----------|-------|------|----------|
| 100 lines | llama3.2:1b | ~2s | Quick sanity check |
| 300 lines | qwen2.5-coder:3b | ~5s | Daily development |
| 500 lines | deepseek-coder-v2:16b | ~20s | Security audit |

## License

MIT - see [LICENSE](LICENSE)
