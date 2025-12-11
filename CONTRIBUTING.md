# Contributing

## Setup

```bash
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain
uv sync
```

**Note:** Requires Python 3.10-3.13 (grpcio build issue with 3.14).

## Development

```bash
# Run locally
uv run local-brain "Hello"

# Test
uv run pytest

# Lint
uv run ruff check local_brain/
```

## Architecture

Local Brain uses [Smolagents](https://github.com/huggingface/smolagents) for code execution:

```
local_brain/
├── __init__.py      # Version
├── cli.py           # Click CLI
├── models.py        # Model discovery & selection
├── security.py      # Path jailing
└── smolagent.py     # CodeAgent + tools
```

## Adding Tools

Tools are defined in `local_brain/smolagent.py` using the `@tool` decorator:

```python
from smolagents import tool

@tool
def my_tool(arg: str) -> str:
    """One-line description.
    
    Args:
        arg: Description of arg
        
    Returns:
        What it returns
    """
    return result
```

Then add to the `ALL_TOOLS` list in the same file:

```python
ALL_TOOLS = [
    read_file,
    list_directory,
    # ...
    my_tool,  # Add your tool here
]
```

### Tool Guidelines

- Use the `@tool` decorator from smolagents
- Include a docstring with Args and Returns sections
- Use `safe_path()` from security.py for file operations (path jailing)
- Return strings for tool output
- Handle errors gracefully (return error message, don't raise)

## Versioning

Version is stored in `local_brain/__init__.py` as the single source of truth.

When bumping the version:

1. Update `__version__` in `local_brain/__init__.py`
2. Run `python3 scripts/sync_version.py` to sync to all plugin.json files

The sync script updates:
- `local-brain/plugin.json` (Claude Code plugin)
- `local-brain/.claude-plugin/plugin.json` (marketplace)

## Pull Requests

1. Fork & branch
2. Make changes
3. Run tests: `uv run pytest`
4. Run linter: `uv run ruff check local_brain/`
5. Submit PR
