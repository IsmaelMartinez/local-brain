# ADR 005: CodeAgent with Markdown Code Block Tags

## Status

Accepted

**Supersedes**: [ADR 004 - ToolCallingAgent Over CodeAgent](004-toolcallingagent-over-codeagent.md)

## Context

After switching from `CodeAgent` to `ToolCallingAgent` (see ADR 004), we discovered a significant usability regression: the agent became too rigid for conversational queries.

### The Problem

The `ToolCallingAgent` system prompt enforces:

> "1. ALWAYS provide a tool call, else you will fail."

This means for **every** user query, the agent must make a tool call. When users ask conversational questions like "explain this code" or "what does this function do?", the agent:

1. Cannot respond naturally — must format everything as a `final_answer` tool call
2. May misuse tools to satisfy the "must call tool" requirement
3. Loses the chat-like experience that makes the tool approachable

### Why We Initially Switched (ADR 004)

`CodeAgent` requires models to output code in `<code>...</code>` XML tags, but local Ollama models (Qwen, Llama, Mistral) naturally output markdown code blocks (` ```python...``` `), causing infinite "code snippet is invalid" loops.

## Decision

We will revert to `CodeAgent` but configure it to accept **markdown code blocks** instead of XML tags using the `code_block_tags="markdown"` parameter.

## Options Considered

### Option 1: Multi-Step Agent (Router Pattern)

Create a router that classifies queries and delegates to either `ToolCallingAgent` or direct chat completion.

```python
def run_smart_agent(prompt):
    needs_tools = classify_query(prompt)  # LLM classification call
    if needs_tools:
        return tool_calling_agent.run(prompt)
    else:
        return direct_llm_response(prompt)
```

| Pros | Cons |
|------|------|
| Best UX — chat gets direct answers | Adds latency (2+ LLM calls) |
| Clean separation of concerns | More complex architecture |
| Leverages smolagents' ManagedAgent pattern | Classification step can fail |

**Verdict**: Good fallback option if Option 2 fails, but adds unnecessary complexity.

### Option 2: CodeAgent with Markdown Tags ✅ (Selected)

Use `CodeAgent` with `code_block_tags="markdown"` to accept the markdown format local models naturally produce.

```python
CodeAgent(
    tools=ALL_TOOLS,
    model=model,
    code_block_tags="markdown",  # Accepts ```python...```
)
```

| Pros | Cons |
|------|------|
| Simple one-parameter change | May need handling if models emit non-Python blocks |
| Works with local models' natural output | Code execution (but already sandboxed) |
| Full CodeAgent flexibility retained | |
| No architectural changes | |
| Already supported by smolagents | |

**Verdict**: Simplest fix that addresses the root cause.

### Option 3: Custom System Prompt for ToolCallingAgent

Override the default system prompt to remove the "ALWAYS provide a tool call" rule.

| Pros | Cons |
|------|------|
| Keeps JSON tool calling | Fights library design |
| Allows natural conversation | May break tool calling reliability |
| | Agent's `_step_stream` still expects tool calls |

**Verdict**: Too risky — could break tool calling entirely.

### Option 4: Instruction-Based Workaround

Keep `ToolCallingAgent` but add custom `instructions` allowing direct `final_answer` for chat queries.

```python
agent = ToolCallingAgent(
    tools=ALL_TOOLS,
    model=model,
    instructions="For conversational questions, use final_answer directly..."
)
```

| Pros | Cons |
|------|------|
| Minimal code change | Relies on LLM following instructions |
| Works within existing framework | Unreliable with smaller models |

**Verdict**: Too dependent on model instruction-following quality.

## Rationale

Option 2 was selected because:

1. **Addresses root cause** — Local models output markdown, so we accept markdown
2. **Simplest fix** — Single parameter change
3. **Full flexibility** — CodeAgent handles both tool calls AND natural responses
4. **Already supported** — smolagents explicitly provides `code_block_tags="markdown"`
5. **No complexity** — No router, classification, or multi-agent orchestration

## Consequences

### Positive

- Natural conversational responses work again ("explain this", "what does X do?")
- Compatible with local Ollama models (Qwen, Llama, Mistral)
- No infinite loops from format mismatch
- Maintains full tool-calling capabilities when needed

### Negative

- Returns to code execution model (but already sandboxed via LocalPythonExecutor)
- Models must output valid Python in code blocks (most do by default)

### Neutral

- No change to user-facing API or tool definitions
- Minimal code change (swap agent class, add parameter)

## Implementation

Changed in `local_brain/smolagent.py`:

```python
from smolagents import CodeAgent, LiteLLMModel

def create_agent(model_id: str, verbose: bool = False) -> CodeAgent:
    model = LiteLLMModel(
        model_id=f"ollama_chat/{model_id}",
        api_base="http://localhost:11434",
        num_ctx=8192,
    )

    return CodeAgent(
        tools=ALL_TOOLS,
        model=model,
        verbosity_level=2 if verbose else 0,
        code_block_tags="markdown",  # Accept markdown from local models
    )
```

## Fallback Plan

If Option 2 exhibits issues (e.g., models produce invalid code blocks), we will implement **Option 1 (Router Pattern)** as a more robust solution at the cost of added complexity and latency.

## References

- [ADR 004 - ToolCallingAgent Over CodeAgent](004-toolcallingagent-over-codeagent.md) (superseded)
- [Smolagents CodeAgent Documentation](https://huggingface.co/docs/smolagents)
- smolagents source: `CodeAgent` supports `code_block_tags` parameter

