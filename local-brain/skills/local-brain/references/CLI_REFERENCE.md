# Local Brain CLI Reference

## Installation

```bash
# Via cargo-binstall (recommended)
cargo binstall local-brain

# Or from source
cargo install --git https://github.com/IsmaelMartinez/local-brain
```

## Command Line Flags

### Input Modes

- `--files <FILES>` - Comma-separated list of files to review
- `--git-diff` - Review all changed files in git working directory
- `--dir <DIR> --pattern <PATTERN>` - Review files in directory matching glob pattern

### Optional Flags

- `--task <TASK>` - Task-based model selection: quick-review, thorough-review, security, documentation, architecture, refactoring
- `--model <MODEL>` - Override default model (e.g., qwen2.5-coder:3b)
- `--kind <KIND>` - Document type: code, design-doc, ticket, other
- `--review-focus <FOCUS>` - Review focus: refactoring, readability, performance, risk, general
- `--dry-run` - Test without calling Ollama (validate inputs only)

## Environment Variables

- `OLLAMA_HOST` - Ollama server URL (default: `http://localhost:11434`)
- `MODEL_NAME` - Default model to use

## Output Format

Structured Markdown with sections:
- **Issues Found** - Problems requiring attention (with line numbers)
- **Simplifications** - Opportunities to reduce complexity
- **Consider Later** - Non-critical improvements
- **Other Observations** - General notes

## Troubleshooting

### Ollama Not Running
```
Error: Failed to send request to Ollama
```
Start Ollama: `ollama serve`

### Model Not Found
```
Error: model 'xyz' not found
```
Pull a model: `ollama pull qwen2.5-coder:3b`

### No Output
Ensure Ollama has enough RAM for the model. Check `ollama ps` for running models.
