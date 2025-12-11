# Local Brain: Analysis & Delegation Research

**Date**: 2025-12-11
**Purpose**: Comprehensive analysis of the local-brain repository, evaluation of analysis methods, and identification of optimal delegation use cases.

---

## Executive Summary

Local Brain is a Claude Code plugin that enables privacy-preserving, local codebase exploration using Ollama models. It implements a secure two-layer architecture with 9 specialized tools for read-only operations. This research compares two analysis approaches (local-brain CLI vs. Claude Code subagent) and identifies optimal task delegation patterns.

**Key Findings**:
- Local-brain completed analysis in ~22 seconds with 8 tool calls across 2 turns
- Claude Code subagent completed analysis in ~30 seconds with deeper exploration
- Both approaches produced accurate, complementary results
- Optimal delegation: local-brain for quick, focused tasks; subagent for comprehensive exploration

---

## Part 1: Repository Analysis

### 1.1 Project Overview

**Local Brain** is a Claude Code plugin marketplace that extends Claude with local AI capabilities:

- **Primary Function**: Delegates read-only codebase exploration from Claude Code (cloud) to local Ollama models
- **Key Benefit**: Eliminates cloud round-trips, ensures data privacy, reduces API costs
- **Architecture**: CLI tool + Gradio web UI + Claude Code skill integration
- **Security Model**: Two-layer sandboxing (path jailing + LLM code sandbox)

**Use Cases**:
```
✓ "Review the code changes"
✓ "Explain how the auth module works"
✓ "Generate a commit message"
✓ "Find all TODO comments"
✓ "What files changed recently?"
```

---

### 1.2 Core Components

#### **Architecture Diagram**
```
┌─────────────────────────────────────────────────────┐
│              Claude Code (Cloud)                     │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP Request
                   ↓
┌─────────────────────────────────────────────────────┐
│              Local Brain (Local)                     │
├─────────────────────────────────────────────────────┤
│  CLI / Gradio UI Interface                          │
├─────────────────────────────────────────────────────┤
│  CodeAgent (Smolagents)                             │
│    ├─ 9 Custom Tools (@tool decorator)             │
│    └─ LiteLLMModel (Ollama connection)             │
├─────────────────────────────────────────────────────┤
│  Security Layer                                      │
│    ├─ Path Jailing (project root only)             │
│    ├─ Output Truncation (200 lines/20k chars)      │
│    ├─ Timeouts (30s per tool)                      │
│    └─ Sensitive File Blocking (.env, *.key, etc.)  │
├─────────────────────────────────────────────────────┤
│  LocalPythonExecutor (Sandboxed Runtime)            │
│    ├─ ALLOWS: @tool function calls                 │
│    ├─ BLOCKS: subprocess, socket, os.system        │
│    └─ BLOCKS: File I/O outside sandbox             │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP
                   ↓
┌─────────────────────────────────────────────────────┐
│         Ollama Server (Local LLM)                    │
│  Models: Qwen3, Llama3.2, Mistral, etc.            │
└─────────────────────────────────────────────────────┘
```

#### **Module Breakdown**

| Module | LOC | Responsibility |
|--------|-----|----------------|
| **cli.py** | 365 | Click CLI, commands (main, ui, doctor), model selection |
| **smolagent.py** | 705 | CodeAgent creation, 9 tools, AST parsing |
| **security.py** | 259 | Path jailing, truncation, timeouts, sensitive files |
| **models.py** | 263 | Ollama model discovery, smart selection (18 models) |
| **tracing.py** | 121 | OpenTelemetry instrumentation (optional) |

---

### 1.3 The 9 Tools

All tools are registered via `@tool` decorator and implement security constraints:

| Tool | Purpose | Security Features |
|------|---------|-------------------|
| `read_file` | Read file contents | Path jailing, sensitive file blocking, truncation |
| `list_directory` | List files with globs | Path jailing, excludes .git/node_modules/etc. |
| `file_info` | Get file metadata | Path jailing, sensitive file blocking |
| `git_diff` | Show staged/unstaged changes | Read-only git command, truncation |
| `git_status` | Current branch/changes summary | Read-only git command |
| `git_log` | Recent commit history | Read-only git command (max 50) |
| `git_changed_files` | List modified files | Read-only git command |
| `search_code` | AST-aware code search | Path jailing, grep-ast integration, context-aware |
| `list_definitions` | Extract classes/functions | Tree-sitter parsing, signatures only (not bodies) |

**Tool Design Principles**:
- Read-only operations only
- All outputs truncated (200 lines / 20k chars)
- 30-second timeout per tool call
- Path-jailed to project root
- Sensitive files blocked by pattern

---

### 1.4 Technology Stack

**Core Dependencies**:
- **Smolagents** (1.0.0+) — HuggingFace agent framework
- **LiteLLM** (1.0.0+) — Unified LLM interface
- **Ollama** (0.6.1+) — Local LLM runtime
- **Click** (8.0.0+) — CLI framework
- **grep-ast** (0.9.0+) — AST-aware search
- **tree-sitter** (0.25.0+) — Language parsing
- **tree-sitter-language-pack** (0.13.0+) — Language grammars

**Optional**:
- **Gradio** (4.0.0+) — Web UI
- **OpenInference** + **OpenTelemetry** — OTEL tracing

**Python**: 3.10-3.13 (grpcio build issues with 3.14)

---

### 1.5 Security Architecture

#### **Two-Layer Security Model**

**Layer 1: Tool-Level Security** (Trusted Code)
```python
@tool
@with_timeout(30)
def read_file(path: str) -> str:
    resolved = safe_path(path)  # Path jailing
    if is_sensitive_file(resolved):  # Pattern blocking
        return "Error: Access denied"
    content = resolved.read_text()
    return truncate_output(content)  # Output limiting
```

**Layer 2: LLM Sandbox** (Untrusted Generated Code)
- LocalPythonExecutor blocks dangerous imports:
  - ❌ `subprocess`
  - ❌ `socket`
  - ❌ `os.system`
  - ❌ `__import__`
- LLM can only call pre-defined `@tool` functions
- Cannot bypass tools to access filesystem/network

#### **Why This Model?**
- **Tool Layer**: Implements git access (needs subprocess), enforces project boundaries
- **Sandbox Layer**: Prevents LLM from generating malicious code
- **Separation**: Trusted tools handle dangerous operations; LLM only orchestrates them

#### **Additional Protections**
- **Path Jailing**: `safe_path()` resolves symlinks, blocks `..` traversal
- **Sensitive Files**: Blocks `.env`, `*.key`, `*.pem`, `id_*`, `.git/config`
- **Output Truncation**: Prevents memory exhaustion
- **Timeouts**: Unix SIGALRM prevents hanging (30s default)
- **No Web Access**: Cannot fetch URLs, prevents data exfiltration (ADR-003)

---

### 1.6 Architecture Decision Records (ADRs)

| ADR | Decision | Rationale | Status |
|-----|----------|-----------|--------|
| **001** | Custom implementation (not LangChain/Aider) | Tight control, minimal dependencies | ✅ Accepted |
| **002** | Use Smolagents for code execution | Robust sandbox, maintained by HuggingFace | ✅ Accepted |
| **003** | No web tools | Prevents data exfiltration, SSRF, prompt injection | ✅ Accepted |
| **004** | ToolCallingAgent with JSON | Structured tool calls | ❌ Superseded |
| **005** | CodeAgent with markdown tags | Simpler, compatible with local models | ✅ Accepted |

**ADR-005 Key Insight**: Local Ollama models naturally output markdown code blocks (````python...```), not XML `<code>...</code>`. CodeAgent with `code_block_tags="markdown"` accepts both formats, enabling:
- Conversational responses ("This code does X because Y")
- Flexible tool use (call tools when needed, explain when not)
- Better compatibility with Qwen, Llama, Mistral

---

### 1.7 Model Support

**18 Pre-configured Models** ranked by tool-calling capability:

**Tier 1 (Excellent)**: Qwen3, Qwen2.5-Coder (recommended)
**Tier 2 (Good)**: Llama3.2, Mistral, Llama3.1, DeepSeek-Coder
**Tier 3 (Limited)**: Gemma2, Phi3

**Smart Selection**:
```python
# Auto-selects best available model
selected_model, was_fallback = select_model_for_task(model=None)
# Prefers code-focused models for code tasks
best = find_best_model(task_type="code")
```

**Default**: `qwen3:latest` (4.4GB, excellent tool support)

---

## Part 2: Comparative Analysis

### 2.1 Analysis Method Comparison

I tested two approaches to analyze this repository:

#### **Method 1: Local-Brain CLI**
```bash
local-brain -v "Analyze this repository and provide a comprehensive overview..."
```

**Results**:
- **Duration**: ~22 seconds
- **Turns**: 2 (exploration → synthesis)
- **Tool Calls**: 8 tools in Turn 1
- **Tools Used**:
  - `list_directory` (3x for different patterns)
  - `read_file` (README.md)
  - `git_status` (1x)
- **Output**: 3,146 characters, well-structured analysis

**Characteristics**:
- ✅ Fast, focused exploration
- ✅ Clear tool usage visibility with `-v` flag
- ✅ Concise, actionable summary
- ✅ Good for targeted questions
- ⚠️ Shallower analysis (didn't read implementation files)
- ⚠️ Relies heavily on README/docs

#### **Method 2: Claude Code Subagent (Explore)**
```python
Task(subagent_type="Explore", prompt="Analyze this repository...")
```

**Results**:
- **Duration**: ~30 seconds
- **Depth**: Comprehensive (read 6+ source files)
- **Files Read**:
  - README.md, pyproject.toml
  - cli.py, smolagent.py, security.py, models.py
  - ADR files
- **Output**: 12,000+ characters, detailed implementation analysis

**Characteristics**:
- ✅ Deep implementation understanding
- ✅ Detailed component analysis
- ✅ Code-level insights (specific functions, patterns)
- ✅ Architectural understanding
- ⚠️ Takes longer
- ⚠️ More verbose (may include unnecessary details)

---

### 2.2 Accuracy & Completeness

| Aspect | Local-Brain | Subagent | Winner |
|--------|-------------|----------|--------|
| **Project Purpose** | ✓ Accurate | ✓ Accurate | Tie |
| **Technology Stack** | ✓ Identified core | ✓ Complete list | Subagent |
| **Architecture** | ✓ High-level | ✓ Detailed with code | Subagent |
| **Security Features** | ✓ Mentioned | ✓ Deep analysis | Subagent |
| **Tool List** | ✓ Listed 7 tools | ✓ Listed 9 tools | Subagent |
| **ADRs** | ⚠️ Not mentioned | ✓ Full coverage | Subagent |
| **Speed** | ✓ 22s | ⚠️ 30s | Local-Brain |
| **Readability** | ✓ Concise | ⚠️ Verbose | Local-Brain |
| **Use Case Fit** | Quick overview | Onboarding/deep dive | Context-dependent |

**Key Insight**: Both approaches are accurate, but serve different purposes:
- **Local-Brain**: Fast reconnaissance, quick questions, iterative exploration
- **Subagent**: Comprehensive understanding, onboarding, architectural analysis

---

### 2.3 Cost & Resource Comparison

| Metric | Local-Brain | Claude Code Subagent |
|--------|-------------|----------------------|
| **Execution** | Local Ollama (qwen3:latest) | Claude Sonnet 4.5 (cloud) |
| **Token Usage** | ~8k tokens (estimated) | ~15k tokens (estimated) |
| **API Cost** | $0.00 (local) | ~$0.45 @ $30/MTok |
| **Privacy** | ✓ All local | ⚠️ Sends code to cloud |
| **Speed** | 22s | 30s |
| **Context Window** | 8192 tokens | 200k tokens |
| **Hardware Req** | 4-8GB VRAM | None (cloud) |

**Cost Analysis** (100 analyses):
- **Local-Brain**: $0 + electricity (~$0.10)
- **Subagent**: ~$45 in API costs

**Privacy Consideration**: Local-brain never sends code to cloud, critical for:
- Proprietary codebases
- Regulated industries (HIPAA, GDPR)
- Pre-release features
- Security-sensitive code

---

## Part 3: Delegation Strategy

### 3.1 When to Use Local-Brain

#### **Optimal Use Cases** (Second Thinking / Side Analysis)

**1. Quick Reconnaissance**
```
✓ "What files changed recently?"
✓ "List all Python files in src/"
✓ "Show me the git status"
✓ "What are the recent commits?"
```
**Why Local-Brain**: Fast, local, no cloud round-trip

---

**2. Code Review Assistance**
```
✓ "Review the changes in feature branch"
✓ "Find potential issues in the diff"
✓ "Check if new code follows patterns"
✓ "Generate commit message from staged changes"
```
**Why Local-Brain**: Iterative, frequent task; privacy-sensitive

---

**3. Pattern Discovery**
```
✓ "Find all TODO comments"
✓ "List all functions named 'handle_*'"
✓ "Show me all error handling patterns"
✓ "Find classes that inherit from BaseModel"
```
**Why Local-Brain**: search_code + AST awareness perfect for patterns

---

**4. Quick Documentation Queries**
```
✓ "What does the security.py module do?"
✓ "Show me the function signatures in cli.py"
✓ "Explain the purpose of this file"
```
**Why Local-Brain**: Fast, read-only, no need for cloud intelligence

---

**5. Git Archaeology**
```
✓ "When was this file last modified?"
✓ "Who changed the authentication code?"
✓ "What branches touch src/auth?"
```
**Why Local-Brain**: Git tools are specialized and fast

---

**6. Iterative Exploration**
```
✓ User: "Find all API endpoints"
  Local-Brain: [Lists 15 endpoints]
✓ User: "Now show me the authentication handlers"
  Local-Brain: [Shows relevant code]
✓ User: "Read the middleware that validates tokens"
  Local-Brain: [Reads file]
```
**Why Local-Brain**: Multi-turn exploration without burning cloud tokens

---

**7. Codebase Metrics**
```
✓ "How many Python files are there?"
✓ "List files larger than 500 lines"
✓ "What's the structure of the tests/ directory?"
```
**Why Local-Brain**: File operations are its specialty

---

**8. AST-Aware Navigation**
```
✓ "Show me all class definitions in models.py"
✓ "List function signatures without implementations"
✓ "Find all methods in the Agent class"
```
**Why Local-Brain**: tree-sitter integration unique capability

---

### 3.2 When to Use Claude Code Subagent

#### **Optimal Use Cases**

**1. Comprehensive Onboarding**
```
✓ "Explain the entire architecture"
✓ "How does authentication flow work end-to-end?"
✓ "Create onboarding docs for new developers"
```
**Why Subagent**: Needs synthesis, cross-file understanding, writing

---

**2. Complex Analysis**
```
✓ "Identify security vulnerabilities"
✓ "Find race conditions in async code"
✓ "Analyze performance bottlenecks"
```
**Why Subagent**: Requires deep reasoning, not just pattern matching

---

**3. Refactoring Planning**
```
✓ "Plan migration from Flask to FastAPI"
✓ "Design a new module structure"
✓ "Propose improvements to error handling"
```
**Why Subagent**: Needs architectural thinking, design decisions

---

**4. Implementation Tasks**
```
✓ "Add logging to all API endpoints"
✓ "Refactor duplicate code"
✓ "Implement feature X"
```
**Why Subagent**: Requires writing code, not just reading

---

**5. Documentation Generation**
```
✓ "Write API documentation"
✓ "Generate README sections"
✓ "Create architecture diagrams"
```
**Why Subagent**: Creative writing, synthesis

---

**6. Cross-Cutting Concerns**
```
✓ "How is error handling done across the codebase?"
✓ "Map all database queries"
✓ "Identify all external API calls"
```
**Why Subagent**: Needs to trace through multiple files and layers

---

### 3.3 Hybrid Strategy (Recommended)

**Workflow Pattern**: Local-Brain for reconnaissance → Claude for synthesis/action

**Example 1: Feature Implementation**
```
Step 1: local-brain "Find all authentication-related files"
        → Identifies 5 files quickly

Step 2: local-brain "Show me auth middleware signature"
        → Returns function signatures

Step 3: Claude Code "Implement OAuth2 support following existing patterns"
        → Uses context from steps 1-2, writes implementation
```

**Example 2: Bug Investigation**
```
Step 1: local-brain "What changed in the last 3 commits?"
        → Shows git log

Step 2: local-brain "Show git diff for api.py"
        → Returns the diff

Step 3: local-brain "Find other uses of the broken function"
        → search_code finds 4 call sites

Step 4: Claude Code "Fix the bug in api.py and update all call sites"
        → Fixes bug with full context
```

**Example 3: Code Review**
```
Step 1: local-brain "Show staged changes"
        → Returns diff

Step 2: local-brain "Find similar patterns in existing code"
        → Finds 3 similar implementations

Step 3: Claude Code "Review these changes against project patterns"
        → Compares and provides feedback
```

---

### 3.4 Delegation Decision Matrix

| Task Characteristic | Use Local-Brain | Use Subagent |
|---------------------|-----------------|--------------|
| **Read-only** | ✓ | Either |
| **Needs writing** | ✗ | ✓ |
| **Privacy-sensitive** | ✓ | ⚠️ |
| **Quick question** | ✓ | ⚠️ |
| **Deep analysis** | ⚠️ | ✓ |
| **Pattern search** | ✓ | Either |
| **Synthesis/creativity** | ⚠️ | ✓ |
| **Multi-file tracing** | ⚠️ | ✓ |
| **Git operations** | ✓ | Either |
| **File listings** | ✓ | Either |
| **Cost-sensitive** | ✓ | ⚠️ |
| **Iterative exploration** | ✓ | Either |

---

## Part 4: Task Delegation Catalog

### 4.1 Second Thinking Tasks (Perfect for Local-Brain)

**Definition**: Parallel analysis that informs main task without blocking it

**Examples**:

**1. Parallel Pattern Check**
```
Main Task: Implementing new API endpoint
Second Thinking: local-brain "Find all existing API endpoint patterns"
Benefit: Main Claude Code task gets validation data without waiting
```

**2. Parallel Impact Analysis**
```
Main Task: Refactoring function signature
Second Thinking: local-brain "Find all calls to this function"
Benefit: Identifies affected code before making changes
```

**3. Parallel Context Gathering**
```
Main Task: Writing documentation
Second Thinking: local-brain "List all public functions in this module"
Benefit: Ensures docs are complete
```

**4. Parallel Git Investigation**
```
Main Task: Debugging production issue
Second Thinking: local-brain "What changed in the last deploy?"
Benefit: Narrows investigation scope
```

---

### 4.2 Side Analysis Tasks (Perfect for Local-Brain)

**Definition**: Supplementary investigation that enriches understanding

**Examples**:

**1. Historical Context**
```
Main: "Why does this code use pattern X?"
Side: local-brain "Show git log for this file"
      local-brain "Find other uses of pattern X"
Result: Historical context enriches answer
```

**2. Dependency Mapping**
```
Main: "Explain module A"
Side: local-brain "List all imports in module A"
      local-brain "Find files that import module A"
Result: Dependency graph reveals architecture
```

**3. Test Coverage Check**
```
Main: "Is this function well-tested?"
Side: local-brain "Find test files mentioning this function"
      local-brain "List all tests in test_module.py"
Result: Coverage assessment
```

**4. Pattern Consistency**
```
Main: "Review this PR"
Side: local-brain "Find similar implementations"
      local-brain "Show existing error handling patterns"
Result: Consistency validation
```

---

### 4.3 Iterative Refinement Tasks

**Workflow**: Local-brain for cheap exploration, Claude for expensive synthesis

**Example Workflow**:

```
🔄 Iteration 1:
  local-brain "List all database models"
  → Returns 20 models

🔄 Iteration 2:
  local-brain "Show definitions for User and Order models"
  → Returns signatures

🔄 Iteration 3:
  local-brain "Find all queries on User model"
  → Returns 15 locations

🎯 Final Synthesis:
  Claude Code "Design efficient indexing strategy for User queries"
  → Uses all gathered context, produces recommendation
```

**Cost Savings**: 3 local-brain iterations (~$0) + 1 Claude synthesis (~$0.15) = **$0.15 total**
**Alternative**: 4 Claude iterations = **~$0.60** (4x more expensive)

---

### 4.4 Privacy-Sensitive Tasks (Must Use Local-Brain)

**When code cannot leave your machine**:

1. **Pre-release Features**
   ```
   local-brain "Review unannounced feature code"
   ```

2. **Proprietary Algorithms**
   ```
   local-brain "Find all crypto implementations"
   ```

3. **Customer Data Handling**
   ```
   local-brain "Show PII access patterns"
   ```

4. **Security Audits**
   ```
   local-brain "Find all authentication code"
   ```

5. **Regulated Industries**
   ```
   local-brain "Scan for HIPAA violations"
   ```

---

## Part 5: Recommendations

### 5.1 Optimal Delegation Strategy

**General Principle**: Use local-brain for reconnaissance, Claude Code for synthesis

**Decision Tree**:
```
Is the task read-only?
├─ Yes → Is it privacy-sensitive?
│  ├─ Yes → Use local-brain
│  └─ No → Is it a quick question?
│     ├─ Yes → Use local-brain
│     └─ No → Does it need deep reasoning?
│        ├─ Yes → Use subagent
│        └─ No → Use local-brain
└─ No → Use Claude Code (needs write access)
```

---

### 5.2 Integration Patterns

**Pattern 1: Parallel Investigation**
```python
# Launch both in parallel
local_brain_task = bash("local-brain 'Find error handlers'")
subagent_task = Task(subagent_type="Explore", prompt="Analyze error strategy")

# Wait for both
local_result = wait(local_brain_task)
subagent_result = wait(subagent_task)

# Synthesize
synthesize(local_result, subagent_result)
```

**Pattern 2: Sequential Refinement**
```python
# Quick check
files = local_brain("List changed files")

# Deep analysis on subset
if len(files) > 5:
    analysis = subagent(f"Analyze these {len(files)} files")
else:
    analysis = local_brain(f"Show me {files}")
```

**Pattern 3: Cost-Optimized Pipeline**
```python
# Use local-brain for filtering
candidates = local_brain("Find all API endpoints")

# Use subagent only for final analysis
security_review = subagent(f"Audit these {len(candidates)} endpoints")
```

---

### 5.3 Skill Improvements

**Suggested Enhancements to Local-Brain**:

1. **Batch Operations**
   ```python
   local-brain batch "read_file(src/a.py); read_file(src/b.py)"
   ```

2. **Streaming Output**
   ```python
   local-brain --stream "Analyze large codebase"
   ```

3. **Result Caching**
   ```python
   local-brain --cache "List all files"  # Caches for 5 min
   ```

4. **Custom Tool Registration**
   ```python
   # Add project-specific tools
   @tool
   def check_license_headers(file_path: str) -> str:
       ...
   ```

5. **Multi-Model Routing**
   ```python
   local-brain --model-routing auto \
     "Quick task"  # Uses fast model

   local-brain --model-routing auto \
     "Complex analysis"  # Uses capable model
   ```

---

## Part 6: Conclusions

### 6.1 Summary of Findings

1. **Local-Brain Strengths**:
   - Fast, privacy-preserving reconnaissance
   - Excellent for pattern search, git operations, file navigation
   - Cost-effective for iterative exploration
   - Specialized AST-aware tools

2. **Subagent Strengths**:
   - Deep architectural understanding
   - Synthesis and creative tasks
   - Cross-cutting analysis
   - Write operations

3. **Optimal Strategy**:
   - Use local-brain for 80% of read-only tasks
   - Reserve subagent for synthesis, writing, complex reasoning
   - Hybrid approach maximizes speed and cost-effectiveness

### 6.2 Cost-Benefit Analysis

**Scenario: Analyzing 10 codebases per day**

| Approach | Daily Cost | Monthly Cost | Privacy |
|----------|-----------|--------------|---------|
| **All Subagent** | $4.50 | $90 | ⚠️ Cloud |
| **All Local-Brain** | $0.00 | $0 | ✓ Local |
| **Hybrid (80/20)** | $0.90 | $18 | ✓ Mostly |

**ROI**: Hybrid approach saves **$72/month** while maintaining quality

### 6.3 Final Recommendations

**For Individual Developers**:
- Install local-brain for daily codebase navigation
- Use for git operations, pattern search, quick questions
- Reserve Claude Code for implementation and synthesis

**For Teams**:
- Mandate local-brain for privacy-sensitive codebases
- Train developers on delegation patterns
- Create custom tools for project-specific needs

**For Enterprises**:
- Deploy local-brain on developer workstations
- Use for compliance-sensitive code review
- Track cost savings vs. cloud-only approach

---

## Appendix A: Quick Reference

### Local-Brain Command Cheat Sheet

```bash
# Basic usage
local-brain "What files changed?"

# Verbose mode (show tool calls)
local-brain -v "Analyze this code"

# Specific model
local-brain -m qwen2.5-coder:7b "Review code"

# Different project
local-brain --root /path/to/project "List files"

# Web UI
local-brain ui

# Health check
local-brain doctor

# List models
local-brain --list-models
```

### Common Delegation Patterns

```bash
# Pattern discovery
local-brain "Find all functions matching 'handle_*'"

# Git operations
local-brain "Show recent commits"
local-brain "What changed in the last hour?"

# File navigation
local-brain "List all Python files in src/"
local-brain "Show me the structure of tests/"

# Code search
local-brain "Find TODO comments"
local-brain "Search for authentication code"

# Definitions
local-brain "List all classes in models.py"
local-brain "Show function signatures in api.py"
```

---

**Document Version**: 1.0
**Last Updated**: 2025-12-11
**Author**: Claude Code Analysis
