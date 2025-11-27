# Architecture

Overview of local-brain's system design and implementation.

## System Overview

Local Brain is a Rust CLI tool that performs structured code reviews using local Ollama LLM models. It's optimized for context offloading from Claude Code to minimize tokens while providing high-quality Markdown-formatted reviews.

```
┌─────────────────┐
│   User Input    │
│  (files, CLI)   │
└────────┬────────┘
         │
    ┌────▼──────┐
    │  local-   │
    │  brain    │──── timeout/retry ────┐
    │   CLI     │                        │
    └────┬──────┘                        │
         │                               │
    ┌────▼──────────────────────────────▼───┐
    │         Ollama (HTTP/JSON)             │
    │     (localhost:11434/api/chat)         │
    └────┬──────────────────────────────┬───┘
         │                              │
    ┌────▼────────────┐          ┌──────▼────────┐
    │ Markdown Output │          │ Error Handling│
    │   (structured)  │          │ (clear msgs)  │
    └─────────────────┘          └───────────────┘
```

## Single-File Architecture

All code lives in `src/main.rs` (~800 lines):

```
src/main.rs
├── CLI Arguments (clap-based, lines 60-99)
├── Model Registry Structures (lines 102-150)
├── Main Entry Point (lines 127-150)
├── Mode Handlers:
│   ├── handle_git_diff() - git changes review (lines 247-292)
│   ├── handle_files() - file list review (lines 294-336)
│   └── handle_directory() - pattern-based review (lines 338-396)
├── Review Core:
│   ├── review_multiple_files() - loop over files (lines 398-434)
│   ├── review_file() - single file review (lines 206-244)
│   └── build_prompt() - prompt construction (lines 594-680)
├── Model Selection (lines 440-516)
├── Ollama Integration:
│   ├── call_ollama() - HTTP request (lines 683-746)
│   └── Error handling with timeout/validation
└── Tests (lines 752-800)
```

### Why Single-File?

1. **Fast startup** - No module loading overhead
2. **Easy to understand** - Entire flow visible in one place
3. **Minimal dependencies** - 4 external crates: serde, reqwest, anyhow, clap
4. **Fast compilation** - Build in ~20 seconds
5. **Skill integration** - Designed to run as subprocess from Claude Code

## Key Components

### 1. CLI Arguments (`Cli` struct, lines 60-99)

```rust
struct Cli {
    // Input modes (choose one)
    #[arg(long)]
    model: Option<String>,

    #[arg(long)]
    task: Option<String>,

    #[arg(long)]
    git_diff: bool,

    #[arg(long)]
    dir: Option<PathBuf>,

    #[arg(long)]
    pattern: Option<String>,

    #[arg(long)]
    files: Option<String>,

    // Options
    #[arg(long)]
    dry_run: bool,

    #[arg(long)]
    kind: Option<String>,

    #[arg(long)]
    review_focus: Option<String>,

    #[arg(long)]
    timeout: Option<u64>,
}
```

**Input Modes:**
- `--files`: Comma-separated file list
- `--git-diff`: Git staged/modified files
- `--dir` + `--pattern`: Directory pattern matching

**Model Selection:**
- `--task`: Task-based (quick-review, security, etc.)
- `--model`: Explicit override

**Context Flags:**
- `--kind`: Document type (code, design-doc, ticket, other)
- `--review-focus`: Focus area (refactoring, readability, performance, risk, general)

### 2. Model Registry (models.json)

```json
{
  "models": [
    {
      "name": "qwen2.5-coder:3b",
      "size_gb": 1.9,
      "speed": "fast"
    },
    {
      "name": "deepseek-coder-v2-8k",
      "size_gb": 8.9,
      "speed": "moderate"
    }
  ],
  "task_mappings": {
    "quick-review": "qwen2.5-coder:3b",
    "security": "deepseek-coder-v2-8k"
  },
  "default_model": "deepseek-coder-v2-8k"
}
```

### 3. Data Flow

```
Input
  ↓
Determine file(s) to review
  ↓
For each file:
  1. Read file content
  2. Select model (CLI flag > task > env > default)
  3. Build prompts (system + user)
  4. Call Ollama HTTP API (with timeout/retry)
  5. Parse response markdown
  ↓
Output (Markdown to stdout, errors to stderr)
```

### 4. Prompt Building (lines 594-680)

**System Prompt** (~300 chars):
- Explains role: "senior code reviewer"
- Defines output structure with markdown headings
- Lists review categories

**User Prompt** (~1KB per file):
- File metadata: name, size, type
- Review context: document type, focus area
- Full file content

### 5. Ollama Integration (lines 683-746)

```rust
fn call_ollama(
    system_msg: &str,
    user_msg: &str,
    model_name: &str,
) -> Result<String>
```

**Features:**
- HTTP POST to `{OLLAMA_HOST}/api/chat`
- 120s default timeout (configurable via --timeout)
- Request validation:
  - Checks HTTP status
  - Validates response is not empty
  - Validates content is not empty
- Markdown content extraction and return

### 6. Output Format

All reviews produce structured Markdown:

```markdown
# Code Review

### filename.ext

## Issues Found
- **Title**: Description (lines: X-Y)

## Simplifications
- **Title**: Description

## Consider Later
- **Title**: Description

## Other Observations
- General observation
```

## Data Structures

### Review Request
```
File Path + Metadata
├── kind: code|design-doc|ticket|other
├── review_focus: refactoring|readability|performance|risk|general
└── model: string (optional override)
```

### Ollama Request Body
```json
{
  "model": "qwen2.5-coder:3b",
  "messages": [
    {
      "role": "system",
      "content": "[system prompt about review structure]"
    },
    {
      "role": "user",
      "content": "[metadata + file content]"
    }
  ],
  "stream": false
}
```

### Ollama Response
```json
{
  "model": "qwen2.5-coder:3b",
  "created_at": "2025-11-26T...",
  "message": {
    "role": "assistant",
    "content": "## Issues Found\n..."
  }
}
```

## Model Selection Priority

1. **CLI `--model` flag** (highest priority - explicit user choice)
2. **Task-based `--task` mapping** (from models.json)
3. **`MODEL_NAME` environment variable** (fallback config)
4. **Default model** (from models.json, typically deepseek-coder-v2-8k)

## Error Handling

Strategy: `anyhow::Result` with context throughout

```rust
// Pattern: Add context to each error
let content = std::fs::read_to_string(&file_path)
    .context(format!("Failed to read file: {}", file_path.display()))?;
```

**Output:**
- Markdown review → stdout
- Errors/diagnostics → stderr
- Exit code: 0 (success) or 1 (error)

**User-Friendly Messages:**
- Timeout: "Failed to send request to Ollama. Check if Ollama is running..."
- Empty response: "Ollama returned empty response. The model may have crashed..."

## External Dependencies

| Crate | Purpose | Lines |
|-------|---------|-------|
| `clap` | CLI argument parsing | ~20 |
| `serde`/`serde_json` | JSON parsing (models.json, Ollama) | ~30 |
| `reqwest` | HTTP client for Ollama API | ~40 |
| `anyhow` | Error handling/context | ~10 |

**Total external code used:** <100 lines of business logic.

## Performance Characteristics

**Startup:** <100ms (no async, minimal allocations)
**Single Review:** 10-30 seconds (mostly Ollama inference)
**Multi-File:** Sequential (one model instance)

```
1 file:    15s
5 files:   75s (5 × 15s sequential)
10 files:  150s
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Single-file architecture | Fast startup, easy debugging, skill-friendly |
| Sequential multi-file reviews | Predictable resource usage, no concurrency bugs |
| Markdown output | Human-readable, no special parsing needed |
| No streaming responses | Simpler implementation, full content available for validation |
| 120s timeout default | Handles slow models without excessive waiting |
| Response validation | Catches empty/malformed responses from model crashes |

## Future Extensibility

Current design supports:
- Adding new input modes (easy: add CLI flag + handler)
- Adding new models (easy: add to models.json)
- Adding new output formats (possible: requires output parsing refactor)
- Retry logic (possible: wrap call_ollama function)
- Parallel reviews (hard: would need async refactor)

## Testing

**Unit Tests** (lines 752-800):
- Prompt building with various inputs
- Model registry loading

**Integration Tests:**
- Full review with real Ollama
- Git diff mode with staged changes
- Dry-run mode without Ollama

**Manual Testing:**
```bash
# Dry run (no Ollama)
local-brain --dry-run --files src/main.rs

# Real review
local-brain --files src/main.rs

# Git diff
local-brain --git-diff

# Directory review
local-brain --dir src --pattern "*.rs"
```

## Skill Integration

Located in `.claude/skills/local-brain/SKILL.md`:
- Tiered architecture (hooks → binary → subagent)
- Launched as subprocess with file arguments
- Parses Markdown output into sections
- Integrates findings into conversation context

---

See [SETUP.md](SETUP.md) for development setup and commands.
