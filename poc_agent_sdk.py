"""Proof-of-concept: Local Brain using Claude Agent SDK with Ollama.

This POC demonstrates migrating from Smolagents to Claude Agent SDK while:
1. Preserving all security features (path jailing, timeouts, etc.)
2. Using Ollama as the backend via Anthropic API compatibility
3. Eliminating the CLI binary dependency

Usage:
    export ANTHROPIC_BASE_URL=http://localhost:11434
    export ANTHROPIC_API_KEY=ollama
    uv pip install claude-agent-sdk
    uv run python poc_agent_sdk.py
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Any

# Import security utilities from existing codebase
from local_brain.security import (
    safe_path,
    is_sensitive_file,
    get_project_root,
    truncate_output,
    with_timeout,
    ToolTimeoutError,
    set_project_root,
)

# Claude Agent SDK imports
try:
    from claude_agent_sdk import (
        ClaudeSDKClient,
        ClaudeAgentOptions,
        tool,
        create_sdk_mcp_server,
        AssistantMessage,
        TextBlock,
    )
except ImportError:
    print("Error: claude-agent-sdk not installed")
    print("Install with: uv pip install claude-agent-sdk")
    exit(1)


# ============================================================================
# Security-Wrapped Tools (Ported from smolagent.py)
# ============================================================================

DEFAULT_MAX_LINES = 200
DEFAULT_MAX_CHARS = 20000
DEFAULT_TIMEOUT_SECONDS = 30


@tool("read_file", "Read a file from disk (path-jailed to project root)", {"path": str})
async def read_file(args: dict[str, Any]) -> dict[str, Any]:
    """Read file with path jailing and security checks.

    Reuses existing security.py logic - identical to Smolagents version.
    """
    path = args["path"]

    try:
        # Use existing security checks
        resolved = safe_path(path)

        if is_sensitive_file(resolved):
            error_msg = f"Error: Access to sensitive file '{path}' is blocked"
            return {"content": [{"type": "text", "text": error_msg}], "isError": True}

        content = resolved.read_text()
        truncated = truncate_output(
            content, max_lines=DEFAULT_MAX_LINES, max_chars=DEFAULT_MAX_CHARS
        )

        return {"content": [{"type": "text", "text": truncated}]}

    except PermissionError as e:
        return {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}
    except FileNotFoundError:
        error_msg = f"Error: File '{path}' not found"
        return {"content": [{"type": "text", "text": error_msg}], "isError": True}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error reading file: {e}"}], "isError": True}


@tool("list_directory", "List files matching a pattern", {"path": str, "pattern": str})
async def list_directory(args: dict[str, Any]) -> dict[str, Any]:
    """List files with path jailing and filtering."""
    path = args.get("path", ".")
    pattern = args.get("pattern", "*")

    try:
        resolved = safe_path(path)

        if not resolved.exists():
            error_msg = f"Error: Directory '{path}' does not exist"
            return {"content": [{"type": "text", "text": error_msg}], "isError": True}

        if not resolved.is_dir():
            error_msg = f"Error: '{path}' is not a directory"
            return {"content": [{"type": "text", "text": error_msg}], "isError": True}

        files = list(resolved.glob(pattern))
        root = get_project_root()

        # Filter out hidden files, node_modules, etc.
        safe_files = []
        for f in files:
            if any(part.startswith(".") for part in f.parts):
                continue
            if any(d in f.parts for d in ("node_modules", "target", "__pycache__", ".venv")):
                continue
            if is_sensitive_file(f):
                continue
            try:
                f.resolve().relative_to(root)
                safe_files.append(f)
            except ValueError:
                continue

        safe_files = sorted(safe_files)[:100]

        if not safe_files:
            msg = f"No files matching '{pattern}' found in '{path}'"
            return {"content": [{"type": "text", "text": msg}]}

        result = "\n".join(
            str(f.relative_to(root) if f.is_relative_to(root) else f)
            for f in safe_files
        )
        truncated = truncate_output(
            result, max_lines=DEFAULT_MAX_LINES, max_chars=DEFAULT_MAX_CHARS
        )

        return {"content": [{"type": "text", "text": truncated}]}

    except PermissionError as e:
        return {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error listing directory: {e}"}], "isError": True}


@tool("git_diff", "Get git diff", {"staged": bool, "file_path": str})
async def git_diff(args: dict[str, Any]) -> dict[str, Any]:
    """Get git diff with timeout protection."""
    staged = args.get("staged", False)
    file_path = args.get("file_path", "")

    git_args = ["git", "diff"]
    if staged:
        git_args.append("--cached")
    if file_path:
        git_args.extend(["--", file_path])

    try:
        result = subprocess.run(
            git_args,
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            cwd=get_project_root(),
        )

        if result.returncode != 0:
            error_msg = f"Error: {result.stderr}"
            return {"content": [{"type": "text", "text": error_msg}], "isError": True}

        if not result.stdout.strip():
            msg = "No changes found" + (" (staged)" if staged else " (unstaged)")
            return {"content": [{"type": "text", "text": msg}]}

        truncated = truncate_output(
            result.stdout, max_lines=DEFAULT_MAX_LINES, max_chars=DEFAULT_MAX_CHARS
        )

        return {"content": [{"type": "text", "text": truncated}]}

    except subprocess.TimeoutExpired:
        error_msg = f"Error: Git command timed out after {DEFAULT_TIMEOUT_SECONDS}s"
        return {"content": [{"type": "text", "text": error_msg}], "isError": True}
    except FileNotFoundError:
        return {"content": [{"type": "text", "text": "Error: Git is not installed"}], "isError": True}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error running git: {e}"}], "isError": True}


@tool("git_status", "Get git status", {})
async def git_status(args: dict[str, Any]) -> dict[str, Any]:
    """Get git status."""
    try:
        result = subprocess.run(
            ["git", "status", "--short", "--branch"],
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            cwd=get_project_root(),
        )

        if result.returncode != 0:
            error_msg = f"Error: {result.stderr}"
            return {"content": [{"type": "text", "text": error_msg}], "isError": True}

        if not result.stdout.strip():
            return {"content": [{"type": "text", "text": "Working tree clean"}]}

        truncated = truncate_output(
            result.stdout, max_lines=DEFAULT_MAX_LINES, max_chars=DEFAULT_MAX_CHARS
        )

        return {"content": [{"type": "text", "text": truncated}]}

    except subprocess.TimeoutExpired:
        error_msg = f"Error: Git command timed out after {DEFAULT_TIMEOUT_SECONDS}s"
        return {"content": [{"type": "text", "text": error_msg}], "isError": True}
    except FileNotFoundError:
        return {"content": [{"type": "text", "text": "Error: Git is not installed"}], "isError": True}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error running git: {e}"}], "isError": True}


# ============================================================================
# Agent Creation
# ============================================================================


async def run_local_brain(prompt: str, model: str = "qwen3-coder:30b", verbose: bool = False):
    """Run Local Brain agent using Claude Agent SDK with Ollama backend.

    Args:
        prompt: User's query
        model: Ollama model name
        verbose: Print detailed output
    """
    # Set up project root for path jailing
    set_project_root()

    # Create MCP server with our security-wrapped tools
    tools_server = create_sdk_mcp_server(
        name="local-brain-tools",
        version="0.9.0",
        tools=[read_file, list_directory, git_diff, git_status],
    )

    # Configure agent options
    options = ClaudeAgentOptions(
        system_prompt=(
            "You are a codebase exploration assistant using local Ollama models. "
            "You have access to read-only tools for exploring code: read_file, "
            "list_directory, git_diff, and git_status. All file operations are "
            "path-jailed to the project root for security."
        ),
        model=model,
        mcp_servers={"tools": tools_server},
        allowed_tools=[
            "mcp__tools__read_file",
            "mcp__tools__list_directory",
            "mcp__tools__git_diff",
            "mcp__tools__git_status",
        ],
        cwd=str(get_project_root()),
    )

    print(f"[POC] Using model: {model}")
    print(f"[POC] Project root: {get_project_root()}")
    print(f"[POC] ANTHROPIC_BASE_URL: {os.getenv('ANTHROPIC_BASE_URL', 'not set')}")
    print(f"[POC] Query: {prompt}\n")

    # Create and run agent
    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(block.text)
                elif verbose:
                    print(f"[DEBUG] {message}")

    except Exception as e:
        print(f"Error running agent: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# CLI Interface
# ============================================================================


async def main():
    """POC entry point."""
    import os
    import sys

    # Check environment
    if not os.getenv("ANTHROPIC_BASE_URL"):
        print("ERROR: ANTHROPIC_BASE_URL not set")
        print("Run: export ANTHROPIC_BASE_URL=http://localhost:11434")
        print("     export ANTHROPIC_API_KEY=ollama")
        sys.exit(1)

    # Simple test prompt
    test_prompt = "List all Python files in this project and read the README.md file"

    if len(sys.argv) > 1:
        test_prompt = " ".join(sys.argv[1:])

    await run_local_brain(test_prompt, verbose=True)


if __name__ == "__main__":
    asyncio.run(main())
