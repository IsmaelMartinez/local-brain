# CLAUDE.md

## What It Is

CLI that chats with local Ollama models. The model has tools (read_file, git_diff, etc.) to explore the codebase.

## Structure

```
local_brain/
├── cli.py         # Click CLI - just: local-brain "prompt"
├── agent.py       # Ollama chat loop with tool execution
└── tools/         # Tool functions (file, git, shell)
```

## Development

```bash
uv sync
uv run local-brain "Hello"
```
