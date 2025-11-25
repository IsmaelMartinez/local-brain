# Local AI Hooks

Lightweight shell functions for quick AI operations. Defined in `~/.zshrc`.

## Available Hooks

### ai - Concise Q&A

Quick, concise question answering using local Ollama model.

**Usage:**
```bash
ai "your question here"
```

**Example:**
```bash
ai "what does the grep -r flag do?"
ai "what is a closure in rust?"
```

**Output:** Concise, direct answers without lengthy explanations

**When to use:**
- Quick factual questions
- Need brief, to-the-point answers
- Want to minimize token usage

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

### ai-explain - Detailed Explanation

Explain the last command, or provide detailed explanation of a given string.

**Usage:**
```bash
# Explain last command and recent output
ai-explain

# Explain a specific string (code, concept, etc)
ai-explain "string to explain"
```

**Example:**
```bash
# Explain last command
ai-explain

# Explain a code pattern
ai-explain "async/await in Rust"

# Explain an error message
ai-explain "connection refused on port 8080"
```

**Output:** Detailed technical explanation with context, implications, and solutions

**When to use:**
- Understand what last command did or what went wrong
- Need detailed explanation of a concept or error
- Want suggestions for fixing/improving

## Default Model

All hooks use: `deepseek-coder-v2-8k` (configurable via `OLLAMA_MODEL` env var)

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
