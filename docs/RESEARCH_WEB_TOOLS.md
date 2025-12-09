# Research: Web Tools for Local Brain

## Overview

This document explores adding web browsing and search capabilities to local-brain.

**Status:** Research / Future Enhancement

## Current State

Local-brain currently has read-only tools for local codebase exploration:
- File tools: `read_file`, `list_directory`, `file_info`
- Git tools: `git_diff`, `git_status`, `git_changed_files`, `git_log`
- Shell tools: `run_command` (restricted allow-list)

## Proposed Web Tools

### 1. Web Search

**Purpose:** Search the internet for information, documentation, examples.

**Options:**

| Library | Pros | Cons |
|---------|------|------|
| `duckduckgo-search` | Free, no API key | Rate limits, less reliable |
| `serpapi` | Reliable, structured | Requires API key, paid |
| `tavily` | AI-optimized results | Requires API key |
| `googlesearch-python` | Direct Google | May break, ToS concerns |

**Example Implementation:**

```python
from duckduckgo_search import DDGS

def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for information.
    
    Args:
        query: Search query
        max_results: Maximum results to return (default: 5)
        
    Returns:
        Search results as formatted string
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        if not results:
            return "No results found"
        
        output = []
        for r in results:
            output.append(f"**{r['title']}**")
            output.append(f"URL: {r['href']}")
            output.append(f"{r['body']}\n")
        
        return "\n".join(output)
    except Exception as e:
        return f"Error: {e}"
```

### 2. URL Fetching

**Purpose:** Fetch and extract text content from web pages.

**Options:**

| Library | Pros | Cons |
|---------|------|------|
| `httpx` + `beautifulsoup4` | Full control | More code |
| `trafilatura` | Clean text extraction | Another dependency |
| `newspaper3k` | Article-focused | May not work on all pages |
| `requests-html` | JavaScript support | Heavy, Chromium needed |

**Example Implementation:**

```python
import httpx
from bs4 import BeautifulSoup

def fetch_url(url: str, max_length: int = 10000) -> str:
    """Fetch and extract text content from a URL.
    
    Args:
        url: URL to fetch
        max_length: Maximum characters to return (default: 10000)
        
    Returns:
        Extracted text content or error message
    """
    try:
        response = httpx.get(url, timeout=10, follow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        
        text = soup.get_text(separator="\n", strip=True)
        
        if len(text) > max_length:
            text = text[:max_length] + "\n\n... (truncated)"
        
        return text
    except Exception as e:
        return f"Error fetching URL: {e}"
```

## Security Considerations

### Risks

1. **Data exfiltration**: Model could fetch attacker-controlled URLs containing instructions
2. **SSRF attacks**: Fetching internal URLs (localhost, private IPs)
3. **Resource exhaustion**: Large pages, infinite redirects
4. **Privacy**: Sending user queries to external services

### Mitigations

```python
# URL validation
BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "169.254."}
BLOCKED_SCHEMES = {"file", "ftp", "data"}

def is_safe_url(url: str) -> bool:
    """Check if URL is safe to fetch."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    
    if parsed.scheme not in ("http", "https"):
        return False
    if any(parsed.netloc.startswith(h) for h in BLOCKED_HOSTS):
        return False
    # Add more checks as needed
    return True
```

## Dependencies

Adding web tools would require new dependencies:

```toml
# pyproject.toml
dependencies = [
    "ollama>=0.6.1",
    "click>=8.0.0",
    # Web tools (optional)
    "httpx>=0.27.0",
    "beautifulsoup4>=4.12.0",
    "duckduckgo-search>=6.0.0",  # or alternative
]
```

## Alternative: MCP Integration

Instead of building tools directly, we could integrate with **Model Context Protocol (MCP)** servers that provide web capabilities:

- Anthropic's MCP specification allows tools to be provided by external servers
- Several MCP servers exist for web browsing
- Keeps local-brain focused on the agent loop

**Pros:** Separation of concerns, reusable tools
**Cons:** Additional infrastructure, complexity

## Recommendation

### Phase 1: Basic Web Search (Optional Feature)
- Add `duckduckgo-search` as optional dependency
- Implement `web_search` tool with rate limiting
- Add `--web` flag to enable web tools

### Phase 2: URL Fetching (If Needed)
- Add `httpx` + `beautifulsoup4`
- Implement `fetch_url` with security checks
- Consider read-only documentation sites only

### Phase 3: Consider MCP
- Evaluate if MCP integration makes sense
- Could replace custom web tools

## References

- [DuckDuckGo Search Library](https://github.com/deedy5/duckduckgo_search)
- [Trafilatura](https://github.com/adbar/trafilatura)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Ollama Tool Calling](https://ollama.com/search?c=tool)




