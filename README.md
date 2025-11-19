# Local Context Helper

**Structured code and document reviews using local Ollama LLM models, optimized for Claude Code integration.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Local Context Helper is a Rust-based tool that performs AI-powered code reviews while keeping your Claude Code conversation context minimal. It achieves this by:

- **Passing file paths instead of content** between Claude Code and subagents
- **Using local LLM models** (via Ollama) for unlimited free reviews
- **Processing files in a disposable binary** that doesn't affect conversation context
- **Returning structured JSON reviews** with actionable insights

### Context Savings

| Component | Without Helper | With Helper | Savings |
|-----------|----------------|-------------|---------|
| Main Conversation | 500+ tokens | ~100 tokens | 80%+ |
| Subagent | 5000+ tokens | ~500 tokens | 90%+ |
| **Total** | **5500+ tokens** | **~600 tokens** | **89%+** |

## Quick Start

### Prerequisites

1. **Rust** (1.70+): [Install Rust](https://rustup.rs/)
2. **Ollama**: [Install Ollama](https://ollama.ai/)
3. **An LLM model**: `ollama pull llama3.2`

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/local-context-helper.git
cd local-context-helper

# Build the binary
cargo build --release

# Install to system (optional)
sudo cp target/release/local-context-optimizer /usr/local/bin/
```

### Basic Usage

```bash
# Set environment variables (optional)
export MODEL_NAME="llama3.2"
export OLLAMA_HOST="http://localhost:11434"

# Review a file
echo '{
  "file_path": "src/main.rs",
  "meta": {
    "kind": "code",
    "review_focus": "refactoring"
  }
}' | local-context-optimizer
```

### Example Output

```json
{
  "spikes": [
    {
      "title": "Complex error handling in main",
      "summary": "Multiple nested error handlers could be simplified using the ? operator and Result types.",
      "lines": "45-78"
    }
  ],
  "simplifications": [
    {
      "title": "Duplicate validation logic",
      "summary": "Input validation is repeated across three functions. Extract to shared validator."
    }
  ],
  "defer_for_later": [
    {
      "title": "Add integration tests",
      "summary": "Unit tests exist but integration tests would help catch API changes."
    }
  ],
  "other_observations": [
    "Good use of type safety",
    "Documentation is comprehensive"
  ]
}
```

## Architecture

```
┌─────────────┐
│ Claude Code │  ◄── Passes file paths (minimal context)
│   (Main)    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│   Subagent      │  ◄── Passes paths through (minimal context)
│  (Haiku 4.5)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Rust Binary            │  ◄── Does heavy lifting:
│  local-context-optimizer│     - Reads files
│                         │     - Calls Ollama
│                         │     - Returns review
└────────┬────────────────┘
         │
         ▼
┌─────────────────┐
│  Ollama API     │  ◄── Local LLM model
│  (Local Model)  │
└─────────────────┘
```

## Review Categories

### Spikes
Hotspots or areas requiring investigation. Complex code, potential bugs, or architectural concerns.

### Simplifications
Opportunities to reduce complexity, refactor, or optimize code.

### Defer for Later
Low-priority improvements that are safe to postpone.

### Other Observations
General notes, ideas, or observations that don't fit other categories.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `llama3.2` | Ollama model to use for reviews |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint |

### Input Format

```json
{
  "file_path": "/absolute/path/to/file",
  "meta": {
    "kind": "code | design-doc | ticket | other",
    "review_focus": "refactoring | readability | performance | risk | general"
  }
}
```

Both fields in `meta` are optional and will default to sensible values.

## Claude Code Integration

### Using as a Skill

Create `.claude/skills/local-context-optimiser/skill.md`:

```markdown
# Local Context Optimiser Skill

This skill performs structured reviews using a local LLM.

## Usage
1. Receive file path from main conversation
2. Determine metadata (kind, review_focus)
3. Build JSON: `{"file_path": "/path", "meta": {...}}`
4. Run: `echo '<json>' | local-context-optimizer`
5. Parse JSON output
6. Return human-friendly summary

## Example
\`\`\`bash
echo '{"file_path":"src/auth.rs","meta":{"kind":"code","review_focus":"refactoring"}}' | local-context-optimizer
\`\`\`
```

### Subagent Configuration

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for complete subagent setup instructions.

## Supported Models

Tested with:
- **llama3.2** - Good general purpose
- **qwen2.5-coder** - Optimized for code
- **mistral** - Alternative option
- **deepseek-coder** - Code specialist

Any Ollama model that supports JSON output should work.

## Development

### Project Structure

```
local-context-helper/
├── src/
│   └── main.rs              # Binary implementation
├── Cargo.toml               # Rust dependencies
├── README.md                # This file
├── IMPLEMENTATION_PLAN.md   # Detailed technical spec
├── VALIDATION_EXPERIMENTS.md # Pre-implementation validation
├── PROJECT_SUMMARY.md       # High-level overview
└── LICENSE                  # MIT License
```

### Building from Source

```bash
# Debug build
cargo build

# Release build (optimized)
cargo build --release

# Run tests
cargo test

# Run with logging
RUST_LOG=debug cargo run
```

### Running Tests

```bash
# Unit tests
cargo test

# Test with a real file
echo '{"file_path":"src/main.rs"}' | cargo run --release
```

## Validation Experiments

Before using in production, we recommend running the validation experiments in [VALIDATION_EXPERIMENTS.md](VALIDATION_EXPERIMENTS.md) to ensure:

- Ollama is properly configured
- Your chosen model returns reliable JSON
- Review quality meets your standards
- Performance is acceptable

## Troubleshooting

### "Failed to connect to Ollama"

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

### "Model not found"

```bash
# List available models
ollama list

# Pull a model
ollama pull llama3.2
```

### "Failed to parse Ollama response as JSON"

Some models are better at JSON generation than others. Try:
1. A code-focused model like `qwen2.5-coder`
2. Setting a different `MODEL_NAME`
3. Adjusting the system prompt in `src/main.rs`

### Performance Issues

```bash
# Use a smaller/faster model
export MODEL_NAME="llama3.2:1b"

# Or optimize the binary
cargo build --release --target-cpu=native
```

## Roadmap

### V1 (Current)
- [x] Basic binary structure
- [ ] Ollama integration
- [ ] Claude Code Skill
- [ ] Validation experiments
- [ ] Documentation

### V2 (Future)
- [ ] Batch processing (multiple files)
- [ ] Streaming responses
- [ ] Response caching
- [ ] Custom prompt templates
- [ ] Multiple output formats
- [ ] Review history

## Contributing

Contributions welcome! Please:

1. Run validation experiments first
2. Add tests for new features
3. Update documentation
4. Follow Rust style guidelines (`cargo fmt`)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Documentation

- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - Complete technical specification
- **[VALIDATION_EXPERIMENTS.md](VALIDATION_EXPERIMENTS.md)** - Pre-implementation testing
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - High-level project overview

## Status

**Planning Complete - Ready for Implementation**

See [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for current status and next steps.

## Questions?

- Check [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed specs
- Review [VALIDATION_EXPERIMENTS.md](VALIDATION_EXPERIMENTS.md) for testing guidance
- Open an issue for bugs or feature requests

---

**Built with** ❤️ **using Rust and Ollama**
