# 005 - LiteLLM Routing for Ollama + Sub-Agent Orchestration

**Date:** 2026-02-12
**Status:** Evaluation
**Relates to:** ADR-002 (Smolagents), ADR-005 (CodeAgent with Markdown Tags)

## Problem Statement

Local-brain currently uses a single Ollama model per invocation via `LiteLLMModel`. Two questions:

1. **Can LiteLLM route between multiple Ollama models** (e.g., tier-based routing, fallbacks)?
2. **How do we run sub-agents** with smolagents using this configuration?

The core constraint: local Ollama models have limited tool-calling reliability (only ~43% of tested models work), and the `CodeAgent` + `code_block_tags="markdown"` workaround is essential.

## Current Architecture

```
CLI (click)
  → select single model (models.py)
    → LiteLLMModel(model_id="ollama_chat/{model}", api_base="http://localhost:11434")
      → CodeAgent(tools=ALL_TOOLS, code_block_tags="markdown")
        → agent.run(prompt)
```

- **smolagents 1.23.0** installed
- **litellm >= 1.0.0** dependency
- Single model, single agent, no routing or fallback

---

## Finding 1: LiteLLM Can Route Ollama Models

LiteLLM has a `Router` class that supports model routing, fallbacks, and load balancing. It works with Ollama via the `ollama_chat/` prefix.

### LiteLLM Router Configuration

```python
from litellm import Router

router = Router(
    model_list=[
        {
            "model_name": "local-large",
            "litellm_params": {
                "model": "ollama_chat/qwen3:30b",
                "api_base": "http://localhost:11434",
            },
        },
        {
            "model_name": "local-small",
            "litellm_params": {
                "model": "ollama_chat/qwen2.5:3b",
                "api_base": "http://localhost:11434",
            },
        },
    ],
    default_fallbacks=["local-small"],  # fallback if primary fails
    num_retries=2,
    timeout=60,
)

# Use like standard litellm.completion()
response = router.completion(
    model="local-large",
    messages=[{"role": "user", "content": "Hello"}],
)
```

### What Routing Buys Us

| Feature | Current | With Router |
|---------|---------|-------------|
| Fallback on failure | None (crashes) | Automatic to next model |
| Load balancing | N/A | Round-robin or latency-based |
| Model tiering | Manual via CLI `-m` | Config-driven |
| Cost/token tracking | None | Built-in callbacks |
| Rate limiting | None | Per-model limits |

### The Problem: Smolagents' LiteLLMModel

**`LiteLLMModel` does not accept a `Router` instance.** It calls `litellm.completion()` directly with a `model_id` string. To use the Router, we would need to either:

1. **Run LiteLLM Proxy Server** as a sidecar process (acts as OpenAI-compatible endpoint with routing built in)
2. **Subclass `LiteLLMModel`** to call `router.completion()` instead of `litellm.completion()`
3. **Use `litellm.set_callbacks`** for observability without full routing

### Recommended: Option 2 (Custom LiteLLMModel Subclass)

```python
from smolagents import LiteLLMModel
from litellm import Router

class RoutedLiteLLMModel(LiteLLMModel):
    """LiteLLMModel that uses Router for fallbacks and load balancing."""

    def __init__(self, router: Router, model_id: str, **kwargs):
        super().__init__(model_id=model_id, **kwargs)
        self._router = router

    def __call__(self, messages, **kwargs):
        # Override to use router.completion instead of litellm.completion
        response = self._router.completion(
            model=self.model_id,
            messages=messages,
            **kwargs,
        )
        return response
```

**Caveat:** This requires inspecting `LiteLLMModel.__call__` to confirm the override is safe. The smolagents `LiteLLMModel` may do preprocessing on messages that we need to preserve.

### Alternative: LiteLLM Proxy Server

```bash
# config.yaml
model_list:
  - model_name: local-agent
    litellm_params:
      model: ollama_chat/qwen3:30b
      api_base: http://localhost:11434
  - model_name: local-agent
    litellm_params:
      model: ollama_chat/qwen2.5:3b
      api_base: http://localhost:11434

# Run proxy
litellm --config config.yaml --port 4000
```

Then point smolagents at the proxy:

```python
model = LiteLLMModel(
    model_id="openai/local-agent",
    api_base="http://localhost:4000",
)
```

**Pros:** No code changes, full routing features, dashboard UI.
**Cons:** Extra process to manage, added latency, more moving parts.

---

## Finding 2: Smolagents Sub-Agents Work with Ollama (With Caveats)

### Current API (smolagents >= 1.8.0)

The old `ManagedAgent` wrapper class was removed in v1.8.0. Now you pass agents directly with `name` and `description` attributes:

```python
from smolagents import CodeAgent, ToolCallingAgent, LiteLLMModel

model = LiteLLMModel(
    model_id="ollama_chat/qwen3:30b",
    api_base="http://localhost:11434",
    num_ctx=8192,
)

# Sub-agent: specialized for code search
search_agent = CodeAgent(
    tools=[search_code, list_definitions, read_file],
    model=model,
    max_steps=5,
    name="code_search",
    description="Searches the codebase for patterns, definitions, and file contents.",
    code_block_tags="markdown",
)

# Sub-agent: specialized for git operations
git_agent = CodeAgent(
    tools=[git_diff, git_status, git_log, git_changed_files],
    model=model,
    max_steps=5,
    name="git_ops",
    description="Runs git operations: diff, status, log, changed files.",
    code_block_tags="markdown",
)

# Manager agent: plans and delegates
manager_agent = CodeAgent(
    tools=[],
    model=model,
    managed_agents=[search_agent, git_agent],
    code_block_tags="markdown",
    max_steps=15,
)

result = manager_agent.run("What changed in the last commit and how does it affect security.py?")
```

### Key Constraints for Ollama Sub-Agents

| Constraint | Impact | Mitigation |
|-----------|--------|------------|
| `code_block_tags="markdown"` needed on ALL agents | Manager + all sub-agents must use it | Set consistently in factory function |
| Only ~43% of models support tool calling | Sub-agents may fail with weaker models | Stick to Tier 1 models (qwen3, qwen2.5:3b) |
| Context window limits (8192 default) | Multi-agent = more context consumed | Keep sub-agent `max_steps` low (3-5) |
| Manager must generate code to call sub-agents | Requires model that can write `code_search("query")` | qwen3:30b handles this well |
| Each sub-agent call = full LLM round-trip | Latency compounds with multiple agents | Minimize delegation depth |

### The Real Problem: Manager Quality with Local Models

The manager agent must:
1. Understand the task
2. Decide which sub-agent to call
3. Write Python code like `result = code_search("find security vulnerabilities")`
4. Interpret the result
5. Decide next steps or call `final_answer()`

This requires strong reasoning and code generation. Based on model evaluation (004-model-performance-comparison.md):

- **qwen3:30b** — Can likely handle manager role (Tier 1, good tool calling)
- **qwen3:latest / qwen2.5:3b** — Better as sub-agents (smaller, faster, focused tasks)
- **Most other models** — Not viable for multi-agent orchestration

### Practical Multi-Agent Architecture for Local-Brain

```
Manager Agent (qwen3:30b, CodeAgent)
  ├── code_search sub-agent (qwen2.5:3b, CodeAgent)
  │     tools: search_code, list_definitions, read_file
  ├── git_ops sub-agent (qwen2.5:3b, CodeAgent)
  │     tools: git_diff, git_status, git_log, git_changed_files
  └── file_explorer sub-agent (qwen2.5:3b, CodeAgent)
        tools: read_file, list_directory, file_info
```

**Mixed-model setup** (different models for manager vs sub-agents):

```python
manager_model = LiteLLMModel(
    model_id="ollama_chat/qwen3:30b",
    api_base="http://localhost:11434",
    num_ctx=8192,
)

sub_model = LiteLLMModel(
    model_id="ollama_chat/qwen2.5:3b",
    api_base="http://localhost:11434",
    num_ctx=4096,
)

search_agent = CodeAgent(
    tools=[search_code, list_definitions, read_file],
    model=sub_model,
    max_steps=5,
    name="code_search",
    description="Searches codebase for code patterns and definitions.",
    code_block_tags="markdown",
)

manager = CodeAgent(
    tools=[read_file, list_directory],
    model=manager_model,
    managed_agents=[search_agent],
    code_block_tags="markdown",
)
```

---

## Finding 3: LiteLLM Routing + Sub-Agents Combined

The two features compose naturally:

```python
from litellm import Router
from smolagents import CodeAgent, LiteLLMModel

# Router handles fallbacks per tier
router_config = [
    {
        "model_name": "manager-model",
        "litellm_params": {
            "model": "ollama_chat/qwen3:30b",
            "api_base": "http://localhost:11434",
        },
    },
    {
        "model_name": "manager-model",
        "litellm_params": {
            "model": "ollama_chat/qwen3:latest",  # fallback
            "api_base": "http://localhost:11434",
        },
    },
    {
        "model_name": "worker-model",
        "litellm_params": {
            "model": "ollama_chat/qwen2.5:3b",
            "api_base": "http://localhost:11434",
        },
    },
]

# Use RoutedLiteLLMModel (custom subclass) or LiteLLM Proxy
# Then create multi-agent system as above
```

---

## Evaluation Summary

### Can LiteLLM route Ollama models?

**Yes**, via the `Router` class or LiteLLM Proxy Server. But `smolagents.LiteLLMModel` doesn't natively support `Router` — you need either a custom subclass or the proxy server approach.

### Can we run sub-agents with Ollama?

**Yes**, smolagents 1.23.0 supports `managed_agents` parameter directly on `CodeAgent`. The old `ManagedAgent` wrapper is gone. You pass agents directly with `name` and `description`.

### What's the main blocker?

**Model quality for the manager role.** The manager agent needs to reliably:
- Parse tasks into sub-agent calls
- Write correct Python code to invoke sub-agents
- Handle multi-step reasoning

Only `qwen3:30b` is a realistic candidate for manager. Smaller models work as focused sub-agents.

### Recommended Implementation Path

1. **Phase 1 — Sub-agents without routing (low effort)**
   - Add `managed_agents` support to `create_agent()`
   - Split current 9 tools into 2-3 focused sub-agents
   - Use same model for all agents initially
   - Add `--multi-agent` CLI flag

2. **Phase 2 — Mixed models (medium effort)**
   - Allow different models for manager vs sub-agents
   - CLI: `local-brain --manager qwen3:30b --worker qwen2.5:3b "prompt"`
   - Factory function creates multi-model agent hierarchy

3. **Phase 3 — LiteLLM routing (higher effort)**
   - Add `litellm_config.yaml` support
   - Implement `RoutedLiteLLMModel` subclass or LiteLLM Proxy integration
   - Automatic fallback when primary model is unavailable
   - Token/cost tracking via LiteLLM callbacks

### What NOT to Do

- **Don't use `ToolCallingAgent` for sub-agents** — Ollama models need `code_block_tags="markdown"` which is only on `CodeAgent`
- **Don't run LiteLLM Proxy for local-only use** — Too much overhead for single-machine Ollama; save it for mixed cloud+local setups
- **Don't make all 9 tools available to every sub-agent** — The whole point of sub-agents is focused tool sets

---

## References

- [Smolagents Multi-Agent Docs](https://huggingface.co/docs/smolagents/en/examples/multiagents)
- [Smolagents Agent Reference](https://huggingface.co/docs/smolagents/reference/agents)
- [LiteLLM Ollama Provider](https://docs.litellm.ai/docs/providers/ollama)
- [LiteLLM Router/Proxy Config](https://docs.litellm.ai/docs/proxy/configs)
- [LLM Model Routing Guide (Medium, Dec 2025)](https://medium.com/@michael.hannecke/implementing-llm-model-routing-a-practical-guide-with-ollama-and-litellm-b62c1562f50f)
- [Smolagents ManagedAgent Removal (Issue #657)](https://github.com/huggingface/smolagents/issues/657)
