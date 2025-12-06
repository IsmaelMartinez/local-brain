---
name: local-brain
description: Delegate code reviews, explanations, commit messages, and analysis tasks to local Ollama LLM models with automatic tool calling. The model uses tools (read_file, git_diff, list_directory) to explore the codebase itself. Use for code reviews, explanations, commit message generation, or any task that can be offloaded to a local model. Ideal for routine analysis that doesn't require cloud-scale reasoning.
---

# Local Brain - Tool-Calling LLM Tasks

Offload tasks to local Ollama models with automatic tool calling. The model reads files, checks git, and explores directories on its own.

## Quick Commands

```bash
# Chat - model decides what to do
local-brain chat "What changed in the last commit?"

# Code review - model explores using tools
local-brain review                    # Review git changes
local-brain review src/main.py        # Review specific file
local-brain review local_brain/       # Review directory

# Generate commit message
local-brain commit

# Explain code
local-brain run explain "How does the agent loop work?"

# Summarize
local-brain run summarize "Summarize this project"
```

## Prerequisites

- **Ollama** running locally with a tool-calling model
- **local-brain** Python package installed

Check prerequisites:
```bash
which local-brain && ollama ps
ollama list  # Ensure qwen3 or llama3.2 is available
```

Install:
```bash
pipx install local-brain
# or
pip install local-brain
```

## When to Use

| Task | Command |
|------|---------|
| Quick questions about codebase | `local-brain chat "What does X do?"` |
| Code review (git changes) | `local-brain review` |
| Code review (specific file) | `local-brain review path/to/file` |
| Code review (directory) | `local-brain review src/` |
| Generate commit message | `local-brain commit` |
| Explain code/concepts | `local-brain run explain "..."` |
| Summarize project | `local-brain run summarize "..."` |

## How It Works

The model has access to tools and uses them automatically:

```bash
$ local-brain review -v

🤖 Using model: qwen3:latest
🔧 Tools: ['read_file', 'list_directory', 'git_diff', 'git_changed_files']

📍 Turn 1
   📞 Tool calls: 2
      → git_changed_files(staged=False)
      → git_diff(staged=False)

📍 Turn 2
   ✅ Final response (structured review)
```

**Key insight:** You don't need to specify files - the model explores using tools!

## Available Tools

| Tool | Description |
|------|-------------|
| `read_file` | Read file contents |
| `list_directory` | List files with glob patterns |
| `write_file` | Write to files |
| `git_diff` | Get git diff |
| `git_changed_files` | List changed files |
| `git_status` | Get git status |
| `git_log` | Get commit history |
| `run_command` | Run safe shell commands |

## Built-in Skills

| Skill | Tools | Output |
|-------|-------|--------|
| `chat` | all | Free-form response |
| `code-review` | file + git | Structured Markdown (Issues/Simplifications/Consider Later) |
| `explain` | file | Technical explanation |
| `commit-message` | git | Conventional Commits format |
| `summarize` | file + git | Project summary |

## Output Format

### Code Review Output

```markdown
## Issues Found
- **Title**: Description (line numbers when relevant)

## Simplifications
- **Title**: How to simplify

## Consider Later
- **Title**: Non-urgent improvements

## Other Observations
- General notes
```

### Commit Message Output

```
feat(scope): subject line under 50 chars

Optional body explaining what and why.
```

## Usage Examples

### Review Changed Files

```bash
# Review all git changes
local-brain review

# With verbose output to see tool calls
local-brain review -v
```

### Review Specific Target

```bash
# Single file
local-brain review src/main.py

# Directory
local-brain review local_brain/

# Multiple items via chat
local-brain chat "Review main.py and test_main.py"
```

### Generate Commit Message

```bash
# Stage changes first
git add .

# Generate message
local-brain commit

# Output: feat(cli): add new review command...
```

### Custom Queries

```bash
# Ask anything - model uses tools as needed
local-brain chat "What's the project structure?"
local-brain chat "Find all TODO comments"
local-brain chat "How does error handling work in agent.py?"
```

## Verbose Mode

Add `-v` to see tool calls:

```bash
local-brain review -v
local-brain chat -v "What files are in src/?"
```

## Model Selection

Default model: `qwen3:latest` (good tool calling support)

Override with `--model`:
```bash
local-brain review --model llama3.2:latest
```

## When NOT to Use

- Complex multi-step reasoning requiring full codebase context
- Security-critical code analysis
- Tasks requiring external API access
- Very large files (>50KB truncated)

## References

- [README.md](../../../README.md) - Full documentation
- [Ollama](https://ollama.ai) - Local LLM runtime
