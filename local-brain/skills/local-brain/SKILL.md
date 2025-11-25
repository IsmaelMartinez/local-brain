---
name: local-brain
description: Delegate code reviews, document analysis, and planning tasks to local Ollama LLM models to reduce context usage. Supports lightweight hooks (ai, ai-cmd, ai-explain) for quick operations and heavyweight agent for multi-file reviews. Use when users request code reviews, design document summaries, ticket/issue triage, documentation analysis, planning, or routine pattern matching. Ideal for routine analysis that doesn't require cloud-scale reasoning. Do NOT use for complex multi-step reasoning requiring extensive codebase context or security-critical decisions.
---

# Local Brain - Context Offloading Skill

Tiered system for offloading work to local Ollama models, preserving main agent context.

## Tiers

**Tier 1 - Hooks** (fastest, direct bash):
- `ai` - Quick Q&A
- `ai-cmd` - Command generation
- `ai-explain` - Explain last command

**Tier 2 - local-brain binary** (structured reviews):
- Single/multiple file reviews
- Directory reviews with patterns
- Git diff reviews
- Structured Markdown output

**Tier 3 - Subagent** (heavyweight, multi-file):
- Orchestrates multiple local-brain calls
- Handles complex multi-file analysis
- Coordinates multiple review tasks

## Decision Logic

Use this flowchart to select the right tier:

```
User request
    ↓
Is it a quick question/explanation?
    → YES: Use Tier 1 (hooks)
    → NO: Continue
        ↓
    Is it 1-3 files for review?
        → YES: Use Tier 2 (local-brain binary directly)
        → NO: Continue
            ↓
        Multiple files OR multiple review tasks?
            → YES: Use Tier 3 (spawn subagent)
```

## Prerequisites

- **Ollama** running locally with at least one model
- **local-brain** binary installed
- **Hooks** defined in `~/.zshrc` (ai, ai-cmd, ai-explain)

Check prerequisites: `which local-brain && ollama ps`

See [CLI_REFERENCE.md](references/CLI_REFERENCE.md) for installation and [HOOKS.md](references/HOOKS.md) for hook details.

## Tier 1: Lightweight Hooks

### When to Use
- Quick factual questions
- Command generation
- Explaining last command/output
- NO file reading needed

### Usage

**Quick Q&A:**
```bash
ai "brief question"
```

**Command generation:**
```bash
ai-cmd "task description"
```

**Explain last command:**
```bash
ai-explain
```

See [HOOKS.md](references/HOOKS.md) for detailed hook documentation.

## Tier 2: Direct local-brain Binary

### When to Use
- Review 1-3 specific files
- Single directory review
- Single git diff review
- Want structured Markdown output

### Usage

**IMPORTANT:** Do NOT read file contents first - that defeats the purpose of context offloading.

1. Verify files exist: `ls path/to/file` (do NOT use Read tool)
2. Run local-brain directly:

```bash
# Single file
local-brain --files path/to/file

# Multiple files
local-brain --files path/file1,path/file2

# Directory
local-brain --dir src --pattern "*.rs"

# Git diff
local-brain --git-diff

# With task type
local-brain --task quick-review --files path/to/file
```

3. Parse and present the Markdown output sections:
   - Issues Found
   - Simplifications
   - Consider Later
   - Other Observations

## Tier 3: Heavyweight Subagent

### When to Use
- Multiple directories to review
- Multiple separate review tasks
- Need to coordinate multiple local-brain calls
- Complex multi-step analysis

### Usage

Spawn subagent using Task tool with `subagent_type=general-purpose` and `model=haiku`:

**Example prompt:**
```
Review multiple files using local-brain without reading them into context.

IMPORTANT: Do NOT read file contents - offload to local-brain.

Prerequisites verified:
- local-brain: [path]
- Ollama: [status]

Tasks:
1. Review [file1] with local-brain --files [file1]
2. Review [file2] with local-brain --files [file2]
3. Review [dir] with local-brain --dir [dir] --pattern "*.ext"

For each review:
- Execute local-brain command
- Parse Markdown output
- Extract key findings

Return consolidated summary:
1. Critical issues across all files
2. Common patterns found
3. Recommended priority actions

Return complete analysis in final message.
```

### Subagent Responsibilities
1. Execute multiple local-brain commands
2. Parse each Markdown output
3. Consolidate findings
4. Return structured summary

## Output Handling

All tiers produce different outputs:

**Tier 1 (hooks):** Plain text responses
**Tier 2 (binary):** Structured Markdown with sections
**Tier 3 (subagent):** Consolidated cross-file analysis

After receiving results:
- Highlight critical items from "Issues Found"
- Summarize simplification opportunities
- Distinguish urgent vs. later improvements
- Ask if user wants to address specific findings

## References

- [CLI_REFERENCE.md](references/CLI_REFERENCE.md) - Installation, flags, troubleshooting
- [HOOKS.md](references/HOOKS.md) - Detailed hook documentation and usage
