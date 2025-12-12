# Local Brain: Delegation Research

**Date**: 2025-12-11 | **Status**: Active

## Summary

Local Brain delegates read-only codebase exploration from Claude Code (cloud) to local Ollama models. This research identifies optimal task delegation patterns between local-brain and Claude Code.

**Key Finding**: Use local-brain for 80% of read-only tasks (reconnaissance, git ops, pattern search). Reserve Claude Code for synthesis, writing, and complex reasoning.

---

## Model Recommendations

Based on testing 7 Ollama models (see [004-model-performance-comparison.md](./004-model-performance-comparison.md)):

| Model | Size | Tier | Use Case |
|-------|------|------|----------|
| **qwen3:latest** | 5.2 GB | ✅ Tier 1 | Default, best all-around |
| **qwen2.5:3b** | 1.9 GB | ✅ Tier 1 | Resource-constrained |
| ministral-3:latest | 6.0 GB | ⚠️ Tier 2 | Basic tasks only |
| qwen2.5-coder:* | 1.9-4.7 GB | ❌ Tier 3 | DO NOT USE (broken tool calling) |
| deepseek-r1:latest | 5.2 GB | ❌ Tier 3 | CANNOT USE (no tool support) |
| llama3.2:1b | 1.3 GB | ❌ Tier 3 | DO NOT USE (hallucinations) |

**Critical**: Only 3 of 7 models (43%) can reliably call tools. "Coder" variants are broken with Smolagents.

---

## When to Use Local-Brain

### ✅ Optimal Use Cases

| Task Type | Examples |
|-----------|----------|
| **Quick Reconnaissance** | "What files changed?", "Show git status", "List Python files" |
| **Code Review** | "Review changes", "Generate commit message", "Find issues in diff" |
| **Pattern Discovery** | "Find all TODOs", "List functions named 'handle_*'" |
| **Git Archaeology** | "Show recent commits", "Who changed this file?" |
| **AST Navigation** | "List class definitions", "Show function signatures" |
| **Privacy-Sensitive** | Pre-release features, proprietary code, regulated industries |

### ❌ Use Claude Code Instead

| Task Type | Why |
|-----------|-----|
| **Writing/editing files** | Local-brain is read-only |
| **Complex synthesis** | Needs cross-file understanding |
| **Refactoring planning** | Requires architectural thinking |
| **Multi-step analysis** | Local models score 2-3/5 on reasoning |
| **Documentation generation** | Creative writing tasks |

---

## Delegation Decision Tree

```
Is the task read-only?
├─ No → Use Claude Code
└─ Yes → Is it privacy-sensitive?
   ├─ Yes → Use local-brain
   └─ No → Quick question or pattern search?
      ├─ Yes → Use local-brain
      └─ No → Needs deep reasoning?
         ├─ Yes → Use Claude Code
         └─ No → Use local-brain
```

---

## Hybrid Workflow (Recommended)

**Pattern**: Local-brain for reconnaissance → Claude Code for synthesis

**Example: Bug Investigation**
```
1. local-brain "What changed in the last 3 commits?"  → git log
2. local-brain "Show git diff for api.py"            → diff output
3. local-brain "Find other uses of broken function"  → 4 call sites
4. Claude Code "Fix the bug and update call sites"   → implementation
```

**Cost Savings**: 3 local iterations ($0) + 1 Claude synthesis ($0.15) = **$0.15**
vs. 4 Claude iterations = **$0.60** (4x more expensive)

---

## Cost & Performance Comparison

| Metric | Local-Brain | Claude Code |
|--------|-------------|-------------|
| **Speed** | ~22s | ~30s |
| **Cost** | $0.00 | ~$0.45/analysis |
| **Privacy** | ✅ All local | ⚠️ Cloud |
| **Context Window** | 8k tokens | 200k tokens |
| **Multi-step Reasoning** | ⚠️ 2-3/5 | ✅ 5/5 |

**Monthly Savings** (10 analyses/day, 80/20 hybrid): **$72/month** vs all-cloud

---

## Architecture Overview

```
Claude Code (Cloud)
       ↓
Local Brain (Local)
  ├─ CLI Interface
  ├─ CodeAgent (Smolagents) → 9 Tools
  ├─ Security Layer (path jailing, truncation, timeouts)
  └─ LocalPythonExecutor (sandbox)
       ↓
Ollama Server (qwen3:latest)
```

**9 Tools**: `read_file`, `list_directory`, `file_info`, `git_diff`, `git_status`, `git_log`, `git_changed_files`, `search_code`, `list_definitions`

---

## Key Limitations

1. **No write operations** - read-only by design
2. **Multi-step reasoning weak** - best models score 3/5
3. **No self-awareness** - models don't decline inappropriate tasks
4. **Model compatibility varies** - must verify tool-calling support

---

**Version**: 1.1 | **Last Updated**: 2025-12-11
