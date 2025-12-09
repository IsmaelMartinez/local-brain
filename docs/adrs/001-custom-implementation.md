# ADR-001: Keep Custom Implementation over Frameworks

**Status:** Accepted  
**Date:** 2025-12-08

## Context

Local Brain is a CLI that lets Claude Code delegate codebase exploration to local Ollama models. We evaluated whether to use existing frameworks (LangChain, LlamaIndex, Aider) or keep a custom implementation.

## Decision

Keep the custom implementation. Local Brain is a **delegation target**, not a standalone CLI competing with Aider.

### Why NOT Aider
- Interactive (designed for humans in terminals)
- No programmatic API for delegation
- Expects user input/confirmation loops

### Why NOT Frameworks (LangChain, LlamaIndex, etc.)
- Overkill: 50+ dependencies vs minimal
- Abstraction overhead for direct Ollama integration
- Maintenance burden as frameworks evolve

### Why Custom
- Works for the delegation use case
- Minimal dependencies
- Focused on read-only codebase exploration
- Simple to maintain and extend
- Native Ollama integration

## Consequences

- Small, focused codebase (~350 lines)
- Few dependencies (ollama, click, smolagents, litellm)
- Full control over security (path jailing, tool restrictions)
- Must implement tools ourselves (see [ADR-002](./002-smolagents.md))

