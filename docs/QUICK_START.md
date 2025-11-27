# Quick Start

Get started with local-brain in less than 5 minutes. Choose the path that matches your needs.

## Option 1: Claude Code Plugin (Easiest - Recommended)

Use local-brain directly from Claude Code without installation.

### Prerequisites
- Claude Code (with plugin support)
- Ollama running locally with at least one model pulled

### Installation
```bash
# In Claude Code, use the plugin marketplace
/plugin marketplace add IsmaelMartinez/local-brain
```

### First Review
```
In Claude Code, ask: "Review this file"

Or use the skill directly:
/skill local-brain --files "path/to/file.rs"
```

No binary installation needed - the skill handles everything.

---

## Option 2: Standalone Binary (More Control)

Use local-brain directly from your terminal.

### Prerequisites
- Ollama running locally (default: http://localhost:11434)
- At least one model pulled: `ollama pull qwen2.5-coder:3b`

### Installation

**macOS/Linux (pre-built):**
```bash
curl -fsSL https://github.com/IsmaelMartinez/local-brain/releases/download/v0.2.0/local-brain-{macos,linux} -o local-brain
chmod +x local-brain
./local-brain --files "src/main.rs"
```

**Or build from source:**
```bash
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain
cargo build --release
./target/release/local-brain --files "src/main.rs"
```

---

## Your First Review

### Review a single file
```bash
local-brain --files "src/main.rs"
```

### Review multiple files
```bash
local-brain --files "src/main.rs,src/lib.rs"
```

### Review git changes
```bash
local-brain --git-diff
```

### Review with a specific model
```bash
local-brain --model "qwen2.5-coder:3b" --files "src/main.rs"
```

---

## Next Steps

- **Need help?** See [INSTALLATION.md](INSTALLATION.md) for detailed setup
- **Want to learn more?** See [USAGE_GUIDE.md](USAGE_GUIDE.md) for common patterns
- **Choosing a model?** See [MODELS.md](MODELS.md) for model comparison
- **Troubleshooting?** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for solutions

---

## Verify Installation

### Check local-brain is working
```bash
local-brain --help
```

### Check Ollama is running
```bash
ollama ps
```

### Try a dry run (no Ollama needed)
```bash
local-brain --dry-run --files "src/main.rs"
```

---

## Common Tasks

### Security review
```bash
local-brain --task security --files "auth.rs"
```

### Quick review (fast model)
```bash
local-brain --task quick-review --files "main.rs"
```

### Review whole directory
```bash
local-brain --dir src --pattern "*.rs"
```

### Get help
```bash
local-brain --help
```
