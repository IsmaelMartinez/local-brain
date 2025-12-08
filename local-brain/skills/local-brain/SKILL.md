---
name: local-brain
description: Chat with local Ollama models that can explore your codebase using tools.
---

# Local Brain

Chat with local Ollama models that have tools to explore your codebase.

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

## Prerequisites

- Ollama running locally
- `uv pip install local-brain` (or `pipx install local-brain`)
- `ollama pull qwen3` (or any other model)

## Available Tools

The model assumes these tools are available and uses them directly:

- `read_file(path)` - Read file contents
- `list_directory(path, pattern)` - List files with glob patterns
- `file_info(path)` - Get file metadata (size, modified time)
- `git_diff(staged, file_path)` - Show code changes
- `git_status()` - Check repo status
- `git_changed_files(staged, include_untracked)` - List changed files
- `git_log(count, oneline)` - View commit history
- `run_command(command)` - Run safe read-only shell commands

All tools return human-readable output or error messages on failure.
