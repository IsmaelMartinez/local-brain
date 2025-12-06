# CLAUDE.md

Guidance for Claude Code when working with the local-brain codebase.

## Project Overview

Local Brain is a Python CLI tool for skill-based LLM tasks using local Ollama models with automatic tool calling. The model uses tools (read_file, git_diff, etc.) to explore the codebase itself.

**Key design:** Skills define what to do (prompts, tools), the agent loop handles how (Ollama integration, tool execution).

## Package Structure

```
local_brain/
├── __init__.py          # Package version
├── cli.py               # Click CLI commands
├── agent.py             # Core agent loop with tool calling
├── skill_loader.py      # YAML skill loading + Jinja2 templates
└── tools/
    ├── __init__.py      # Tool registry
    ├── file_tools.py    # read_file, list_directory, write_file
    ├── git_tools.py     # git_diff, git_changed_files, git_status
    └── shell_tools.py   # run_command (with safety restrictions)
```

## When USING Local Brain

For using the tool for tasks:

**Skill Usage** → See [local-brain/skills/local-brain/SKILL.md](local-brain/skills/local-brain/SKILL.md)

### Common Commands

```bash
# Chat - model decides what to do
local-brain chat "What files changed?"

# Code review
local-brain review                    # Review git changes
local-brain review src/main.py        # Review specific file
local-brain review local_brain/       # Review directory

# Generate commit message
local-brain commit

# Run skills
local-brain run explain "How does the agent loop work?"
local-brain run summarize "Summarize this project"

# Verbose mode (shows tool calls)
local-brain review -v
```

## When Working WITH Code (Development)

### Setup

```bash
# Clone and install
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain
uv sync

# Run
uv run local-brain chat "Hello!"

# Test
uv run pytest
```

### Key Files to Know

| File | Purpose |
|------|---------|
| `local_brain/cli.py` | CLI commands (chat, review, commit, run) |
| `local_brain/agent.py` | Agent loop - tool calling conversation |
| `local_brain/skill_loader.py` | Load skills from YAML, render Jinja2 templates |
| `local_brain/tools/*.py` | Built-in tools (file, git, shell) |

### Adding a New Tool

1. Create function in appropriate `tools/*.py` file
2. Add type hints and docstring (ollama uses these for schema)
3. Register in `tools/__init__.py` TOOL_REGISTRY
4. Add to relevant skills in `skill_loader.py` BUILTIN_SKILLS

Example:
```python
# tools/file_tools.py
def my_tool(path: str, option: bool = False) -> str:
    """Description of what the tool does.
    
    Args:
        path: Path to operate on
        option: Optional flag
        
    Returns:
        Result string
    """
    # Implementation
    return result
```

### Adding a New Skill

Add to `BUILTIN_SKILLS` in `skill_loader.py`:

```python
"my-skill": Skill({
    "name": "my-skill",
    "description": "What this skill does",
    "system_prompt": """Instructions for the model...""",
    "user_prompt_template": "{{ input }}",
    "tools": ["read_file", "list_directory"],  # Available tools
}),
```

Or create a YAML file in `local_brain/skills/my-skill/skill.yaml`.

### Running Tests

```bash
uv run pytest                    # All tests
uv run pytest -v                 # Verbose
uv run local-brain chat "test"   # Manual test
```

### Code Style

```bash
uv run ruff check .              # Lint
uv run ruff format .             # Format
uv run mypy local_brain/         # Type check
```

## Built-in Skills

| Skill | Tools | Purpose |
|-------|-------|---------|
| `chat` | all | General assistant, model decides what tools to use |
| `code-review` | file + git | Structured review (Issues/Simplifications/Consider/Observations) |
| `explain` | file | Technical explanations |
| `commit-message` | git | Generate Conventional Commits message |
| `summarize` | file + git | Summarize files/projects |

## Available Tools

| Tool | Description |
|------|-------------|
| `read_file` | Read file contents |
| `list_directory` | List files with glob patterns |
| `write_file` | Write to files |
| `file_info` | Get file metadata |
| `git_diff` | Get git diff |
| `git_changed_files` | List changed files |
| `git_status` | Get git status |
| `git_log` | Get commit history |
| `run_command` | Run safe shell commands |

## Agent Loop

The core loop in `agent.py`:

1. Send user prompt with system prompt from skill
2. If model requests tool calls → execute them
3. Add tool results to conversation
4. Repeat until model gives final response (no tool calls)

## External Requirements

- Ollama running locally (http://localhost:11434)
- Model that supports tool calling: `qwen3:latest` or `llama3.2:latest`

## Quick Reference

| Task | Command |
|------|---------|
| Install | `uv sync` |
| Run | `uv run local-brain chat "..."` |
| Test | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Review | `local-brain review` |
| Commit msg | `local-brain commit` |

---

**For tool usage:** See [local-brain/skills/local-brain/SKILL.md](local-brain/skills/local-brain/SKILL.md)
