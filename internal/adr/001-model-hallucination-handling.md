# ADR-001: Model Hallucination Handling Strategy

**Status**: Accepted

**Date**: November 2025

**Deciders**: Project maintainer

---

## Context

During validation testing (Phase 1-2, November 2025), we discovered two critical issues with model output:

1. **Markdown Code Fence Wrapping**: Despite explicit instructions to return "ONLY valid JSON", the model (deepseek-coder-v2-8k) consistently wrapped JSON responses in markdown code fences (\`\`\`json...`\`\`), making direct JSON parsing fail.

2. **Documentation File Hallucination**: When reviewing pure documentation files (e.g., IMPLEMENTATION_PLAN.md), the code-focused model hallucinated non-existent code functions (e.g., "verify_token", "login", "logout" functions that don't exist), producing invalid review results.

These issues threatened the reliability of the entire system, as structured JSON output is critical for Claude Code skill integration.

## Decision

We will implement a **multi-layered defense strategy**:

### 1. JSON Extraction Layer (for markdown wrapping)

Implement `extract_json_from_markdown()` function that:
- Detects and strips markdown code fences before JSON parsing
- Falls back to direct parsing if no fences detected
- Provides 100% reliability for JSON extraction

**Code Location**: `src/main.rs:240-260`

### 2. Stronger System Prompt

Update system prompt to be more explicit:
```
"You MUST output ONLY raw JSON. No markdown, no code fences, no explanations..."
```

**Code Location**: `src/main.rs:111`

**Rationale**: Belt-and-suspenders approach - both prompt improvement AND extraction layer.

### 3. File Type Guidance (for hallucination)

**Document, don't fix**: Acknowledge model hallucination on documentation files as a known limitation.

**Guidance**:
- **Best for**: Code files (Rust, JS, Python, etc.)
- **Use with caution**: Pure documentation/planning files
- **Reason**: Code-focused models infer code patterns in text-only docs

**Documentation Location**: README.md, VALIDATION.md

## Consequences

### Positive

- **100% JSON reliability**: Extraction layer achieved 100% success rate in validation (5/5 basic tests, all integration tests)
- **Graceful degradation**: System works even if prompt is ignored
- **Clear user guidance**: Users understand tool limitations
- **Fast processing**: Extraction adds negligible overhead (<1ms)
- **Maintainable**: Single extraction function, easy to update

### Negative

- **Doesn't fix root cause**: Model behavior unchanged, we work around it
- **File type limitations**: Not suitable for all use cases (docs review unreliable)
- **Ongoing risk**: Future models may have different wrapping behavior
- **User education needed**: Must document file type recommendations

### Neutral

- **Architecture decision**: Committed to extraction-based approach vs. model retraining
- **No performance impact**: <1ms per review for extraction

## Alternatives Considered

### 1. Model Retraining/Fine-tuning
**Rejected**: Requires significant resources, not feasible for solo dev project, would need to maintain custom model.

### 2. Structured Output API
**Investigated**: Ollama didn't support structured output guarantees at validation time.
**Status**: Revisit if Ollama adds this feature.

### 3. Retry Loop with Validation
**Rejected**: 3x slower (multiple API calls), doesn't solve hallucination problem, extraction layer is more reliable.

### 4. Switch to Different Model
**Considered**: Other models (qwen2.5-coder, llama3.2) may have same issues, extraction layer is model-agnostic solution.
**Decision**: Keep current approach, document model compatibility.

## References

- **Validation Results**: [internal/VALIDATION.md](../VALIDATION.md) (Issues #1-2)
- **Implementation**: `src/main.rs:240-260` (extraction function)
- **User Documentation**: README.md (file type recommendations)
- **Related Decision**: ADR-003 (Model Selection Priority System)

## Notes

This decision enables production deployment while acknowledging inherent limitations of code-focused LLMs. The extraction layer provides reliability without compromising on the benefits of using local models (privacy, speed, cost).

**Future Consideration**: If Ollama adds native structured output support, we could simplify by removing extraction layer while keeping stronger prompts as safeguard.
