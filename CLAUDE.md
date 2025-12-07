# CLAUDE.md

Guidance for Claude Code when working with local-brain.

## What It Is

A Python CLI that chats with local Ollama models. The model has tools (read_file, git_diff, etc.) to explore the codebase itself.

## Structure

```
local_brain/
├── __init__.py    # Version
├── cli.py         # Click CLI (single command with flags)
├── agent.py       # Ollama chat loop with tool execution
└── tools/         # Tool functions (file, git, shell)
```

## Commands

```bash
local-brain "prompt"        # Chat with tools
local-brain --review        # Code review mode
local-brain --commit        # Generate commit message
local-brain -v "prompt"     # Verbose (show tool calls)
```

## Key Files

- `cli.py`: Entry point, defines system prompts for different modes
- `agent.py`: `run_agent()` - the conversation loop that executes tool calls
- `tools/__init__.py`: Registry of all tools (read_file, git_diff, etc.)

## Development

```bash
uv sync
uv run local-brain "Hello"
uv run pytest
```
