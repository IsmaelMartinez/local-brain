# Local Brain

A Rust binary that performs structured code reviews using local Ollama LLM models, optimized for Claude Code integration with minimal context usage.

## Quick Start

### Prerequisites

- Rust 1.70+ (`rustup`)
- Ollama (`ollama.ai`)
- An LLM model: `ollama pull deepseek-coder-v2-8k`

### Build & Run

```bash
# Build
cargo build --release

# Test
echo '{"file_path":"src/main.rs","meta":{"kind":"code","review_focus":"refactoring"}}' | ./target/release/local-brain
```

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `deepseek-coder-v2-8k` | Ollama model |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama endpoint |

## How It Works

The binary receives a **file path** (not content), reads the file, calls Ollama for review, and returns structured JSON:

```json
{
  "spikes": [...],           // Areas to investigate
  "simplifications": [...],   // Refactoring opportunities
  "defer_for_later": [...],   // Low priority items
  "other_observations": [...]  // General notes
}
```

This design keeps both main Claude conversation and subagent contexts minimal (~600 tokens vs 5500+).

## Documentation

- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - Complete technical specification
- **[VALIDATION_EXPERIMENTS.md](VALIDATION_EXPERIMENTS.md)** - Pre-implementation testing

## Development

```bash
cargo build          # Debug build
cargo test           # Run tests
cargo build --release # Optimized build
```

## License

MIT - see [LICENSE](LICENSE)
