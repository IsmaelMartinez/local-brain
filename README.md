# Local Brain

Chat with local Ollama models that can explore your codebase.

```bash
local-brain "What files changed recently?"
local-brain "Review the code in src/"
local-brain "Generate a commit message"
local-brain "Explain how auth works"
```

## Install

```bash
uv pip install local-brain
```

Or with pipx:
```bash
pipx install local-brain
```

**Requires:** [Ollama](https://ollama.ai) with a model:
```bash
ollama pull qwen3
```

## Usage

```bash
local-brain "prompt"                    # Ask anything (auto-selects best model)
local-brain -v "prompt"                 # Verbose (show tool calls)
local-brain -m qwen2.5-coder:7b "prompt"  # Specific model
local-brain --list-models               # Show available models
local-brain --root /path/to/project "prompt"  # Set project root
```

The model has tools to explore your codebase — it reads files, checks git, lists directories on its own.

## Model Discovery

Local Brain automatically detects installed Ollama models and picks the best one:

```bash
local-brain --list-models
```

**Recommended models:**
- `qwen3:latest` — General purpose (default)
- `qwen2.5-coder:7b` — Code-focused
- `llama3.2:3b` — Fast, lightweight
- `mistral:7b` — Balanced

## Examples

```bash
# Explore
local-brain "What's in this repo?"
local-brain "How does the auth system work?"

# Review
local-brain "Review the git changes"
local-brain "Review src/main.py for issues"

# Git
local-brain "Generate a commit message for staged changes"
local-brain "Summarize recent commits"

# Explain
local-brain "Explain how agent.py works"
```

## Security

All operations are **restricted to the project root** (path jailing):

- ✅ Read files within project directory
- ✅ Run safe, read-only shell commands
- ❌ Access files outside project root
- ❌ Read sensitive files (`.env`, keys)
- ❌ Network access

## Tools

The model can use (all read-only):

| Tool | What it does |
|------|--------------|
| `read_file` | Read file contents |
| `list_directory` | List files (glob patterns) |
| `file_info` | Get file metadata |
| `git_diff` | See code changes |
| `git_status` | Check repo status |
| `run_command` | Run safe shell commands |

## Development

```bash
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain
uv sync
uv run local-brain "Hello!"
```

## License

MIT
