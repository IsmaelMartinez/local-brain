# Installation

## Requirements

- 8GB RAM minimum (16GB recommended)
- 10GB disk space
- macOS, Linux, or Windows (WSL2)

## Installation Methods

### Option 1: Pre-built Binaries (Recommended)

Download the latest release for your platform from [GitHub Releases](https://github.com/IsmaelMartinez/local-brain/releases):

#### macOS
```bash
# Intel Mac
curl -L https://github.com/IsmaelMartinez/local-brain/releases/latest/download/local-brain-x86_64-apple-darwin.tar.gz | tar xz
sudo mv local-brain /usr/local/bin/

# Apple Silicon (M1/M2/M3)
curl -L https://github.com/IsmaelMartinez/local-brain/releases/latest/download/local-brain-aarch64-apple-darwin.tar.gz | tar xz
sudo mv local-brain /usr/local/bin/

# Verify
local-brain --version
```

#### Linux
```bash
# x86_64
curl -L https://github.com/IsmaelMartinez/local-brain/releases/latest/download/local-brain-x86_64-unknown-linux-gnu.tar.gz | tar xz
sudo mv local-brain /usr/local/bin/

# Verify
local-brain --version
```

#### Windows
1. Download `local-brain-x86_64-pc-windows-msvc.zip` from releases
2. Extract `local-brain.exe`
3. Add to PATH or move to a directory in PATH

### Option 2: Cargo Install

Requires Rust toolchain installed.

```bash
cargo install local-brain
```

### Option 3: Cargo Binstall (Fast)

No compilation required.

```bash
cargo install cargo-binstall  # One-time setup
cargo binstall local-brain
```

### Option 4: Build from Source

#### 1. Install Rust

```bash
# macOS / Linux
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Windows: Download from https://rustup.rs/

# Verify
rustc --version  # Should be 1.70+
```

#### 2. Build
```bash
git clone https://github.com/IsmaelMartinez/local-brain.git
cd local-brain
cargo build --release

# Binary at: ./target/release/local-brain
```

## Install Ollama

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

## Pull Models

```bash
# Recommended: Fast and capable (1.9GB)
ollama pull qwen2.5-coder:3b

# Or thorough analysis (8.9GB, needs 16GB RAM)
ollama pull deepseek-coder-v2:16b

# Verify
ollama list
```

## Test Installation

```bash
# Test version
local-brain --version

# Test with sample file
echo 'fn main() {}' > /tmp/test.rs
echo '{"file_path":"/tmp/test.rs"}' | local-brain
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
