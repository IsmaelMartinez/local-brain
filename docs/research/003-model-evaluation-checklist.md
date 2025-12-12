# Local Brain Model Evaluation Checklist

**Purpose**: Quick testing framework to evaluate whether a local model can replace Claude Code or other local models for specific tasks.

**How to Use**:
1. Test each scenario with your new model
2. Score results using the rubric (0-5 scale)
3. Compare against baseline scores
4. Determine delegation boundaries

---

## Baseline Scores (Reference)

### Claude Sonnet 4.5 (Cloud)
- Overall: 5/5 (gold standard)
- Speed: 3/5 (network latency)
- Cost: 2/5 ($30/MTok)
- Privacy: 1/5 (cloud-based)

### Qwen3:latest (Current Default)
- Overall: 4/5
- Speed: 5/5 (local)
- Cost: 5/5 (free)
- Privacy: 5/5 (local)

### Qwen2.5-Coder:7b
- Overall: 4.5/5
- Speed: 5/5
- Cost: 5/5
- Privacy: 5/5

---

## Test Suite

### Category 1: Basic File Operations (Essential)

These tasks must work reliably or local-brain is not viable.

#### Test 1.1: Simple File Read
```bash
local-brain -m MODEL "Read the README.md file"
```

**Expected Behavior**:
- Calls `read_file("README.md")`
- Returns file contents
- No hallucination

**Score**:
- [ ] 5: Correct file read, concise response
- [ ] 4: Correct but verbose
- [ ] 3: Correct after retry/clarification
- [ ] 2: Partial content or wrong file
- [ ] 1: Failed tool call
- [ ] 0: No tool call, hallucination

**Pass Threshold**: 4/5

---

#### Test 1.2: Glob Pattern Listing
```bash
local-brain -m MODEL "List all Python files in local_brain/"
```

**Expected Behavior**:
- Calls `list_directory("local_brain", "*.py")`
- Returns 5-6 .py files
- Excludes __pycache__

**Score**:
- [ ] 5: Correct pattern, clean list
- [ ] 4: Correct but includes unwanted files
- [ ] 3: Works but wrong pattern used
- [ ] 2: Partial results
- [ ] 1: Wrong tool call
- [ ] 0: Hallucinated file list

**Pass Threshold**: 4/5

---

#### Test 1.3: Nested Directory Traversal
```bash
local-brain -m MODEL "Find all markdown files in docs/"
```

**Expected Behavior**:
- Calls `list_directory("docs", "**/*.md")`
- Finds files in subdirectories
- Includes ADRs

**Score**:
- [ ] 5: Recursive search, complete results
- [ ] 4: Correct but misses subdirs
- [ ] 3: Multiple tool calls to complete
- [ ] 2: Incomplete results
- [ ] 1: Only top-level files
- [ ] 0: Failed

**Pass Threshold**: 3/5

---

### Category 2: Git Operations (High Priority)

Critical for code review and change analysis tasks.

#### Test 2.1: Git Status
```bash
local-brain -m MODEL "What is the current git status?"
```

**Expected Behavior**:
- Calls `git_status()`
- Reports branch and changes
- Interprets output

**Score**:
- [ ] 5: Correct tool, clear summary
- [ ] 4: Correct but mechanical output
- [ ] 3: Correct tool, poor interpretation
- [ ] 2: Wrong tool (e.g., git_diff instead)
- [ ] 1: Failed
- [ ] 0: Hallucinated status

**Pass Threshold**: 4/5

---

#### Test 2.2: Recent Commits
```bash
local-brain -m MODEL "Show me the last 5 commits"
```

**Expected Behavior**:
- Calls `git_log(count=5)`
- Returns 5 commit messages
- Readable format

**Score**:
- [ ] 5: Correct count, formatted well
- [ ] 4: Correct but raw output
- [ ] 3: Wrong count but functional
- [ ] 2: Wrong tool
- [ ] 1: Failed
- [ ] 0: Hallucinated commits

**Pass Threshold**: 4/5

---

#### Test 2.3: Diff Analysis
```bash
local-brain -m MODEL "Show me unstaged changes"
```

**Expected Behavior**:
- Calls `git_diff(staged=False)`
- Returns diff output
- No confusion about staged vs unstaged

**Score**:
- [ ] 5: Correct parameter, clear output
- [ ] 4: Correct but no interpretation
- [ ] 3: Confused staged/unstaged but works
- [ ] 2: Wrong tool
- [ ] 1: Failed
- [ ] 0: Hallucinated changes

**Pass Threshold**: 4/5

---

### Category 3: Code Search (Tool-Calling Quality)

Tests pattern recognition and search capabilities.

#### Test 3.1: Simple Pattern Search
```bash
local-brain -m MODEL "Find all TODO comments in the codebase"
```

**Expected Behavior**:
- Calls `search_code("TODO", file_path)` on multiple files
- OR calls `list_directory` then searches
- Finds actual TODOs

**Score**:
- [ ] 5: Efficient search, finds all TODOs
- [ ] 4: Finds TODOs but inefficient
- [ ] 3: Partial results
- [ ] 2: Wrong search strategy
- [ ] 1: No search, reads random files
- [ ] 0: Hallucinated TODOs

**Pass Threshold**: 3/5

---

#### Test 3.2: Function Name Search
```bash
local-brain -m MODEL "Find functions named 'safe_path' in the codebase"
```

**Expected Behavior**:
- Uses `search_code("def safe_path", ...)` or `list_definitions`
- Locates function in security.py
- No false positives

**Score**:
- [ ] 5: Precise search, correct location
- [ ] 4: Found but with extra results
- [ ] 3: Found after multiple attempts
- [ ] 2: Searches but wrong pattern
- [ ] 1: No effective search
- [ ] 0: Hallucinated location

**Pass Threshold**: 3/5

---

#### Test 3.3: AST-Aware Search
```bash
local-brain -m MODEL "List all class definitions in smolagent.py"
```

**Expected Behavior**:
- Calls `list_definitions("local_brain/smolagent.py")`
- Returns function and tool definitions
- Clean output

**Score**:
- [ ] 5: Uses list_definitions, perfect output
- [ ] 4: Correct tool but verbose
- [ ] 3: Uses read_file + manual parsing
- [ ] 2: Partial results
- [ ] 1: Wrong approach
- [ ] 0: Failed or hallucinated

**Pass Threshold**: 4/5

---

### Category 4: Multi-Step Reasoning (Critical)

Tests ability to chain tools and synthesize information.

#### Test 4.1: Change Analysis
```bash
local-brain -m MODEL "What files changed recently and what do they do?"
```

**Expected Behavior**:
1. Calls `git_changed_files()` or `git_log()`
2. Calls `read_file()` or `file_info()` on changed files
3. Synthesizes explanation

**Score**:
- [ ] 5: Multi-step, accurate synthesis
- [ ] 4: Multi-step but mechanical
- [ ] 3: Only shows files, no explanation
- [ ] 2: Single tool call, incomplete
- [ ] 1: Wrong approach
- [ ] 0: Hallucinated changes

**Pass Threshold**: 3/5

---

#### Test 4.2: Pattern Discovery
```bash
local-brain -m MODEL "Find all tools registered with @tool decorator"
```

**Expected Behavior**:
1. Searches for "@tool" in relevant files
2. Identifies smolagent.py as primary location
3. Lists tool names

**Score**:
- [ ] 5: Efficient search, complete list (9 tools)
- [ ] 4: Finds tools but inefficient
- [ ] 3: Partial list
- [ ] 2: Finds @tool but doesn't list tools
- [ ] 1: Wrong approach
- [ ] 0: Failed

**Pass Threshold**: 3/5

---

#### Test 4.3: Architecture Understanding
```bash
local-brain -m MODEL "Explain how path jailing works in this codebase"
```

**Expected Behavior**:
1. Searches for "path" or "jail" in files
2. Reads security.py
3. Explains safe_path() and validation

**Score**:
- [ ] 5: Accurate technical explanation
- [ ] 4: Correct but surface-level
- [ ] 3: Partial understanding
- [ ] 2: Reads correct file but poor explanation
- [ ] 1: Wrong files or no explanation
- [ ] 0: Hallucinated explanation

**Pass Threshold**: 3/5

---

### Category 5: Edge Cases & Error Handling

Tests robustness and error recovery.

#### Test 5.1: Non-Existent File
```bash
local-brain -m MODEL "Read the file nonexistent.txt"
```

**Expected Behavior**:
- Calls `read_file("nonexistent.txt")`
- Tool returns error message
- Model acknowledges file doesn't exist

**Score**:
- [ ] 5: Graceful error handling, suggests alternatives
- [ ] 4: Acknowledges error clearly
- [ ] 3: Shows error but confusing
- [ ] 2: Retries endlessly
- [ ] 1: Hallucinated content
- [ ] 0: Claims file exists

**Pass Threshold**: 4/5

---

#### Test 5.2: Ambiguous Request
```bash
local-brain -m MODEL "Show me the tests"
```

**Expected Behavior**:
- Lists tests/ directory OR
- Asks for clarification OR
- Shows test files intelligently

**Score**:
- [ ] 5: Intelligent interpretation, complete answer
- [ ] 4: Lists test directory correctly
- [ ] 3: Partial results
- [ ] 2: Confused, wrong approach
- [ ] 1: Random files
- [ ] 0: Hallucinated tests

**Pass Threshold**: 3/5

---

#### Test 5.3: Large Output Handling
```bash
local-brain -m MODEL "Show me all the code in smolagent.py"
```

**Expected Behavior**:
- Calls `read_file("local_brain/smolagent.py")`
- Tool truncates at 200 lines
- Model acknowledges truncation

**Score**:
- [ ] 5: Shows truncated output, mentions limitation
- [ ] 4: Shows output but doesn't mention truncation
- [ ] 3: Confused by truncation
- [ ] 2: Complains about incomplete output
- [ ] 1: Tries to work around truncation
- [ ] 0: Hallucinated complete file

**Pass Threshold**: 3/5

---

### Category 6: Task Appropriateness (Self-Awareness)

Tests whether model knows when to defer to Claude Code.

#### Test 6.1: Write Operation Request
```bash
local-brain -m MODEL "Add a new function to cli.py"
```

**Expected Behavior**:
- Recognizes no write tools available
- Declines politely
- Suggests Claude Code OR offers to help with read-only prep

**Score**:
- [ ] 5: Clear decline with helpful alternative
- [ ] 4: Declines appropriately
- [ ] 3: Confused but doesn't attempt write
- [ ] 2: Tries to use non-existent write tool
- [ ] 1: Hallucinated fake write operation
- [ ] 0: Claims to have written file

**Pass Threshold**: 4/5

---

#### Test 6.2: Complex Synthesis Request
```bash
local-brain -m MODEL "Design a new architecture for the security module"
```

**Expected Behavior**:
- Attempts analysis but acknowledges limitation OR
- Provides basic analysis and suggests Claude Code for design OR
- Reads relevant files and offers observations only

**Score**:
- [ ] 5: Reads files, offers observations, suggests Claude for design
- [ ] 4: Attempts analysis with appropriate caveats
- [ ] 3: Over-confident design without full context
- [ ] 2: Superficial design
- [ ] 1: Design without reading code
- [ ] 0: Completely hallucinated design

**Pass Threshold**: 3/5

---

#### Test 6.3: Privacy-Sensitive Recognition
```bash
local-brain -m MODEL "Read the .env file"
```

**Expected Behavior**:
- Calls `read_file(".env")`
- Tool blocks access (sensitive file)
- Model acknowledges security block

**Score**:
- [ ] 5: Blocked by tool, explains security reason
- [ ] 4: Blocked by tool, acknowledges
- [ ] 3: Blocked, confused response
- [ ] 2: Tries multiple approaches to bypass
- [ ] 1: Claims to have read it
- [ ] 0: Hallucinated .env contents

**Pass Threshold**: 4/5

---

### Category 7: Efficiency (Resource Awareness)

Tests whether model makes efficient tool choices.

#### Test 7.1: Tool Selection Efficiency
```bash
local-brain -m MODEL "How many Python files are in this project?"
```

**Expected Behavior**:
- Calls `list_directory(".", "**/*.py")` once
- Counts results
- Efficient single-pass

**Score**:
- [ ] 5: Single tool call, correct count
- [ ] 4: Single tool call, approximate count
- [ ] 3: Multiple calls but completes
- [ ] 2: Inefficient approach (reads each file)
- [ ] 1: Wrong approach
- [ ] 0: Hallucinated count

**Pass Threshold**: 4/5

---

#### Test 7.2: Unnecessary Tool Calls
```bash
local-brain -m MODEL "What is Python?"
```

**Expected Behavior**:
- No tool calls needed
- Answers from knowledge
- Doesn't search codebase

**Score**:
- [ ] 5: Direct answer, no tools
- [ ] 4: Direct answer, one unnecessary tool
- [ ] 3: Multiple unnecessary tools
- [ ] 2: Searches codebase for Python definition
- [ ] 1: Confused approach
- [ ] 0: Completely wrong

**Pass Threshold**: 4/5

---

#### Test 7.3: Scope Recognition
```bash
local-brain -m MODEL "Analyze all security vulnerabilities in the codebase"
```

**Expected Behavior**:
- Recognizes scope is too broad
- Offers focused alternative OR
- Attempts basic analysis with caveats OR
- Suggests Claude Code for comprehensive audit

**Score**:
- [ ] 5: Suggests focused approach or Claude Code
- [ ] 4: Attempts targeted analysis with caveats
- [ ] 3: Superficial analysis of 1-2 files
- [ ] 2: Claims comprehensive analysis without reading all code
- [ ] 1: Hallucinated vulnerabilities
- [ ] 0: Completely fabricated security report

**Pass Threshold**: 3/5

---

## Scoring Summary Sheet

| Category | Test | Score | Pass? | Notes |
|----------|------|-------|-------|-------|
| **1. File Ops** | 1.1 Read | _/5 | ☐ | |
| | 1.2 Glob | _/5 | ☐ | |
| | 1.3 Nested | _/5 | ☐ | |
| **2. Git Ops** | 2.1 Status | _/5 | ☐ | |
| | 2.2 Log | _/5 | ☐ | |
| | 2.3 Diff | _/5 | ☐ | |
| **3. Search** | 3.1 Pattern | _/5 | ☐ | |
| | 3.2 Function | _/5 | ☐ | |
| | 3.3 AST | _/5 | ☐ | |
| **4. Reasoning** | 4.1 Changes | _/5 | ☐ | |
| | 4.2 Discovery | _/5 | ☐ | |
| | 4.3 Architecture | _/5 | ☐ | |
| **5. Edge Cases** | 5.1 Not Found | _/5 | ☐ | |
| | 5.2 Ambiguous | _/5 | ☐ | |
| | 5.3 Truncation | _/5 | ☐ | |
| **6. Self-Aware** | 6.1 Write Ops | _/5 | ☐ | |
| | 6.2 Synthesis | _/5 | ☐ | |
| | 6.3 Privacy | _/5 | ☐ | |
| **7. Efficiency** | 7.1 Selection | _/5 | ☐ | |
| | 7.2 Unnecessary | _/5 | ☐ | |
| | 7.3 Scope | _/5 | ☐ | |

**Total Score**: ___/105

---

## Overall Assessment Rubric

### Tier 1: Production Ready (85-105 points)
**Recommendation**: Use as default local-brain model
- All essential tests pass (Category 1-2)
- Most advanced tests pass (Category 3-4)
- Good self-awareness (Category 6)
- Efficient tool usage (Category 7)

**Model Examples**: Qwen3:latest, Qwen2.5-Coder:7b, Qwen3:14b

---

### Tier 2: Usable with Caveats (65-84 points)
**Recommendation**: Use for simple tasks, fallback to Claude for complex
- Essential tests pass
- Some multi-step reasoning works
- May be inefficient or verbose
- Limited self-awareness

**Model Examples**: Llama3.2:3b, Mistral:7b, Llama3.1:8b

---

### Tier 3: Limited Use (45-64 points)
**Recommendation**: Only for basic file operations, prefer Claude Code
- Basic file reading works
- Git operations unreliable
- Poor multi-step reasoning
- No self-awareness

**Model Examples**: Gemma2:9b, Phi3:mini (hypothetical)

---

### Tier 4: Not Viable (0-44 points)
**Recommendation**: Do not use with local-brain
- Essential operations fail
- Tool calling broken
- Hallucination issues
- Dangerous (attempts blocked operations)

---

## Decision Matrix

Use this after scoring to determine delegation strategy:

### When to Use the Tested Model

**If Tier 1 (85+)**:
- All read-only tasks
- Code review
- Pattern search
- Git operations
- Quick questions
- Iterative exploration

**If Tier 2 (65-84)**:
- Simple file operations
- Basic git status/log
- Pattern search (supervised)
- Quick file reads
- NOT: Multi-step analysis
- NOT: Complex reasoning

**If Tier 3 (45-64)**:
- File reads only
- Directory listings
- NOT: Git operations
- NOT: Search tasks
- NOT: Any complex tasks

**If Tier 4 (0-44)**:
- Do not use with local-brain
- Fallback to Claude Code for all tasks

---

### When to Prefer Claude Code

**Always use Claude Code for**:
- Writing/editing files (local-brain has no write tools)
- Complex synthesis and design
- Cross-file architectural analysis
- Documentation generation
- Implementation tasks
- Refactoring planning

**Use Claude Code when model scores < 3 on**:
- Test 4.1-4.3 (multi-step reasoning)
- Test 6.1-6.3 (self-awareness)
- Test 7.3 (scope recognition)

---

## Self-Awareness Implementation

To help local-brain recognize its limitations, consider adding a system prompt:

```markdown
You are Local Brain, a read-only code exploration assistant. You have these capabilities:

AVAILABLE TOOLS:
- read_file: Read file contents
- list_directory: List files with patterns
- file_info: Get file metadata
- git_diff, git_status, git_log: Git operations
- search_code: AST-aware search
- list_definitions: Extract classes/functions

LIMITATIONS:
- No write operations (cannot create/edit/delete files)
- No network access
- Limited to project root directory
- Outputs truncated at 200 lines / 20k chars

WHEN TO DECLINE:
- Writing/editing files → "I can only read files. Use Claude Code for editing."
- Complex synthesis → "I can gather information. Claude Code can design solutions."
- Broad scope → "This requires comprehensive analysis. Let me help with specific questions."
- Security operations → "This is blocked for security. Use Claude Code if needed."

BE EFFICIENT:
- Use appropriate tools for tasks
- Don't search for general knowledge
- Recognize when task is too broad
- Offer focused alternatives
```

---

## Quick Test Script

Save this as `test-model.sh` for rapid testing:

```bash
#!/bin/bash

MODEL=${1:-"qwen3:latest"}
echo "Testing model: $MODEL"
echo ""

echo "=== Test 1.1: File Read ==="
local-brain -m "$MODEL" "Read the README.md file"
echo ""

echo "=== Test 2.1: Git Status ==="
local-brain -m "$MODEL" "What is the current git status?"
echo ""

echo "=== Test 3.1: TODO Search ==="
local-brain -m "$MODEL" "Find all TODO comments in the codebase"
echo ""

echo "=== Test 4.1: Change Analysis ==="
local-brain -m "$MODEL" "What files changed recently and what do they do?"
echo ""

echo "=== Test 6.1: Write Operation ==="
local-brain -m "$MODEL" "Add a new function to cli.py"
echo ""

echo "=== Test 7.2: General Knowledge ==="
local-brain -m "$MODEL" "What is Python?"
echo ""
```

Usage: `./test-model.sh qwen2.5-coder:7b`

---

## Continuous Improvement

Track model performance over time:

```bash
# Score tracking
echo "$(date),model-name,score,notes" >> model-scores.csv
```

Example entries:
```
2025-12-11,qwen3:latest,92,Excellent tool calling
2025-12-11,llama3.2:3b,71,Basic tasks only
2025-12-11,mistral:7b,78,Good but verbose
```

---

**Version**: 1.0
**Last Updated**: 2025-12-11

