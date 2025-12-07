---
name: local-brain
description: Chat with local Ollama models that can explore your codebase. The model uses tools (read_file, git_diff, list_directory) to answer questions. Use for code reviews, commit messages, or any codebase questions.
---

# Local Brain

Chat with local Ollama models that have tools to explore your codebase.

## Commands

```bash
local-brain "What changed recently?"     # Chat - model explores with tools
local-brain --review                      # Code review (git changes)
local-brain --review src/main.py          # Code review (specific file)
local-brain --commit                      # Generate commit message
local-brain -v "prompt"                   # Verbose (show tool calls)
```

## Prerequisites

- **Ollama** running locally
- **local-brain** installed: `pipx install local-brain`
- A model: `ollama pull qwen3`

## Examples

### Review Code

```bash
local-brain --review                 # Review git changes
local-brain --review src/utils.py    # Review specific file
local-brain --review -v              # Show tool calls
```

### Generate Commit Message

```bash
git add .
local-brain --commit
```

### Ask Questions

```bash
local-brain "What does this repo do?"
local-brain "How does auth work?"
local-brain "Find all TODO comments"
```

## Available Tools

| Tool | What it does |
|------|--------------|
| `read_file` | Read file contents |
| `list_directory` | List files (glob patterns) |
| `git_diff` | See code changes |
| `git_status` | Check repo status |
| `run_command` | Run safe shell commands |

## Model Selection

Default: `qwen3:latest`

```bash
local-brain -m llama3.2 "prompt"
```

## When to Use

- Quick codebase questions
- Code reviews
- Commit message generation
- File/directory exploration

## When NOT to Use

- Complex multi-step reasoning
- Security-critical analysis
- Tasks needing external APIs
