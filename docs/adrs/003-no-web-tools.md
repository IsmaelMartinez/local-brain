# ADR-003: No Web Tools

**Status:** Accepted  
**Date:** 2025-12-08

## Context

We considered adding web browsing and search capabilities (DuckDuckGo search, URL fetching) to Local Brain.

## Decision

**Do not add web tools.** Local Brain is for *local* codebase exploration only.

### Security Risks
- **Data exfiltration** — Model could send code to attacker-controlled URLs
- **SSRF attacks** — Fetching internal URLs (localhost, private IPs)
- **Prompt injection** — Malicious content in fetched pages could manipulate the model
- **Resource exhaustion** — Large pages, infinite redirects

### Scope Creep
- Local Brain's purpose is local codebase exploration
- Adding web tools increases attack surface
- Would require URL validation, rate limiting, content sanitization

### Better Alternative
Claude Code already has web access. Delegate web research to Claude, local execution to Local Brain:

```
┌─────────────┐  web research   ┌─────────────┐
│ Claude Code │ ◄─────────────► │  Internet   │
│   (Cloud)   │                 └─────────────┘
│             │
│             │  local codebase ┌─────────────┐
│             │ ◄─────────────► │ Local Brain │
└─────────────┘                 └─────────────┘
```

## Consequences

- No `web_search` or `fetch_url` tools
- No additional dependencies (httpx, beautifulsoup4, duckduckgo-search)
- Smaller attack surface
- Clear separation of concerns between Claude (web) and Local Brain (local)
- If web tools are needed later, consider Smolagents with Docker sandbox for network isolation

