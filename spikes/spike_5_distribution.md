# Spike 5: Distribution Options Evaluation

**Goal:** Evaluate Python distribution methods for local-brain-py

## Distribution Options

### Option 1: pip/pipx (Recommended)

**Installation:**
```bash
# Standard pip
pip install local-brain

# pipx (isolated, recommended for CLI tools)
pipx install local-brain
```

**Pros:**
- ✅ Single command install
- ✅ Cross-platform (macOS, Linux, Windows)
- ✅ Easy updates (`pip install -U local-brain` or `pipx upgrade local-brain`)
- ✅ No build step needed
- ✅ Dependencies handled automatically
- ✅ Can publish to PyPI

**Cons:**
- ❌ Requires Python 3.8+ installed
- ❌ Slower startup than compiled binary
- ❌ Multiple files (not single binary)

**User friction:** LOW (if Python already installed)

### Option 2: PyInstaller (Single Binary)

**Build:**
```bash
pip install pyinstaller
pyinstaller --onefile local_brain/cli.py --name local-brain
```

**Installation:**
```bash
# Download binary for your platform
curl -LO https://github.com/user/local-brain-py/releases/download/v1.0.0/local-brain-linux-amd64
chmod +x local-brain-linux-amd64
sudo mv local-brain-linux-amd64 /usr/local/bin/local-brain
```

**Pros:**
- ✅ Single binary (like current Rust version)
- ✅ No Python required on target system
- ✅ Fast startup (bundled interpreter)

**Cons:**
- ❌ Large binary size (50-100MB vs 5MB Rust)
- ❌ Need to build for each platform (x86_64, arm64, Windows)
- ❌ Complex CI/CD pipeline
- ❌ Some antivirus false positives
- ❌ Slower build process

**User friction:** MEDIUM (download + chmod + move)

### Option 3: uv (Fast Python Package Manager)

**Installation:**
```bash
# Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install local-brain
uv pip install local-brain
# or
uvx local-brain  # Run without installing
```

**Pros:**
- ✅ Very fast package installation (10-100x faster than pip)
- ✅ Can run tools directly with `uvx` without installing
- ✅ Written in Rust, very fast
- ✅ Isolated environments by default

**Cons:**
- ❌ New tool, users may not have it
- ❌ Additional dependency (uv itself)
- ❌ Less widespread than pip

**User friction:** MEDIUM (need to install uv first)

### Option 4: Docker

**Installation:**
```bash
# Pull image
docker pull ghcr.io/user/local-brain-py:latest

# Run
docker run -v $(pwd):/workspace ghcr.io/user/local-brain-py --files /workspace/src/main.py
```

**Pros:**
- ✅ Completely isolated
- ✅ Exact same environment everywhere
- ✅ No Python/dependencies needed locally

**Cons:**
- ❌ Requires Docker
- ❌ Verbose command to run
- ❌ Volume mounting complexity
- ❌ Overhead of container startup

**User friction:** HIGH (Docker + verbose commands)

### Option 5: Homebrew (macOS/Linux)

**Installation:**
```bash
brew install user/tap/local-brain
```

**Pros:**
- ✅ Single command on macOS
- ✅ Handles Python dependency
- ✅ Easy updates (`brew upgrade local-brain`)

**Cons:**
- ❌ macOS/Linux only (Linuxbrew exists but less common)
- ❌ Need to maintain Homebrew formula
- ❌ Need to set up tap

**User friction:** LOW (on macOS)

---

## Evaluation Matrix

| Criterion | pip/pipx | PyInstaller | uv | Docker | Homebrew |
|-----------|----------|-------------|-----|--------|----------|
| Install commands | 1 | 3 | 2 | 2 | 1 |
| Cross-platform | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| No runtime deps | ❌ | ✅ | ❌ | ✅ | ✅ |
| Easy updates | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| Binary size | N/A | 50-100MB | N/A | ~500MB | N/A |
| CI/CD complexity | LOW | HIGH | LOW | MEDIUM | MEDIUM |
| Startup time | ~500ms | ~200ms | ~500ms | ~1s | ~500ms |

---

## Recommendation

### Primary: pipx (for CLI tool users)

```bash
pipx install local-brain
```

**Why:**
- Single command installation
- Isolated from system Python
- Easy updates
- Standard in Python ecosystem
- Most users doing AI/LLM work have Python

### Secondary: PyPI (for library users)

```bash
pip install local-brain
```

**Why:**
- Can be used programmatically
- Import as library in other projects

### Tertiary: GitHub Releases (for users without Python)

Provide PyInstaller binaries for those who don't want Python:
- `local-brain-macos-arm64`
- `local-brain-macos-x86_64`
- `local-brain-linux-x86_64`
- `local-brain-windows-x86_64.exe`

---

## pyproject.toml Setup

```toml
[project]
name = "local-brain"
version = "0.2.0"
description = "Skill-based LLM tasks using local Ollama models"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
authors = [
    {name = "Ismael Martinez", email = "ismaelmartinez@gmail.com"}
]
keywords = ["ollama", "llm", "code-review", "cli"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Quality Assurance",
]
dependencies = [
    "ollama>=0.3.0",
    "click>=8.0.0",
    "pyyaml>=6.0.0",
    "jinja2>=3.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[project.scripts]
local-brain = "local_brain.cli:main"

[project.urls]
Homepage = "https://github.com/IsmaelMartinez/local-brain"
Repository = "https://github.com/IsmaelMartinez/local-brain"
Documentation = "https://github.com/IsmaelMartinez/local-brain#readme"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## Migration Path

1. **Create `local-brain-py` branch/directory**
2. **Set up pyproject.toml** with above config
3. **Implement core Python package**
4. **Test locally with `pip install -e .`**
5. **Publish to PyPI** as `local-brain` (if available) or `local-brain-py`
6. **Update Claude Code skill** to prefer Python version
7. **Deprecate Rust version** after 1-2 months
8. **Optionally build PyInstaller binaries** for binary-preferred users

---

## Spike Conclusion

**Recommended approach:** `pipx install local-brain`

- Simplest for target audience (developers)
- Standard Python packaging
- No special tooling needed
- Easy CI/CD (just publish to PyPI)
- Updates work out of the box

**Fallback:** Provide PyInstaller binaries in GitHub Releases for users who prefer single binaries.

