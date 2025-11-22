# Local Brain - Context Offloading Skill

Use this skill to delegate tasks to local Ollama LLM models, reducing context usage in the main agent. Ideal for routine analysis that doesn't need cloud-scale reasoning.

## When to Use

**Offload these tasks to local models:**
- Code reviews and quality analysis
- Design document summaries
- Ticket/issue triage and prioritization
- Documentation analysis
- Planning and task breakdown
- Routine pattern matching (TODOs, code smells)

**Keep in main agent:**
- Complex multi-step reasoning
- Tasks requiring broader codebase context
- Security-critical decisions

## Prerequisites

- **Ollama** running locally with at least one model
- **local-brain** binary installed

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

### Code Review

```bash
# Quick review for issues
local-brain --task quick-review --files src/main.rs | jq .

# Security audit
local-brain --task security --dir src/auth --pattern "*.rs" | jq .

# Review staged changes before commit
local-brain --git-diff --task quick-review | jq .
```

### Document Analysis

```bash
# Summarize design docs
local-brain --task summarize --files docs/architecture.md | jq .

# Analyze requirements
local-brain --task requirements --files specs/feature.md | jq .
```

### Planning & Triage

```bash
# Prioritize TODOs across codebase
local-brain --task prioritization --dir src --pattern "*.rs" | jq .

# Triage issues
local-brain --task triage --files issues/backlog.md | jq .
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
