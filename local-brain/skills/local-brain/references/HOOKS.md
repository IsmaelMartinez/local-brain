# Local AI Hooks

Lightweight shell functions for quick AI operations. Defined in `~/.zshrc`.

## Available Hooks

### ai - General Q&A

Quick question answering using local Ollama model.

**Usage:**
```bash
ai "your question here"
```

**Example:**
```bash
ai "what does the grep -r flag do?"
ai "explain rust lifetimes briefly"
```

**When to use:**
- Quick factual questions
- Brief explanations
- Single-concept clarifications

### ai-cmd - Command Generation

Generate shell commands from natural language task descriptions.

**Usage:**
```bash
ai-cmd "what you want to do"
```

**Example:**
```bash
ai-cmd "find all rust files modified in the last week"
ai-cmd "count lines in all python files"
```

**Output:** Shell commands only, no commentary

**When to use:**
- Need shell command for a specific task
- Don't remember exact syntax
- Want safe command suggestions

### ai-explain - Command Explanation

Explain the last command executed and its output.

**Usage:**
```bash
ai-explain
```

**Context:** Automatically captures:
- Last command executed (`fc -ln -1`)
- Recent terminal output (last 100 lines if in tmux)

**When to use:**
- Command produced unexpected output
- Need to understand what went wrong
- Want suggestions for fixing/improving command

## Default Model

All hooks use: `deepseek-coder-v2:16b` (configurable via `OLLAMA_MODEL` env var)

## Decision Matrix: Hooks vs local-brain Binary

| Scenario | Tool | Reason |
|----------|------|--------|
| Quick question | `ai` hook | Fastest, no file reading |
| Generate command | `ai-cmd` hook | Direct shell output |
| Explain last command | `ai-explain` hook | Auto-captures context |
| Review single file | `local-brain` binary | Structured output |
| Review multiple files | `local-brain` binary | Handles multiple files |
| Review directory | `local-brain` binary | Directory traversal |
| Git diff review | `local-brain` binary | Git integration |
