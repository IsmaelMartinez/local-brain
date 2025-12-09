# Local Brain — Claude Code Plugin Marketplace

A [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugins) that extends Claude with local capabilities. The first skill lets Claude delegate codebase exploration to local Ollama models.

## 🔌 Install Marketplace

Add this marketplace to Claude Code:

```bash
/plugin marketplace add IsmaelMartinez/local-brain
```

Then install the plugin:

```bash
/plugin install local-brain@local-brain-marketplace
```

## 🧠 Available Plugins

### [`local-brain`](./local-brain/skills/local-brain/SKILL.md)

Delegate codebase exploration to local Ollama models. Claude offloads read-only tasks to your machine—no cloud round-trips, full privacy.

```
┌─────────────┐     delegates      ┌─────────────┐     calls      ┌─────────┐
│ Claude Code │ ──────────────────►│ Local Brain │ ──────────────►│ Ollama  │
│   (Cloud)   │                    │ (Smolagents)│                │ (Local) │
│             │◄────────────────── │             │◄────────────── │         │
└─────────────┘     returns        └─────────────┘    responds    └─────────┘
                    results                        with code execution
```

**What Claude can delegate:**
- "Review the code changes"
- "Explain how the auth module works"
- "Generate a commit message"
- "Find all TODO comments"

---

## Marketplace Structure

This repo follows the [Claude Code plugin structure](https://code.claude.com/docs/en/plugins):

```
local-brain/                          # MARKETPLACE ROOT
├── .claude-plugin/
│   └── marketplace.json              # Marketplace manifest
└── local-brain/                      # PLUGIN
    ├── plugin.json                   # Plugin manifest
    └── skills/
        └── local-brain/
            └── SKILL.md              # Skill documentation
```

---

## `local-brain` Plugin Details

### Prerequisites

1. **Install the CLI:**

```bash
uv pip install local-brain
```

Or with pipx:
```bash
pipx install local-brain
```

2. **Install Ollama** from [ollama.ai](https://ollama.ai) and pull a model:

```bash
ollama pull qwen3
```

### CLI Usage

```bash
local-brain "What files changed recently?"
local-brain "Review the code in src/"
local-brain "Generate a commit message"
local-brain "Explain how auth works"
```

```bash
local-brain "prompt"                       # Ask anything (auto-selects best model)
local-brain -v "prompt"                    # Verbose (show tool calls)
local-brain -m qwen2.5-coder:7b "prompt"   # Specific model
local-brain --list-models                  # Show available models
local-brain --root /path/to/project "prompt"  # Set project root
```

### Model Discovery

Local Brain automatically detects installed Ollama models and picks the best one:

```bash
local-brain --list-models
```

**Recommended models:**
- `qwen3:latest` — General purpose (default)
- `qwen2.5-coder:7b` — Code-focused
- `llama3.2:3b` — Fast, lightweight
- `mistral:7b` — Balanced

### Tools

Custom read-only tools registered with Smolagents' `@tool` decorator:

| Tool | What it does |
|------|--------------|
| `read_file` | Read file contents (path-jailed) |
| `list_directory` | List files with glob patterns (path-jailed) |
| `file_info` | Get file metadata (path-jailed) |
| `git_diff` | Show git changes (staged or unstaged) |
| `git_status` | Show current branch and changes |
| `git_log` | View recent commit history |
| `git_changed_files` | List modified/staged files |

### Architecture

Local Brain uses [Smolagents](https://github.com/huggingface/smolagents) as the agent framework:

```
local_brain/
├── __init__.py      # Version
├── cli.py           # Click CLI entry point
├── models.py        # Ollama model discovery & selection
├── security.py      # Path jailing utilities
└── smolagent.py     # CodeAgent + custom tools
```

**What comes from Smolagents:**
- `CodeAgent` — Agent that executes tasks via code generation
- `LiteLLMModel` — Connects to Ollama via LiteLLM
- `@tool` decorator — Registers our custom tools with the agent

**What we implement:**
- All 7 tools (read_file, git_diff, etc.) — our code, registered via `@tool`
- Path jailing security — restricts file access to project root
- Model discovery — detects installed Ollama models

### Security

**Sandboxed execution** via Smolagents LocalPythonExecutor:

- ✅ Read files within project directory (path-jailed)
- ✅ Execute git commands (read-only)
- ❌ File I/O outside project root blocked
- ❌ Dangerous imports blocked (subprocess, socket, etc.)
- ❌ Network access blocked
- ❌ Sensitive files blocked (`.env`, keys)

**Why no web access?** Claude Code already has web access—delegate web research to Claude, local codebase work to Local Brain. This separation prevents data exfiltration and prompt injection from fetched content.

### Future Ideas

- **MCP Bridge** — Ollama ↔ Model Context Protocol bridge when MCP adoption increases
- **Docker Sandbox** — Stronger isolation via container when Docker is available

### Architecture Decisions

See [docs/adrs/](./docs/adrs/) for Architecture Decision Records:
- [ADR-001](./docs/adrs/001-custom-implementation.md) — Why custom implementation over frameworks
- [ADR-002](./docs/adrs/002-smolagents.md) — Why Smolagents for code execution
- [ADR-003](./docs/adrs/003-no-web-tools.md) — Why no web tools

---

## Adding New Plugins

Want to add a plugin to this marketplace?

1. Create a new directory at the root:

```
your-plugin/
├── plugin.json
└── skills/
    └── your-skill/
        └── SKILL.md
```

2. Register it in `.claude-plugin/marketplace.json`:

```json
{
  "plugins": [
    { "name": "local-brain", "source": "./local-brain", "description": "..." },
    { "name": "your-plugin", "source": "./your-plugin", "description": "..." }
  ]
}
```

See the [Claude Code plugin docs](https://code.claude.com/docs/en/plugins) for full specifications.

---

## Development

```bash
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain
uv sync
uv run local-brain "Hello!"
```

**Note:** Requires Python 3.10-3.13 (grpcio build issue with 3.14).

### Run Tests

```bash
uv run pytest tests/ -v
```

### Test Plugin Locally

```bash
# In Claude Code
/plugin marketplace add ./path/to/local-brain
/plugin install local-brain@local-brain-marketplace
```

## License

MIT
