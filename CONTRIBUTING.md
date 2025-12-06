# Contributing to Local Brain

Thank you for your interest in contributing! This guide covers development setup and contribution guidelines.

## Development Setup

### Prerequisites

- Python 3.10+
- uv (recommended) or pip
- Ollama with a tool-calling model (`ollama pull qwen3`)
- Git

### Clone and Install

```bash
# Clone repository
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"

# Verify installation
uv run local-brain --version
uv run local-brain chat "Hello!"
```

## Architecture Overview

### Package Structure

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

### Data Flow

1. **User input**: Command via CLI
2. **Skill loading**: Load system prompt and tools from skill definition
3. **Agent loop**: 
   - Send message to Ollama
   - If model requests tools → execute them
   - Add tool results to conversation
   - Repeat until final response
4. **Output**: Print model's final response

### Key Components

- **`agent.py`**: The core loop that handles multi-turn conversations with tool calling
- **`skill_loader.py`**: Built-in skills (chat, code-review, etc.) and YAML loading
- **`tools/`**: Functions the model can call (file ops, git, shell)

## Making Changes

### Adding a New Tool

1. Add function to appropriate file in `tools/`:

```python
# tools/file_tools.py
def my_new_tool(path: str, option: bool = False) -> str:
    """Description of what this tool does.
    
    Args:
        path: Path to operate on
        option: Optional flag for behavior
        
    Returns:
        Result as a string
    """
    # Implementation
    return "result"
```

2. Register in `tools/__init__.py`:

```python
from .file_tools import my_new_tool

TOOL_REGISTRY = {
    # ... existing tools
    "my_new_tool": my_new_tool,
}
```

3. Add to relevant skills in `skill_loader.py`:

```python
"my-skill": Skill({
    "tools": ["read_file", "my_new_tool"],
    # ...
}),
```

### Adding a New Skill

Add to `BUILTIN_SKILLS` in `skill_loader.py`:

```python
"my-skill": Skill({
    "name": "my-skill",
    "description": "What this skill does",
    "system_prompt": """Instructions for the model...""",
    "user_prompt_template": "{{ input }}",
    "tools": ["read_file", "list_directory"],
}),
```

Or create `local_brain/skills/my-skill/skill.yaml`:

```yaml
name: my-skill
description: What this skill does
system_prompt: |
  Instructions for the model...
user_prompt_template: "{{ input }}"
tools:
  - read_file
  - list_directory
```

### Adding a CLI Command

Add to `cli.py`:

```python
@cli.command()
@click.argument("target")
@click.option("--model", "-m", help="Model to use")
@click.option("--verbose", "-v", is_flag=True)
def mycommand(target: str, model: str | None, verbose: bool):
    """Description of command."""
    skill = get_skill("my-skill")
    result = run_agent(skill, user_input=target, model=model, verbose=verbose)
    click.echo(result)
```

## Testing

```bash
# Run tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Manual testing
uv run local-brain chat "What files are here?"
uv run local-brain review -v
uv run local-brain commit -v
```

## Code Style

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type check
uv run mypy local_brain/
```

### Style Guidelines

- Use type hints for all function parameters and returns
- Add docstrings with Args and Returns sections
- Keep functions focused and under 50 lines when possible
- Use meaningful variable names

## Pull Request Process

### Before Submitting

1. **Test your changes**:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run ruff format .
   ```

2. **Update documentation** if needed (README.md, docstrings)

3. **Write clear commit messages**:
   ```
   feat(tools): add file_exists tool
   
   - Add file_exists function to file_tools.py
   - Register in tool registry
   - Add to chat skill
   ```

### Submitting

1. Fork repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes and commit
4. Push to your fork: `git push origin feature/your-feature`
5. Open PR against `main` branch

### PR Checklist

- [ ] Tests pass (`uv run pytest`)
- [ ] Code formatted (`uv run ruff format .`)
- [ ] No lint errors (`uv run ruff check .`)
- [ ] Documentation updated if needed
- [ ] Commit messages are clear

## Getting Help

- **Questions**: Open a [GitHub Discussion](https://github.com/IsmaelMartinez/local-brain/discussions)
- **Bugs**: Open a [GitHub Issue](https://github.com/IsmaelMartinez/local-brain/issues)
- **Features**: Open a [GitHub Issue](https://github.com/IsmaelMartinez/local-brain/issues) with "Feature Request" label

## Areas for Contribution

**High Priority**:
- More built-in tools
- Better error handling
- Test coverage

**Good First Issues**:
- Add more skills
- Improve tool docstrings
- Documentation improvements

**Experimental**:
- Streaming output support
- Async tool execution
- Custom skill directories

Thank you for contributing! 🎉
