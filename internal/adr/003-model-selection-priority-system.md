# ADR-003: Model Selection Priority System

**Status**: Accepted

**Date**: November 2025

**Deciders**: Project maintainer

---

## Context

Local-brain supports multiple Ollama models optimized for different tasks (fast feedback, security review, low-resource environments). Users need flexibility to specify models in multiple ways:

1. **Default behavior**: System picks best model for general use
2. **Task-based**: User specifies task type (e.g., "quick-review"), system picks appropriate model
3. **Explicit override**: User specifies exact model name
4. **Per-file configuration**: Project-level model preferences in models.json

Without a clear priority system, users would experience unpredictable model selection, leading to confusion and incorrect results.

### Requirements

- **Predictability**: User should always know which model will be used
- **Flexibility**: Support different use cases (CLI, project config, task-based)
- **Override capability**: Allow explicit model selection to bypass defaults
- **Documentation**: Clear documentation of priority rules

## Decision

Implement a **4-level priority system** for model selection:

```
Priority 1 (HIGHEST): CLI --model flag (explicit user override)
Priority 2:            models.json registry (project-level config)
Priority 3:            CLI --task flag (task-based selection)
Priority 4 (DEFAULT):  Built-in default model
```

### Selection Algorithm

```rust
fn select_model(cli_model: Option<String>, task: Option<String>, registry: &ModelsRegistry) -> String {
    // Priority 1: CLI --model flag (explicit override)
    if let Some(model) = cli_model {
        return model;
    }

    // Priority 2: models.json registry lookup by file extension
    if let Some(model) = registry.get_model_for_file(file_path) {
        return model;
    }

    // Priority 3: --task flag
    if let Some(task_type) = task {
        return registry.get_model_for_task(task_type);
    }

    // Priority 4: Default model
    return "deepseek-coder-v2-8k".to_string();
}
```

### CLI Interface

```bash
# Priority 4: Default model
local-brain --file src/main.rs

# Priority 3: Task-based selection (picks qwen2.5-coder:3b for speed)
local-brain --file src/main.rs --task quick-review

# Priority 2: models.json mapping (e.g., Rust files → deepseek-coder-v2:16b)
# Configured in models.json: {"patterns": {"*.rs": {"model": "deepseek-coder-v2:16b"}}}
local-brain --file src/main.rs

# Priority 1: Explicit override (highest priority)
local-brain --file src/main.rs --model llama3.2:1b
```

### models.json Structure

```json
{
  "models": {
    "deepseek-coder-v2-8k": {
      "description": "Balanced performance and accuracy",
      "capabilities": ["code-review", "refactoring", "security"],
      "min_ram_gb": 10
    }
  },
  "tasks": {
    "quick-review": "qwen2.5-coder:3b",
    "security": "deepseek-coder-v2:16b",
    "low-resource": "llama3.2:1b"
  },
  "patterns": {
    "*.rs": {"model": "deepseek-coder-v2:16b"},
    "*.js": {"model": "qwen2.5-coder:7b"}
  }
}
```

## Rationale

### Why This Priority Order?

1. **CLI --model (Highest)**: User explicitly typing a model name indicates strong intent - must always win
2. **models.json (Second)**: Project-level config represents team decisions, should apply by default
3. **--task (Third)**: Convenience feature for common workflows, easily overridden
4. **Default (Lowest)**: Safe fallback for simple usage

### Why 4 Levels?

- **Flexibility**: Covers solo dev (CLI flags) and team workflows (models.json)
- **Predictability**: Clear hierarchy, no ambiguity
- **Simplicity**: Not too many levels (considered adding environment variables, rejected as too complex)

### Design Principles

1. **Explicit > Implicit**: CLI flags override config files
2. **Specific > General**: File-specific config overrides task-based selection
3. **User > System**: User choices always win over system defaults

## Consequences

### Positive

- **Clear documentation**: Users understand exactly which model will be used
- **Flexibility**: Supports different use cases (quick checks, thorough reviews, team workflows)
- **Override capability**: Power users can always force a specific model
- **Testable**: Priority system is deterministic and unit-testable
- **Extensible**: Easy to add new task types or pattern matches in models.json

### Negative

- **Complexity**: 4 levels may confuse beginners (mitigated by good defaults)
- **Documentation burden**: Must explain priority system clearly
- **Debugging**: Users may not understand why a particular model was selected

### Neutral

- **Configuration**: models.json is optional (defaults work fine)
- **Backward compatibility**: Adding new priority levels would break expectations

## Alternatives Considered

### 1. Single Priority: CLI --model Only
**Pros**: Simplest possible design
**Cons**: No support for project-level config or task-based selection
**Decision**: Rejected - too inflexible for real-world use

### 2. Environment Variables as Priority 2
**Pros**: Standard Unix practice, supports CI/CD
**Cons**: Adds complexity, conflicts with project config, hard to document
**Decision**: Rejected - models.json is clearer for project settings

### 3. Auto-Detection Based on File Content
**Pros**: "Smart" selection, no user input needed
**Cons**: Slow (requires reading file), unpredictable, hard to debug
**Decision**: Rejected - predictability more important than automation

### 4. Weighted Scoring System
**Pros**: Could consider multiple factors (file size, complexity, RAM available)
**Cons**: Complex algorithm, hard to explain, non-deterministic
**Decision**: Rejected - simple priority system is more maintainable

### 5. Interactive Prompts
**Pros**: User chooses model every time
**Cons**: Breaks automation, annoying for repeated use
**Decision**: Rejected - good defaults are better than prompts

## Implementation Notes

### Flag Parsing

```rust
#[derive(Parser)]
struct Cli {
    #[arg(long)]
    model: Option<String>,  // Priority 1

    #[arg(long)]
    task: Option<String>,   // Priority 3

    #[arg(long)]
    file: PathBuf,
}
```

### Registry Lookup

```rust
impl ModelsRegistry {
    fn get_model_for_file(&self, path: &Path) -> Option<String> {
        let ext = path.extension()?.to_str()?;
        self.patterns.get(format!("*.{}", ext))?.model
    }

    fn get_model_for_task(&self, task: &str) -> Option<String> {
        self.tasks.get(task).cloned()
    }
}
```

### Error Handling

- Unknown model name: Warn but proceed (user may have custom model)
- Unknown task type: Error with list of valid tasks
- Missing models.json: Use defaults (file is optional)

## References

- **Implementation**: `src/main.rs` (model selection logic)
- **Configuration**: `models.json` (model registry)
- **Documentation**: [MODELS.md](../../MODELS.md)
- **Related Decision**: ADR-001 (model behavior and limitations)
- **Feature Completion**: [PRIORITIZATION_ANALYSIS.md](../PRIORITIZATION_ANALYSIS.md) (Targeted Model Selection ✅)

## Future Considerations

### Potential Extensions

1. **Profile Support**: Named profiles (e.g., `--profile fast` = quick-review + low-resource settings)
2. **Context-Aware Selection**: Auto-detect git commit messages, CI environment
3. **Model Fallback**: If preferred model unavailable, try alternative
4. **Performance Tracking**: Learn from past reviews which models work best for which files

### Breaking Changes to Avoid

- **Never change priority order**: Would break user expectations
- **Never remove default model**: Always need a fallback
- **Never make models.json required**: Should work without configuration

## Notes

This system balances **flexibility** (power users can override) with **simplicity** (beginners can ignore flags). The 4-level priority is sufficient for current use cases and extensible for future needs.

**Key Insight**: Predictability matters more than automation. Users prefer knowing exactly which model will run, even if it means specifying flags, over "smart" auto-detection that might surprise them.
