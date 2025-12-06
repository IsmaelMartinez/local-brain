# Local Brain

[![CI](https://github.com/IsmaelMartinez/local-brain/actions/workflows/ci.yml/badge.svg)](https://github.com/IsmaelMartinez/local-brain/actions/workflows/ci.yml)

**Skill-based LLM tasks using local Ollama models with automatic tool calling.**

The model decides what to do — read files, check git, explore directories — you just describe what you need.

## What It Does

```bash
# Chat with tools - model decides what to read
local-brain chat "What files changed and why?"

# Code review - model explores the codebase itself
local-brain review                    # Review git changes
local-brain review src/main.py        # Review specific file  
local-brain review local_brain/       # Review directory

# Generate commit messages from staged changes
local-brain commit

# Run any skill
local-brain run explain "How does the agent loop work?"
local-brain run summarize "Summarize this project"
```

## Quick Start

### Install with pip/pipx

```bash
# Recommended: isolated install
pipx install local-brain

# Or with pip
pip install local-brain
```

### Install with uv (development)

```bash
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain
uv sync
uv run local-brain chat "Hello!"
```

### Prerequisites

- **Ollama** running locally: https://ollama.ai
- A model that supports tool calling:
  ```bash
  ollama pull qwen3        # Recommended
  ollama pull llama3.2     # Alternative
  ```

## Built-in Skills

| Skill | Command | What it does |
|-------|---------|--------------|
| **chat** | `local-brain chat "..."` | General assistant with all tools |
| **code-review** | `local-brain review` | Structured code review (Issues/Simplifications/Consider Later) |
| **explain** | `local-brain run explain "..."` | Technical explanations |
| **commit-message** | `local-brain commit` | Generate Conventional Commits message |
| **summarize** | `local-brain run summarize "..."` | Summarize files/projects |

## How It Works

Instead of manually specifying files, the **model uses tools** to explore:

```bash
$ local-brain chat -v "What Python files are in local_brain?"

🤖 Using model: qwen3:latest
🔧 Tools: ['read_file', 'list_directory', 'git_diff', ...]

📍 Turn 1
   📞 Tool calls: 1
      → list_directory(path='local_brain', pattern='*.py')
        ← local_brain/__init__.py, local_brain/agent.py, ...

📍 Turn 2
   ✅ Final response
The Python files in local_brain are: __init__.py, agent.py, cli.py, skill_loader.py
```

### Available Tools

| Tool | Description |
|------|-------------|
| `read_file` | Read file contents |
| `list_directory` | List files with glob patterns |
| `write_file` | Write to files |
| `file_info` | Get file metadata |
| `git_diff` | Get git diff (staged or all) |
| `git_changed_files` | List changed files |
| `git_status` | Get git status |
| `git_log` | Get commit history |
| `run_command` | Run safe shell commands |

## Examples

### Code Review

```bash
# Review git changes
local-brain review

# Review with verbose output (shows tool calls)
local-brain review -v

# Review specific file
local-brain review src/main.py
```

Output:
```markdown
## Issues Found
- **Hardcoded path**: Line 42 uses hardcoded `/tmp/` path

## Simplifications  
- **List comprehension**: Lines 15-18 can be simplified

## Consider Later
- **Add caching**: The API call on line 30 could benefit from caching

## Other Observations
- Good docstrings throughout
```

### Generate Commit Message

```bash
# Stage your changes
git add .

# Generate message
local-brain commit
```

Output:
```
feat(agent): add retry logic for failed tool calls

Implement exponential backoff when tool execution fails,
with configurable max retries and timeout settings.
```

### Custom Skills

Create `skills/my-skill/skill.yaml`:

```yaml
name: my-skill
description: My custom skill
model_preference: qwen3:latest

system_prompt: |
  You are a helpful assistant specialized in...

user_prompt_template: |
  {{ input }}

tools:
  - read_file
  - list_directory
```

Then run:
```bash
local-brain run my-skill "Do the thing"
```

## Why Local Brain?

| Feature | Benefit |
|---------|---------|
| **Tool Calling** | Model explores codebase itself |
| **Local** | No API costs, works offline |
| **Private** | Code never leaves your machine |
| **Fast** | 10-30 second responses |
| **Extensible** | Add skills via YAML files |

## Architecture

```
local_brain/
├── cli.py           # Click CLI
├── agent.py         # Tool calling conversation loop
├── skill_loader.py  # YAML skill loading + Jinja2
└── tools/           # Built-in tools (file, git, shell)
```

The agent loop:
1. Send user prompt with system prompt from skill
2. If model requests tools → execute them
3. Continue conversation until final response

## Contributing

```bash
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain
uv sync
uv run pytest
uv run local-brain chat "Hello!"
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Legacy Rust Version

The original Rust implementation is in `src/main.rs`. The Python version with tool calling is the recommended approach going forward.

## License

MIT License - see [LICENSE](LICENSE)

## Links

- **GitHub**: https://github.com/IsmaelMartinez/local-brain
- **Issues**: https://github.com/IsmaelMartinez/local-brain/issues
- **Ollama**: https://ollama.ai
