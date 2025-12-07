# Contributing

## Setup

```bash
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain
uv sync
```

## Development

```bash
# Run locally
uv run local-brain "Hello"

# Test
uv run pytest

# Lint
uv run ruff check local_brain/
```

## Adding Tools

Add to `local_brain/tools/`:

```python
def my_tool(arg: str) -> str:
    """One-line description.
    
    Args:
        arg: Description of arg
        
    Returns:
        What it returns
    """
    return result
```

Register in `local_brain/tools/__init__.py`:

```python
TOOL_REGISTRY = {
    ...
    "my_tool": my_tool,
}
```

## Pull Requests

1. Fork & branch
2. Make changes
3. Test locally
4. Submit PR
