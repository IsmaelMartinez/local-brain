# Installation

## Requirements

- 8GB RAM minimum (16GB recommended)
- 10GB disk space
- macOS, Linux, or Windows (WSL2)

## 1. Install Rust

```bash
# macOS / Linux
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Windows: Download from https://rustup.rs/

# Verify
rustc --version  # Should be 1.70+
```

## 2. Install Ollama

```bash
# macOS
brew install ollama
ollama serve

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Download from ollama.ai/download

# Verify
curl http://localhost:11434/api/tags
```

## 3. Pull a Model

```bash
# Recommended: Fast and capable (1.9GB)
ollama pull qwen2.5-coder:3b

# Or thorough analysis (8.9GB, needs 16GB RAM)
ollama pull deepseek-coder-v2:16b

# Verify
ollama list
```

## 4. Build Binary

```bash
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain
cargo build --release
```

## 5. Test

```bash
echo 'fn main() {}' > /tmp/test.rs
echo '{"file_path":"/tmp/test.rs"}' | ./target/release/local-brain
```

You should see JSON output with `spikes`, `simplifications`, etc.

## Troubleshooting

**Build fails**: `rustup update && cargo clean && cargo build --release`

**Ollama not running**: `ollama serve`

**Model not found**: `ollama pull qwen2.5-coder:3b`

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more issues.

## Next Steps

- [QUICKSTART.md](QUICKSTART.md) - Tutorial
- [MODELS.md](MODELS.md) - Model guide
