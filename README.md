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
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama endpoint |
| `MODEL_NAME` | From `models.json` | Fallback model (deprecated, use CLI flags) |

### Model Selection

Local Brain supports multiple Ollama models with automatic selection based on task type. Model selection priority:

1. **CLI `--model` flag** (highest priority)
2. **JSON `ollama_model` field**
3. **CLI `--task` flag** (maps to model via `models.json`)
4. **Default model** from `models.json`

#### Usage Examples

```bash
# Explicit model selection
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain --model qwen2.5-coder:3b

# Task-based automatic selection
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain --task quick-review

# JSON override (highest priority after --model)
echo '{"file_path":"src/main.rs","ollama_model":"phi3:mini"}' | ./target/release/local-brain

# Default model (from models.json)
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain
```

#### Available Tasks

| Task | Recommended Model | Use Case |
|------|------------------|----------|
| `quick-review` | `qwen2.5-coder:3b` | Fast code checks, syntax analysis |
| `syntax-check` | `qwen2.5-coder:3b` | Simple code smell detection |
| `summarize` | `llama3.2:1b` | Quick file summaries |
| `triage` | `llama3.2:1b` | Rapid codebase assessment |
| `documentation` | `phi3:mini` | Documentation quality review |
| `general-review` | `phi3:mini` | Balanced code review |
| `requirements` | `qwen2.5:3b` | Requirements analysis |
| `prioritization` | `qwen2.5:3b` | Task prioritization |
| `design-review` | `qwen2.5:3b` | Design document review |
| `thorough-review` | `deepseek-coder-v2:8k` | Deep code analysis (default) |
| `security` | `deepseek-coder-v2:8k` | Security-focused review |
| `architecture` | `deepseek-coder-v2:8k` | Architectural analysis |

**Model Registry**: See `models.json` for complete model specifications and RAM requirements.

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

## Performance

| File Size | Processing Time | Quality |
|-----------|----------------|---------|
| 100 lines | ~27s | Detailed insights |
| 300 lines | ~17s | Comprehensive |
| 800 lines | ~23s | Processed successfully |

**Recommended**: 100-500 lines for optimal results

## Claude Code Integration

A skill file is provided at `.claude/skills/local-brain/skill.md` for integration.

**Usage**:
```bash
echo '{"file_path": "/path/to/file"}' | ./target/release/local-brain | jq .
```

## Documentation

- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - Complete technical specification
- **[VALIDATION_EXPERIMENTS.md](VALIDATION_EXPERIMENTS.md)** - Pre-implementation testing
- **[VALIDATION_RESULTS.md](VALIDATION_RESULTS.md)** - Validation test results (100% pass rate)

## Development

```bash
cargo build          # Debug build
cargo test           # Run tests
cargo build --release # Optimized build
```

## Testing

### Integration Test

Verify code smell detection with the integration test:

```bash
./tests/integration_test.sh
```

**Test File**: `tests/fixtures/code_smells.js` contains 5 intentional code smells:
1. Deeply nested conditionals (validateUser)
2. God function - too many responsibilities (processOrder)
3. Magic numbers (calculateDiscount)
4. Duplicate code (getUserBy* functions)
5. Missing error handling (parseUserData)

**Expected Result**: Model should detect 6+ issues across spikes, simplifications, and defer_for_later

**Latest Run**: ✅ Detected 8 findings (2 spikes, 2 simplifications, 2 defer, 2 observations)

## Known Issues & Solutions

**Issue**: Model wraps JSON in markdown code fences despite explicit instructions
**Solution**: Implemented `extract_json_from_markdown()` function (src/main.rs:240-260)
**Status**: ✅ Resolved

**Limitation**: Model may hallucinate when reviewing pure documentation files
**Recommendation**: Best suited for code reviews, use with caution for text-only docs
**Status**: Known limitation

## License

MIT - see [LICENSE](LICENSE)
