---
name: local-brain
description: Chat with local Ollama models that can explore your codebase using tools.
---

# Local Brain

Chat with local Ollama models that have tools to explore your codebase.

## Installation

Install local-brain:
```bash
uv pip install local-brain
```

Or with pipx:
```bash
pipx install local-brain
```

**Requirements:**
- Ollama running locally (https://ollama.ai)
- A model pulled (e.g., `ollama pull qwen3`)

## Usage

```bash
local-brain "prompt"              # Ask anything
local-brain -v "prompt"           # Show tool calls
local-brain -m llama3.2 "prompt"  # Different model
```

## Examples

```bash
local-brain "What's in this repo?"
local-brain "Review the git changes"
local-brain "Generate a commit message"
local-brain "Explain how src/main.py works"
local-brain "Find all TODO comments"
```

## Available Tools

The model assumes these tools are available and uses them directly:

- `read_file(path)` - Read file contents at a given `path`.
- `list_directory(path, pattern)` - List files in `path` matching a glob `pattern` (e.g., `*.py`, `src/**/*.js`).
- `file_info(path)` - Get file metadata (size, modified time) for a given `path`.
- `git_diff(staged, file_path)` - Show code changes. Use `staged=True` for staged changes. Optionally provide a `file_path`.
- `git_status()` - Check repo status.
- `git_changed_files(staged, include_untracked)` - List changed files. Use `staged=True` for staged files, `include_untracked=True` to include untracked files.
- `git_log(count, oneline)` - View commit history. `count` specifies number of commits, `oneline=True` for compact view.
- `run_command(command)` - Run a safe, read-only shell `command`.

All tools return human-readable output or error messages on failure.
