# Installation Guide

Complete setup instructions for local-brain.

## System Requirements

**Minimum**:
- 8GB RAM (for smallest models)
- 10GB disk space
- macOS, Linux, or Windows (WSL2)

**Recommended**:
- 16GB RAM (for best performance with larger models)
- 20GB disk space (for multiple models)
- macOS or Linux (native support)

## Prerequisites

### 1. Install Rust

**macOS / Linux**:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

**Windows** (PowerShell):
```powershell
# Download and run rustup-init.exe from:
# https://rustup.rs/
```

**Verify installation**:
```bash
rustc --version
# Expected: rustc 1.70+ or newer
```

### 2. Install Ollama

Ollama provides the local LLM runtime.

**macOS**:
```bash
# Download from ollama.ai/download
# Or use Homebrew:
brew install ollama

# Start Ollama service
ollama serve
```

**Linux**:
```bash
curl -fsSL https://ollama.ai/install.sh | sh

# Ollama runs as a system service automatically
# Check status:
systemctl status ollama
```

**Windows**:
```bash
# Download from ollama.ai/download
# Follow Windows installer instructions
```

**Verify installation**:
```bash
curl http://localhost:11434/api/tags
# Expected: {"models":[...]} or empty list
```

### 3. Download LLM Models

Choose models based on your RAM and needs:

**Recommended for 16GB+ RAM**:
```bash
# Best overall quality (8.9GB)
ollama pull deepseek-coder-v2:16b
```

**For 8-12GB RAM** (fast, lightweight):
```bash
# Fast code reviews (1.9GB)
ollama pull qwen2.5-coder:3b

# Quick summaries (1.3GB)
ollama pull llama3.2:1b
```

**Verify models**:
```bash
ollama list
# Should show downloaded models
```

## Installation

### Build from Source

```bash
# 1. Clone repository
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain

# 2. Build release binary
cargo build --release

# 3. Verify binary exists
ls -lh target/release/local-brain
# Expected: ~5-10MB executable

# 4. Optional: Add to PATH
export PATH="$PATH:$(pwd)/target/release"
# Or copy to system path:
# sudo cp target/release/local-brain /usr/local/bin/
```

## Verification

Test the installation with a simple file review:

```bash
# 1. Create test file
echo 'fn main() { println!("Hello, world!"); }' > /tmp/test.rs

# 2. Run review
echo '{"file_path":"/tmp/test.rs"}' | ./target/release/local-brain

# 3. Expected output (JSON):
# {
#   "spikes": [...],
#   "simplifications": [...],
#   "defer_for_later": [...],
#   "other_observations": [...]
# }
```

**If successful**, you should see structured JSON output. ✅

## First Run

Try reviewing a real file:

```bash
# Review a file with specific model
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain --model qwen2.5-coder:3b | jq .

# Review git changes
./target/release/local-brain --git-diff --task quick-review
```

## Troubleshooting Installation

### Rust Build Fails

```bash
# Update Rust toolchain
rustup update

# Clean and rebuild
cargo clean
cargo build --release
```

### Ollama Connection Failed

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama service (macOS/Linux)
ollama serve

# Check logs
journalctl -u ollama -f  # Linux
```

### Model Not Found

```bash
# List available models
ollama list

# Pull missing model
ollama pull deepseek-coder-v2:16b

# Test model directly
ollama run deepseek-coder-v2:16b "Hello"
```

### Binary Not Found

```bash
# Use full path
./target/release/local-brain

# Or add to PATH
export PATH="$PATH:$(pwd)/target/release"
echo $PATH
```

## Configuration

Local-brain uses environment variables for configuration:

```bash
# Optional: Custom Ollama host
export OLLAMA_HOST="http://localhost:11434"

# Optional: Fallback model (deprecated, use CLI flags)
export MODEL_NAME="deepseek-coder-v2:16b"
```

## Next Steps

✅ Installation complete!

**Continue to**:
- [QUICKSTART.md](QUICKSTART.md) - 5-minute tutorial with examples
- [MODELS.md](MODELS.md) - Choose the right model for your task
- [README.md](README.md) - Advanced features and usage

**Need help?**
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [GitHub Issues](https://github.com/IsmaelMartinez/local-brain/issues) - Report problems
