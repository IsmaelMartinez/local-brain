# Local Brain

Chat with local Ollama models that can explore your codebase.

```bash
local-brain "What files changed recently?"
local-brain "Explain src/main.py"
local-brain --review              # Code review
local-brain --commit              # Generate commit message
```

## Install

```bash
pipx install local-brain    # Recommended
# or
pip install local-brain
```

**Requires:** [Ollama](https://ollama.ai) running locally with a model:
```bash
ollama pull qwen3
```

## Usage

```bash
# Ask anything - model uses tools to explore
local-brain "What's in this repo?"
local-brain "How does the auth system work?"

# Review code
local-brain --review                    # Review git changes
local-brain --review src/utils.py       # Review specific file

# Generate commit message
local-brain --commit

# Options
local-brain -v "prompt"                 # Verbose (show tool calls)
local-brain -m llama3.2 "prompt"        # Different model
```

## How It Works

The model has tools to explore your codebase:

| Tool | What it does |
|------|--------------|
| `read_file` | Read file contents |
| `list_directory` | List files (glob patterns) |
| `git_diff` | See code changes |
| `git_status` | Check repo status |
| `run_command` | Run safe shell commands |

```bash
$ local-brain -v "What Python files are here?"

🤖 Model: qwen3:latest
🔧 Tools: 9
----------------------------------------

📍 Turn 1
   📞 1 tool call(s)
      → list_directory(path='.', pattern='*.py')
        ← main.py, setup.py, test_utils.py

📍 Turn 2
   ✅ Done
The Python files are: main.py, setup.py, test_utils.py
```

## Development

```bash
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain
uv sync
uv run local-brain "Hello!"
```

## License

MIT
