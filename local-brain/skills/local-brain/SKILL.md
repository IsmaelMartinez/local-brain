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
- `pipx install local-brain`
- `ollama pull qwen3`

## Tools

The model can: read files, list directories, check git status/diff/log, run safe shell commands.
