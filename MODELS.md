# Model Selection

## Quick Start

**New?** Start with `qwen2.5-coder:3b` - good balance of speed and quality.

```bash
ollama pull qwen2.5-coder:3b
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain --model qwen2.5-coder:3b
```

**Choose by need**:
- Fast feedback (2s) → `llama3.2:1b`
- Balanced (5s) → `qwen2.5-coder:3b`
- Thorough (20s) → `deepseek-coder-v2:16b`
- Low RAM (1.5GB) → `llama3.2:1b`

## Available Models

| Model | Size | RAM | Speed | Use Case |
|-------|------|-----|-------|----------|
| llama3.2:1b | 1.3GB | 1.5GB | 2s | Quick checks, CI/CD |
| qwen2.5-coder:3b | 1.9GB | 2.0GB | 5s | Daily code reviews |
| deepseek-coder-v2:16b | 8.9GB | 9.2GB | 20s | Security, production |

### llama3.2:1b
Fast summaries and triage. Use for rapid iteration and pre-commit hooks.

```bash
./target/release/local-brain --model llama3.2:1b
```

### qwen2.5-coder:3b (Recommended)
Best balance of speed and code understanding. Good for daily development.

```bash
./target/release/local-brain --model qwen2.5-coder:3b
```

### deepseek-coder-v2:16b (Default)
Thorough analysis with architectural insights. Use for security audits and production code.

```bash
./target/release/local-brain  # Uses default
```

## Task-Based Selection

Let local-brain choose the model for you:

```bash
./target/release/local-brain --task quick-review    # → qwen2.5-coder:3b
./target/release/local-brain --task security        # → deepseek-coder-v2:16b
./target/release/local-brain --task summarize       # → llama3.2:1b
```

**Available tasks**:
- `quick-review`, `syntax-check` → qwen2.5-coder:3b
- `summarize`, `triage` → llama3.2:1b
- `security`, `architecture` → deepseek-coder-v2:16b

See `models.json` for all task mappings.

## Selection Priority

Local-brain selects models in this order:

1. CLI `--model` flag (highest priority)
2. JSON `ollama_model` field
3. CLI `--task` flag
4. Default model (deepseek-coder-v2:16b)

Examples:

```bash
# CLI model wins
./target/release/local-brain --model llama3.2:1b --task security
# → Uses llama3.2:1b (not deepseek)

# Task flag when no model specified
./target/release/local-brain --task quick-review
# → Uses qwen2.5-coder:3b

# JSON override
echo '{"file_path":"test.rs","ollama_model":"phi3:mini"}' | ./target/release/local-brain
# → Uses phi3:mini
```

## Workflows

**Development loop**:
1. Quick checks → `llama3.2:1b`
2. Code review → `qwen2.5-coder:3b`
3. Pre-merge → `deepseek-coder-v2:16b`

**Team review**:
1. Triage PRs → `llama3.2:1b`
2. Standard review → `qwen2.5-coder:3b`
3. Critical paths → `deepseek-coder-v2:16b`

## Troubleshooting

**Model not found**: `ollama pull qwen2.5-coder:3b`

**Too slow**: Use `--model llama3.2:1b`

**Low quality**: Use `--model deepseek-coder-v2:16b`

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more issues.
