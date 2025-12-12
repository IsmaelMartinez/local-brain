# ADR 0001: Use ToolCallingAgent Over CodeAgent

## Status

Superseded by [ADR 005 - CodeAgent with Markdown Tags](005-codeagent-with-markdown-tags.md)

## Context

Local Brain uses HuggingFace's `smolagents` library to provide an AI agent that can explore codebases using tools like `read_file`, `git_diff`, and `search_code`. The library provides two agent types:

1. **CodeAgent** - Executes arbitrary Python code in a sandboxed environment. The model outputs code in `<code>...</code>` XML tags that gets parsed and executed.
2. **ToolCallingAgent** - Uses JSON-based function calling to invoke predefined tools. The model outputs JSON tool calls.

When running with local Ollama models (Qwen, Llama, Mistral, etc.), we encountered an infinite loop where the agent repeatedly produced "code snippet is invalid" errors. The root cause: local models output markdown code blocks (```python...```) instead of the XML format (`<code>...</code>`) that CodeAgent expects.

## Decision

We will use `ToolCallingAgent` instead of `CodeAgent`.

## Rationale

### Why ToolCallingAgent Works Better with Local Models

1. **Universal Format** - JSON function calling is a widely-supported pattern across modern LLMs. Models like Qwen, Llama 3, and Mistral are trained to handle JSON tool calls.

2. **No Special Syntax** - CodeAgent requires models to output `<code>...</code>` XML blocks, which only models specifically fine-tuned for smolagents format handle reliably.

3. **Simpler Parsing** - The model just needs to specify which tool to call and with what arguments, rather than generating valid Python code.

4. **Better Error Handling** - JSON parsing errors are clearer and easier to debug than code execution errors.

### Trade-offs

| Aspect | CodeAgent | ToolCallingAgent |
|--------|-----------|------------------|
| **Flexibility** | Can execute arbitrary Python code | Limited to predefined tools |
| **Model Compatibility** | Requires special training | Works with most modern LLMs |
| **Use Case Fit** | General-purpose scripting | Structured tool invocation |
| **Reliability** | High with compatible models | High with most models |

For Local Brain's use case (codebase exploration with specific tools), ToolCallingAgent is actually a better fit - we don't need arbitrary Python execution, just reliable tool calling.

### What About Small Models?

Very small models (< 7B parameters) may still struggle with JSON function calling. However, the models we recommend (Qwen 2.5 7B+, Llama 3 8B+) all handle JSON tool calls well.

## Consequences

### Positive

- Works reliably with local Ollama models out of the box
- No infinite loops from format mismatch
- Simpler output to debug when issues occur
- More predictable behavior across different models

### Negative

- Cannot execute arbitrary Python code (which we don't need)
- Tools must be predefined (which aligns with our security model anyway)

### Neutral

- No change to the user-facing API or tool definitions
- Minimal code change (just swap agent class)

## Implementation

Changed in `local_brain/smolagent.py`:
- Import `ToolCallingAgent` instead of `CodeAgent`
- Update `create_agent()` to return `ToolCallingAgent` instance
- Update docstrings to reflect the change

No changes needed to tool definitions - both agent types use the same `@tool` decorator.

## References

- [Smolagents Documentation](https://github.com/huggingface/smolagents)
- Issue: Infinite loop with "code snippet is invalid" errors
- Models tested: Qwen 2.5, Llama 3, Mistral
