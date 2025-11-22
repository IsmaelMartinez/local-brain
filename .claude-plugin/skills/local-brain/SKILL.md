# Local Brain - Code Review Skill

Use this skill when the user wants to perform structured code reviews using local LLM models via Ollama.

## When to Use

- User asks to review code for issues, smells, or improvements
- User wants to analyze code quality
- User asks for refactoring suggestions
- User wants to identify potential bugs or security issues

## Prerequisites

- **Ollama** must be running locally with at least one model
- **local-brain** binary must be installed

### Installation

```bash
# Via cargo-binstall (recommended)
cargo binstall local-brain

# Or from source
cargo install --git https://github.com/IsmaelMartinez/local-brain
```

## Usage

### Review a Single File

```bash
echo '{"file_path": "/absolute/path/to/file.rs"}' | local-brain
```

### Review Multiple Files

```bash
local-brain --files src/main.rs,src/lib.rs
```

### Review Directory

```bash
local-brain --dir src --pattern "*.rs"
```

### Review Git Changes

```bash
local-brain --git-diff
```

### Specify Task Type

```bash
local-brain --task quick-review --files src/main.rs
local-brain --task security --files src/auth.rs
local-brain --task thorough-review --dir src --pattern "*.rs"
```

Available tasks: `quick-review`, `thorough-review`, `security`, `documentation`, `architecture`, `refactoring`

### Override Model

```bash
local-brain --model deepseek-coder-v2:16b --files src/main.rs
```

### Dry Run (Test Without Ollama)

```bash
local-brain --dry-run --files src/main.rs
```

## Output Format

Returns JSON with structured findings:

```json
{
  "spikes": [
    {
      "title": "Potential null pointer",
      "summary": "The function doesn't check if input is null before dereferencing",
      "lines": "45-48"
    }
  ],
  "simplifications": [
    {
      "title": "Extract duplicate logic",
      "summary": "Lines 100-120 and 200-220 contain similar validation logic"
    }
  ],
  "defer_for_later": [
    {
      "title": "Consider caching",
      "summary": "This function is called frequently and could benefit from memoization"
    }
  ],
  "other_observations": [
    "Overall code quality is good",
    "Consider adding more inline comments for complex sections"
  ]
}
```

## Examples

### Quick Code Review

```bash
# Review current file for issues
local-brain --task quick-review --files src/main.rs | jq .
```

### Security Audit

```bash
# Review auth code for security issues
local-brain --task security --dir src/auth --pattern "*.rs" | jq .
```

### Review Staged Changes

```bash
# Review what's about to be committed
local-brain --git-diff --task quick-review | jq .
```

### Format Output

```bash
# Pretty print results
local-brain --files src/main.rs | jq '.spikes[] | "\(.title): \(.summary)"'
```

## Environment Variables

- `OLLAMA_HOST` - Ollama server URL (default: `http://localhost:11434`)
- `MODEL_NAME` - Default model to use

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

Pull the model: `ollama pull deepseek-coder-v2:16b`

### No Output

Ensure Ollama has enough RAM for the model. Check `ollama ps` for running models.
