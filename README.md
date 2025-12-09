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
│   (Cloud)   │                    │    (CLI)    │                │ (Local) │
│             │◄────────────────── │             │◄────────────── │         │
└─────────────┘     returns        └─────────────┘    responds    └─────────┘
                    results                           with tools
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
    ├── .claude-plugin/
    │   └── plugin.json               # Plugin manifest
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

The model has these read-only tools:

| Tool | What it does |
|------|--------------|
| `read_file` | Read file contents |
| `list_directory` | List files (glob patterns) |
| `file_info` | Get file metadata |
| `git_diff` | See code changes |
| `git_status` | Check repo status |
| `git_log` | View commit history |
| `git_changed_files` | List changed files |
| `run_command` | Run safe shell commands |

### Security

All operations are **restricted to the project root** (path jailing):

- ✅ Read files within project directory
- ✅ Run safe, read-only shell commands
- ❌ Access files outside project root
- ❌ Read sensitive files (`.env`, keys)
- ❌ Network access

---

## Adding New Plugins

Want to add a plugin to this marketplace?

1. Create a new directory at the root:

```
your-plugin/
├── .claude-plugin/
│   └── plugin.json
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

### Test Plugin Locally

```bash
# In Claude Code
/plugin marketplace add ./path/to/local-brain
/plugin install local-brain@local-brain-marketplace
```

## License

MIT
