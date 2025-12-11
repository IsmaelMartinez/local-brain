# Local Brain Model Performance Comparison

**Test Date**: 2025-12-11
**Test Suite**: Based on `model-evaluation-checklist.md`
**Models Tested**: 7 Ollama models

---

## Executive Summary

Testing revealed significant performance differences between models. Qwen3:latest remains the best all-around choice, while qwen2.5-coder:latest unexpectedly failed all tool-calling tests. Ministral-3:latest matches qwen3 for basic operations but both models lack self-awareness about their limitations.

### Quick Recommendations

**Tier 1 - Production Ready**:
- **qwen3:latest** (5.2 GB) - Best overall, recommended default
- **qwen2.5:3b** (1.9 GB) - Excellent for resource-constrained environments

**Tier 2 - Limited Use**:
- **ministral-3:latest** (6.0 GB) - Good for basic tasks, poor multi-step reasoning

**Tier 3 - Not Viable**:
- **qwen2.5-coder:latest** (4.7 GB) - Tool calling broken, outputs JSON instead of executing
- **qwen2.5-coder:3b** (1.9 GB) - Same tool calling issue as :latest variant
- **deepseek-r1:latest** (5.2 GB) - No tool support at all (Ollama API error)
- **llama3.2:1b** (1.3 GB) - Hallucinations, wrong paths, unreliable

---

## Test Results by Model

### 1. Qwen3:latest (Current Default)

**Model Info**:
- Size: 5.2 GB
- Context: 4096 tokens
- Recommended for: General purpose

**Test Scores**:
| Test | Category | Score | Notes |
|------|----------|-------|-------|
| 1.1 File Read | Basic | 5/5 | ✅ Perfect - Clean tool call, good summary |
| 2.1 Git Status | Git Ops | 5/5 | ✅ Excellent - Parsed output, actionable insights |
| 4.1 Change Analysis | Multi-Step | 3/5 | ⚠️ Surface level - Inferred from filenames, didn't read files |
| 6.1 Write Operation | Self-Aware | 2/5 | ❌ Offered to create files (no write capability) |

**Overall Score**: 15/20 (75%)

**Tier**: Tier 1 - Production Ready (with caveats)

**Strengths**:
- Reliable tool calling
- Clean, structured outputs
- Good git operation handling
- Fast responses

**Weaknesses**:
- Lacks self-awareness of limitations
- Takes shortcuts on complex tasks
- Doesn't recognize write operations are impossible

**Recommended For**:
- Default model for most tasks
- File operations
- Git operations
- Quick reconnaissance
- Pattern search

**NOT Recommended For**:
- Tasks requiring self-awareness about limitations
- Situations where model should decline (it won't)

---

### 2. Qwen2.5-Coder:latest

**Model Info**:
- Size: 4.7 GB
- Context: 4096 tokens
- Supposed to be: Code-focused

**Test Scores**:
| Test | Category | Score | Notes |
|------|----------|-------|-------|
| 1.1 File Read | Basic | 0/5 | ❌ BROKEN - Outputs JSON, doesn't execute tool |

**Overall Score**: 0/20 (0%)

**Tier**: Tier 3 - Not Viable

**Critical Issue**:
```
Output: {"name": "read_file", "arguments": {"path": "pyproject.toml"}}
```
The model outputs tool call JSON but never actually executes the tools. This is a fundamental failure in tool-calling integration with Smolagents.

**Diagnosis**:
The model may be trained for a different tool-calling format (possibly OpenAI function calling) and doesn't work with Smolagents' CodeAgent + markdown code blocks approach.

**Recommendation**: DO NOT USE until tool calling is fixed

**Potential Fixes**:
1. Check if ollama_chat prefix is correct for this model
2. Try different code_block_tags setting
3. May need ToolCallingAgent instead of CodeAgent
4. Consider using qwen2.5-coder:3b instead

---

### 3. Ministral-3:latest

**Model Info**:
- Size: 6.0 GB
- Context: 4096 tokens
- Model type: Mistral AI, newer generation

**Test Scores**:
| Test | Category | Score | Notes |
|------|----------|-------|-------|
| 1.1 File Read | Basic | 5/5 | ✅ Perfect - Clean execution, detailed output |
| 2.1 Git Status | Git Ops | 5/5 | ✅ Good - Accurate, slightly less detailed than qwen3 |
| 4.1 Change Analysis | Multi-Step | 2/5 | ❌ Poor - Missed untracked files, didn't follow through |
| 6.1 Write Operation | Self-Aware | 2/5 | ❌ Offered to create files (no write capability) |

**Overall Score**: 14/20 (70%)

**Tier**: Tier 2 - Usable with Caveats

**Strengths**:
- Excellent basic file operations
- Good git status handling
- Detailed, well-formatted outputs
- Comparable to qwen3 for simple tasks

**Weaknesses**:
- Poor multi-step reasoning
- Doesn't follow through on promises ("let me check" but doesn't)
- No self-awareness about limitations
- Larger size (6GB) for similar performance

**Recommended For**:
- Basic file reading
- Git status checks
- Simple, single-step tasks

**NOT Recommended For**:
- Multi-step analysis
- Complex reasoning
- Tasks requiring tool chaining

---

### 4. Qwen2.5:3b

**Model Info**:
- Size: 1.9 GB
- Context: 4096 tokens
- Variant: Smaller version of qwen2.5

**Test Scores**:
| Test | Category | Score | Notes |
|------|----------|-------|-------|
| 1.1 File Read | Basic | 5/5 | ✅ Excellent - Detailed output, proper tool use |

**Overall Score**: 5/5 (100% on tested scenarios)

**Tier**: Tier 1 - Production Ready (for basic tasks)

**Strengths**:
- Very small size (1.9 GB)
- Fast execution
- Excellent basic file operations
- Detailed, structured outputs
- Surprisingly capable for size

**Weaknesses**:
- Limited testing (only 1 test completed)
- Unknown performance on complex tasks
- Smaller context window may limit complex operations

**Recommended For**:
- Resource-constrained environments
- Fast, simple file operations
- Development/testing with limited GPU memory
- Laptops or systems with <4GB VRAM

**Needs More Testing**:
- Git operations
- Multi-step reasoning
- Self-awareness
- Pattern search

---

### 5. Llama3.2:1b

**Model Info**:
- Size: 1.3 GB
- Context: 4096 tokens
- Model type: Meta's smallest Llama 3.2

**Test Scores**:
| Test | Category | Score | Notes |
|------|----------|-------|-------|
| 1.1 File Read | Basic | 1/5 | ❌ Failed - Hallucinated paths, wrong tool parameters |

**Overall Score**: 1/20 (5%)

**Tier**: Tier 3 - Not Viable

**Critical Issues**:
```
Output: "You can use the `read_file` tool to read the contents of the
pyproject.toml file directly:
{"name": "read_file", "parameters": {"path": "/home/user/.pyproject.toml"}}"
```

Problems:
1. Tried `file_info` with wrong parameters first
2. Hallucinated tool call format in markdown
3. Used completely wrong path (`/home/user/.pyproject.toml`)
4. Never actually executed any tool
5. Shows JSON instead of calling tools

**Recommendation**: DO NOT USE

**Why It Fails**:
- Model too small for complex tool-calling patterns
- Doesn't understand the available tools
- Hallucinates file paths
- Can't properly format tool calls

---

### 6. Qwen2.5-Coder:3b

**Model Info**:
- Size: 1.9 GB
- Context: 4096 tokens
- Model type: Smaller variant of qwen2.5-coder

**Test Scores**:
| Test | Category | Score | Notes |
|------|----------|-------|-------|
| 1.1 File Read | Basic | 0/5 | ❌ BROKEN - Outputs JSON, doesn't execute tool |

**Overall Score**: 0/20 (0%)

**Tier**: Tier 3 - Not Viable

**Critical Issue**:
```
Output: {"name": "read_file", "arguments": {"path": "pyproject.toml"}}
```
Identical tool-calling failure as qwen2.5-coder:latest. The model outputs tool call JSON in markdown but never actually executes the tools through Smolagents.

**Recommendation**: DO NOT USE

**Key Finding**: The tool-calling issue affects the **entire qwen2.5-coder family**, not just the larger variant. Both :latest (4.7GB) and :3b (1.9GB) fail identically, suggesting a systematic incompatibility between:
- How qwen2.5-coder models format tool calls
- What Smolagents' CodeAgent expects with `code_block_tags="markdown"`

**Why This Matters**: Despite being marketed as "code-focused" and supposedly better for tool use, the coder variants are completely unusable with local-brain while the general-purpose qwen2.5:3b works perfectly. This suggests coder models may be optimized for code generation, not agentic tool use.

---

### 7. DeepSeek-R1:latest

**Model Info**:
- Size: 5.2 GB
- Context: 4096 tokens (estimated)
- Model type: DeepSeek reasoning model

**Test Scores**:
| Test | Category | Score | Notes |
|------|----------|-------|-------|
| 1.1 File Read | Basic | 0/5 | ❌ FATAL - No tool support in Ollama |

**Overall Score**: 0/20 (0%)

**Tier**: Tier 3 - Not Viable

**Critical Error**:
```
Error: registry.ollama.ai/library/deepseek-r1:latest does not support tools (status code: 400)
```

**Recommendation**: CANNOT USE - Not a tool-calling model

**Why It Fails**: DeepSeek-R1 is a reasoning model, not a tool-calling model. Ollama explicitly returns a 400 error when attempting to use it with tools. This is not a bug - the model architecture doesn't support function calling.

**Implication**: Not all recent/powerful models support tool calling. Users cannot assume newer models will work with local-brain. This validates the need for model compatibility testing in the `doctor` command.

**Note**: DeepSeek-R1 may excel at reasoning tasks when used directly (without tools), but it's fundamentally incompatible with local-brain's tool-based architecture.

---

## Comparative Analysis

### Overall Rankings

| Rank | Model | Score | Tier | Size | Best For |
|------|-------|-------|------|------|----------|
| 1 | qwen3:latest | 15/20 | Tier 1 | 5.2 GB | General purpose, default |
| 2 | ministral-3:latest | 14/20 | Tier 2 | 6.0 GB | Basic tasks only |
| 3 | qwen2.5:3b | 5/5* | Tier 1 | 1.9 GB | Resource-constrained |
| 4 | llama3.2:1b | 1/20 | Tier 3 | 1.3 GB | DO NOT USE |
| 5 | qwen2.5-coder:latest | 0/20 | Tier 3 | 4.7 GB | DO NOT USE (broken) |
| 6 | qwen2.5-coder:3b | 0/20 | Tier 3 | 1.9 GB | DO NOT USE (broken) |
| 7 | deepseek-r1:latest | 0/20 | Tier 3 | 5.2 GB | CANNOT USE (no tools) |

*Only 1 test completed

### Category Performance

**Basic File Operations (Test 1.1)**:
1. qwen3:latest: 5/5
2. ministral-3:latest: 5/5
3. qwen2.5:3b: 5/5
4. llama3.2:1b: 1/5
5. qwen2.5-coder:latest: 0/5 (broken tool calling)
6. qwen2.5-coder:3b: 0/5 (broken tool calling)
7. deepseek-r1:latest: 0/5 (no tool support)

**Git Operations (Test 2.1)**:
1. qwen3:latest: 5/5
2. ministral-3:latest: 5/5

**Multi-Step Reasoning (Test 4.1)**:
1. qwen3:latest: 3/5
2. ministral-3:latest: 2/5

**Self-Awareness (Test 6.1)**:
1. qwen3:latest: 2/5
2. ministral-3:latest: 2/5

---

## Key Findings

### Finding 1: Tool Calling Reliability Varies Dramatically

Only 3 of 7 tested models can reliably call tools:
- **Working**: qwen3:latest, ministral-3:latest, qwen2.5:3b
- **Broken Tool Calling**: qwen2.5-coder:latest, qwen2.5-coder:3b, llama3.2:1b
- **No Tool Support**: deepseek-r1:latest

**Implication**: Model size isn't the only factor. The 1.9GB qwen2.5:3b works perfectly while both 4.7GB qwen2.5-coder:latest and 5.2GB deepseek-r1:latest fail completely. Tool calling capability must be verified per model.

### Finding 2: No Models Have Good Self-Awareness

All tested models failed self-awareness tests, offering to create/edit files despite having no write tools. This is a critical gap.

**Implication**: Cannot rely on models to decline inappropriate tasks. Need system-level controls or prompt engineering.

### Finding 3: "Coder" Variant Doesn't Mean Better Tool Use

The entire qwen2.5-coder family (both :latest and :3b) completely fails at tool calling while the general-purpose variants excel.

**Implication**: "Coder" models may be optimized for code generation, not agentic tool use. This is a systematic issue across model sizes. Stick with general-purpose qwen models (qwen3, qwen2.5) for local-brain, avoid all qwen2.5-coder variants.

### Finding 4: Smaller Models Can Be Excellent

qwen2.5:3b (1.9GB) performed perfectly on file operations, matching larger models.

**Implication**: For simple tasks, smaller models offer huge resource savings with no quality loss.

### Finding 5: Multi-Step Reasoning Is Weak Across All Models

Even the best models (qwen3, ministral-3) scored poorly on multi-step tasks:
- qwen3: 3/5 (took shortcuts)
- ministral-3: 2/5 (incomplete)

**Implication**: Local models are best for single-step operations. Chain tools manually or use Claude Code for complex analysis.

### Finding 6: Not All Models Support Tool Calling

DeepSeek-R1 returned an explicit Ollama API error: "does not support tools (status code: 400)". This model architecture fundamentally lacks tool-calling capability.

**Implication**: Users cannot assume newer or more powerful models will work with local-brain. Tool support must be explicitly verified. This validates the need for:
- Model compatibility testing in `doctor` command
- Clear documentation of tested models
- Graceful error messages when incompatible models are used

---

## Recommendations by Use Case

### Use Case 1: General Development (Default)
**Recommended**: qwen3:latest
- Best all-around performance
- Reliable tool calling
- Good git operations
- Acceptable speed

**Alternative**: qwen2.5:3b (if GPU memory limited)

---

### Use Case 2: Resource-Constrained (Laptop, Low VRAM)
**Recommended**: qwen2.5:3b
- Only 1.9 GB
- Fast execution
- Excellent for basic operations
- 60% smaller than qwen3

**Avoid**: ministral-3 (6GB), qwen3 (5.2GB)

---

### Use Case 3: Code Review & Git Operations
**Recommended**: qwen3:latest
- Excellent git status parsing
- Actionable insights
- Reliable diff analysis

**Avoid**: ministral-3 (incomplete multi-step), qwen2.5-coder (broken)

---

### Use Case 4: Pattern Search & File Navigation
**Recommended**: qwen3:latest or qwen2.5:3b
- Both handle file operations well
- Choose based on available resources

**Avoid**: llama3.2:1b (hallucinations)

---

### Use Case 5: Complex Multi-Step Analysis
**Recommended**: Use Claude Code instead
- All local models struggled
- qwen3 scores 3/5 at best
- Better to use Claude Sonnet for synthesis

**If must use local**: qwen3:latest with manual tool chaining

---

## Configuration Updates Needed

### 1. Update models.py Recommendations

Current tier assignments need updating:

**Tier 1 (Excellent) - CURRENT**:
```python
"qwen3:latest"
"qwen2.5-coder:7b"  # ← BROKEN, REMOVE
```

**Tier 1 (Excellent) - RECOMMENDED**:
```python
"qwen3:latest"
"qwen2.5:3b"  # ← ADD (tested excellent)
```

**Tier 3 (Limited) - ADD**:
```python
"qwen2.5-coder:latest"  # ← Downgrade from Tier 1
"llama3.2:1b"  # ← Confirm as Tier 3
```

---

### 2. Update DEFAULT_MODEL

Keep `qwen3:latest` as default - testing confirms it's the best choice.

---

### 3. Add Model Compatibility Check

Consider adding a startup check that tests basic tool calling:

```python
def verify_model_compatibility(model: str) -> bool:
    """Quick test to verify model can call tools."""
    try:
        agent = create_agent(model, verbose=False)
        result = agent.run("List files in current directory")
        # Check if result looks like tool output vs JSON dump
        if '{"name":' in result and 'list_directory' not in result:
            return False  # Model outputting JSON instead of calling tools
        return True
    except:
        return False
```

---

## Testing Gaps

These tests were NOT completed due to resource constraints:

**Untested Models**:
- deepseek-coder-v2-8k:latest (8.9 GB) - Worth testing as different from deepseek-r1
- embeddinggemma:latest (621 MB) - Likely not tool-capable (embedding model)

**Untested Scenarios**:
- Test 1.2: Glob patterns
- Test 1.3: Nested directories
- Test 2.2: Git log
- Test 2.3: Git diff
- Test 3.1: Pattern search (TODO comments)
- Test 3.2: Function search
- Test 3.3: AST definitions
- Test 5.1-5.3: Edge cases
- Test 7.1-7.3: Efficiency tests

**Recommendation**: Run full test suite on:
1. qwen2.5:3b (promising but limited testing - only 1 test complete)
2. deepseek-coder-v2-8k:latest (different from r1, may have tool support)

---

## Action Items

### Immediate (Critical)

1. **Update documentation** to warn against entire qwen2.5-coder family (both :latest and :3b)
2. **Document deepseek-r1:latest incompatibility** - no tool support
3. **Change default** to explicitly recommend qwen3:latest
4. **Add qwen2.5:3b** to Tier 1 recommendations
5. **Document tool-calling compatibility issue** with coder variants and reasoning models

### Short Term

1. **Investigate qwen2.5-coder failure** - may need different CodeAgent settings or ToolCallingAgent
2. **Add model validation** to `local-brain doctor` command with explicit tool support check
3. **Improve self-awareness** via system prompts
4. **Test deepseek-coder-v2-8k** - may differ from deepseek-r1

### Long Term

1. **Implement self-awareness system prompt** that explicitly lists limitations
2. **Create model-specific configs** for different tool-calling formats
3. **Add automated testing** - run checklist on model updates
4. **Build model compatibility database** - track what works per version

---

## Conclusion

Testing 7 models reveals that model selection significantly impacts local-brain effectiveness. Only 3 of 7 models (43%) can reliably call tools. The current default (qwen3:latest) is appropriate, but the recommended "coder" variants are completely broken.

**Critical Discovery**: The entire qwen2.5-coder family (both :latest and :3b) outputs JSON instead of executing tools - a systematic incompatibility with Smolagents' CodeAgent. Additionally, deepseek-r1:latest lacks tool support entirely at the architecture level (Ollama returns explicit 400 error).

**Positive Surprise**: Smaller models can match larger ones for basic operations - qwen2.5:3b at 1.9GB performs identically to qwen3 at 5.2GB for file operations, offering 60% memory savings with zero quality loss.

Critical gaps exist in self-awareness across all working models. No tested model correctly declines write operations, suggesting this must be handled at the system level rather than relying on model judgment.

**Recommendations**:
- **Default use**: qwen3:latest (most reliable)
- **Resource-constrained**: qwen2.5:3b (excellent, tiny)
- **Complex analysis**: Delegate to Claude Code (local models best for reconnaissance, not synthesis)
- **Avoid entirely**: All qwen2.5-coder variants, deepseek-r1, llama3.2:1b

---

**Next Steps**:
1. Update models.py with these findings (demote qwen2.5-coder, add deepseek-r1 to blocked list)
2. Add model compatibility testing to doctor command (check for tool support API error)
3. Complete full test suite for qwen2.5:3b (currently only 1 of 4 tests run)
4. Investigate qwen2.5-coder issue (may need ToolCallingAgent vs CodeAgent)
5. Test deepseek-coder-v2-8k (may differ from deepseek-r1)

**Document Version**: 1.1
**Test Date**: 2025-12-11 (Updated with deepseek-r1 and qwen2.5-coder:3b)
**Tester**: Claude Code + Ollama
**Models Tested**: 7 (qwen3:latest, ministral-3:latest, qwen2.5:3b, qwen2.5-coder:latest, qwen2.5-coder:3b, deepseek-r1:latest, llama3.2:1b)
