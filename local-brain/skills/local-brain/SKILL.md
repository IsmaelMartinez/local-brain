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
local-brain "prompt"                    # Ask anything (auto-selects best model)
local-brain -v "prompt"                 # Show tool calls
local-brain -m qwen2.5-coder:7b "prompt"  # Specific model
local-brain --list-models               # Show available models
local-brain --root /path/to/project "prompt"  # Set project root
```

## Examples

```bash
local-brain "What's in this repo?"
local-brain "Review the git changes"
local-brain "Generate a commit message"
local-brain "Explain how src/main.py works"
local-brain "Find all TODO comments"
```

## Model Discovery

Local Brain automatically detects installed Ollama models and selects the best one for tool-calling tasks:

```bash
# See what models are available
local-brain --list-models
```

**Recommended models** (with excellent tool support):
- `qwen3:latest` - General purpose, default choice
- `qwen2.5-coder:7b` - Code-focused tasks
- `llama3.2:3b` - Fast, lightweight
- `mistral:7b` - Balanced performance

If no model is specified, Local Brain auto-selects the best installed model.

## Security

All file operations are **restricted to the project root** (path jailing):

- Files outside the project directory cannot be read
- Shell commands execute within the project root
- Sensitive files (`.env`, `.pem`, SSH keys) are blocked
- Only read-only shell commands are allowed

## Available Tools

The model assumes these tools are available and uses them directly:

- `read_file(path)` - Read file contents at a given `path`. Large files are truncated. **Restricted to project root.**
- `list_directory(path, pattern)` - List files in `path` matching a glob `pattern` (e.g., `*.py`, `src/**/*.js`). Excludes hidden files and common ignored directories. Returns up to 100 files.
- `file_info(path)` - Get file metadata (size, type, modified time) for a given `path`.
- `git_diff(staged, file_path)` - Show code changes. Use `staged=True` for staged changes. Optionally provide a `file_path`. Large diffs are truncated.
- `git_status()` - Check repo status.
- `git_changed_files(staged, include_untracked)` - List changed files. Use `staged=True` for staged files, `include_untracked=True` to include untracked files.
- `git_log(count, oneline)` - View commit history. `count` specifies number of commits (max 50), `oneline=True` for compact view.
- `run_command(command)` - Run a safe, read-only shell `command`. Only specific commands are allowed (e.g., `ls`, `cat`, `grep`). **Executes within project root.**

All tools return human-readable output or error messages on failure.
