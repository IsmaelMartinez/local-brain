---
name: local-brain
description: Chat with local Ollama models that can explore your codebase using tools.
version: 0.8.0
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
local-brain -d "prompt"                 # Show step-by-step debug output
local-brain -m qwen3-coder:30b "prompt" # Specific model
local-brain --trace "prompt"            # Enable OTEL tracing
local-brain --list-models               # Show available models
local-brain --root /path/to/project "prompt"  # Set project root
local-brain doctor                      # Check system health
```

## Health Check

Verify your setup is working correctly:

```bash
local-brain doctor
```

This checks:
- Ollama is installed and running
- Recommended models are available
- Tools execute correctly
- Optional tracing dependencies

Example output:
```
🔍 Local Brain Health Check

Checking Ollama...
  ✅ Ollama is installed (ollama version is 0.13.1)

Checking Ollama server...
  ✅ Ollama server is running (9 models)

Checking recommended models...
  ✅ Recommended models installed: qwen3:latest

Checking tools...
  ✅ Tools working (9 tools available)

Checking optional features...
  ✅ OTEL tracing available (--trace flag)

========================================
✅ All checks passed! Local Brain is ready.
```

## Examples

```bash
local-brain "What's in this repo?"
local-brain "Review the git changes"
local-brain "Generate a commit message"
local-brain "Explain how src/main.py works"
local-brain "Find all TODO comments"
local-brain "What functions are defined in utils.py?"
local-brain "Search for 'validate' in the auth module"
```

## Model Selection Guide

Choose the right model for your task:

### For Code Exploration (Recommended)

Use `qwen3-coder:30b` for fast, direct code exploration:

```bash
local-brain -m qwen3-coder:30b "List all files in src/lib/"
local-brain -m qwen3-coder:30b "Read the main configuration file"
local-brain -m qwen3-coder:30b "Find all TODO comments"
local-brain -m qwen3-coder:30b "What functions are in utils.py?"
```

Why: 2.5x faster than qwen3:30b (3-20s per step vs 120-260s), direct tool usage.

### For Complex Reasoning

Use `qwen3:30b` for tasks requiring deeper analysis:

```bash
local-brain -m qwen3:30b "Analyze the architecture of this codebase"
local-brain -m qwen3:30b "Review recent changes and suggest improvements"
local-brain -m qwen3:30b "Explain how authentication works end-to-end"
```

Why: More thorough reasoning, better at synthesis tasks.

### For Resource-Constrained Environments

Use `qwen2.5:3b` for fast, lightweight operation:

```bash
local-brain -m qwen2.5:3b "What files changed?"
local-brain -m qwen2.5:3b "Show git status"
```

Why: 60% smaller than qwen3, same quality for simple tasks.

### Tips for Better Results

When exploring nested directories, ask for recursive listing:
```bash
local-brain -m qwen3-coder:30b "List ALL files recursively with pattern **/*"
```

Use --debug to see what the model is doing:
```bash
local-brain -d -m qwen3-coder:30b "Find Python files"
```

**Avoid these models** (broken or unreliable tool calling):
- `qwen2.5-coder:*` - Outputs JSON instead of executing tools
- `llama3.2:1b` - Too small, hallucinates paths
- `deepseek-r1:*` - No tool support at architecture level

If no model is specified, Local Brain auto-selects the best installed model.

## Observability

### Debug Mode (--debug or -d)

See step-by-step progress with the `--debug` flag:

```bash
local-brain --debug "What files are here?"
```

This shows:
- Step number and duration
- Tool calls with arguments
- Result preview (truncated)
- Token usage per step

Example output:
```
[debug] Model: qwen3-coder:30b
[debug] Project root: /path/to/project

[Step 1] (4.2s)
  Tool: list_directory(path='.', pattern='**/*')
  Result:
    src/main.py
    src/utils.py
    ... (15 lines total)
  Tokens: 2634 in / 42 out
```

### OTEL Tracing (--trace)

Enable OpenTelemetry tracing to visualize agent execution with detailed timing and metrics:

```bash
local-brain --trace "Analyze the architecture"
```

This captures:
- Agent execution timeline (total duration)
- Individual steps (planning, execution, final answer)
- LLM calls with token counts
- Tool invocations with inputs/outputs
- Timing for each operation

#### Visualizing Traces with Jaeger (Recommended)

For real-time visualization of agent execution, use Jaeger:

**1. Start Jaeger (one-time setup):**
```bash
docker run -d \
  --name jaeger \
  -p 16686:16686 \
  -p 4318:4318 \
  jaegertracing/all-in-one
```

**2. Run local-brain with tracing:**
```bash
local-brain --trace -m qwen3-coder:30b "List all files in src/"
```

**3. View in Jaeger UI:**
Open http://localhost:16686 and select:
- Service: `local-brain`
- Operation: `CodeAgent.run`

You'll see a waterfall timeline showing:
```
CodeAgent.run (5.1s total)
├── Step 1 (2.04s)
│   ├── LiteLLMModel.generate (2.03s) ← LLM latency
│   └── list_directory (1.5ms) ← Tool execution
└── Step 2 (3.09s)
    ├── LiteLLMModel.generate (3.09s)
    └── FinalAnswerTool (0.1ms)
```

Click any span to see details: tokens used, arguments, outputs, errors.

#### Install Tracing Dependencies

For JSON console output only (no Jaeger):
```bash
pip install local-brain[tracing]
```

For Jaeger visualization, also install:
```bash
pip install opentelemetry-exporter-otlp
```

#### Combining Flags for Maximum Insight

Use all three flags together for complete visibility:
```bash
local-brain --trace --debug -m qwen3-coder:30b "Review the code"
```

This gives:
- `--trace` → OTEL spans in Jaeger (timing, tokens, architecture)
- `--debug` → Real-time step progress to stderr (what's happening now)
- `--verbose` → Tool calls in main output (what was called)

Note: `--debug` and `--trace` can be combined.

## Security

All file operations are **restricted to the project root** (path jailing):

- Files outside the project directory cannot be read
- Shell commands execute within the project root
- Sensitive files (`.env`, `.pem`, SSH keys) are blocked
- Only read-only shell commands are allowed
- All tool outputs are truncated (200 lines / 20K chars max)
- Tool calls have timeouts (30 seconds default)

## Available Tools

The model assumes these tools are available and uses them directly:

### File Tools
- `read_file(path)` - Read file contents at a given `path`. Large files are truncated (200 lines / 20K chars). Has 30s timeout. **Restricted to project root.**
- `list_directory(path, pattern)` - List files in `path` matching a glob `pattern`. Supports recursive patterns:
  - `*` - files in directory only
  - `**/*` - ALL files recursively (use this to discover nested structures)
  - `**/*.py` - all Python files recursively
  - `src/**/*.js` - all JS files under src/
  Excludes hidden files and common ignored directories. Returns up to 100 files. Has 30s timeout.
- `file_info(path)` - Get file metadata (size, type, modified time) for a given `path`. Has 30s timeout.

### Code Navigation Tools (New in v0.6.0)
- `search_code(pattern, file_path, ignore_case)` - **AST-aware code search**. Unlike simple grep, shows intelligent context around matches (function/class boundaries). Supports Python, JavaScript, TypeScript, Go, Rust, Ruby, Java, C/C++.
- `list_definitions(file_path)` - **Extract class/function definitions** from a source file. Shows signatures and docstrings without full implementation code. Great for understanding file structure quickly.

### Git Tools
- `git_diff(staged, file_path)` - Show code changes. Use `staged=True` for staged changes. Optionally provide a `file_path`. Output is truncated.
- `git_status()` - Check repo status. Output is truncated.
- `git_changed_files(staged, include_untracked)` - List changed files. Use `staged=True` for staged files, `include_untracked=True` to include untracked files. Output is truncated.
- `git_log(count)` - View commit history. `count` specifies number of commits (max 50). Output is truncated.

All tools return human-readable output or error messages on failure.
