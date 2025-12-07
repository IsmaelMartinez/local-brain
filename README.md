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
pipx install local-brain
```

**Requires:** [Ollama](https://ollama.ai) with a model:
```bash
ollama pull qwen3
```

## Usage

```bash
local-brain "prompt"              # Ask anything
local-brain -v "prompt"           # Verbose (show tool calls)
local-brain -m llama3.2 "prompt"  # Different model
```

The model has tools to explore your codebase — it reads files, checks git, lists directories on its own.

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

## Tools

The model can use:

| Tool | What it does |
|------|--------------|
| `read_file` | Read file contents |
| `list_directory` | List files (glob patterns) |
| `git_diff` | See code changes |
| `git_status` | Check repo status |
| `run_command` | Run shell commands |

## Development

```bash
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain
uv sync
uv run local-brain "Hello!"
```

## License

MIT
