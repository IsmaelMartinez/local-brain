"""Smolagents-based agent for Local Brain.

Uses HuggingFace's smolagents library for code-as-tool execution
with sandboxed Python execution via LocalPythonExecutor.
"""

from smolagents import CodeAgent, LiteLLMModel, tool

from .security import safe_path, is_sensitive_file, get_project_root


# ============================================================================
# Tools - Using @tool decorator for Smolagents
# ============================================================================


@tool
def read_file(path: str) -> str:
    """Read the contents of a file.

    Args:
        path: Path to the file to read (absolute or relative to project root)

    Returns:
        The file contents as a string, or error message if failed
    """
    try:
        resolved = safe_path(path)

        if is_sensitive_file(resolved):
            return f"Error: Access to sensitive file '{path}' is blocked"

        content = resolved.read_text()
        if len(content) > 50000:
            return content[:50000] + f"\n\n... (truncated, {len(content)} total chars)"
        return content
    except PermissionError as e:
        return f"Error: {e}"
    except FileNotFoundError:
        return f"Error: File '{path}' not found"
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def list_directory(path: str = ".", pattern: str = "*") -> str:
    """List files in a directory matching a pattern.

    Args:
        path: Directory path to list (default: current directory)
        pattern: Glob pattern to filter files (e.g., "*.py", "**/*.md")

    Returns:
        Newline-separated list of matching file paths
    """
    try:
        resolved = safe_path(path)

        if not resolved.exists():
            return f"Error: Directory '{path}' does not exist"
        if not resolved.is_dir():
            return f"Error: '{path}' is not a directory"

        files = list(resolved.glob(pattern))
        root = get_project_root()

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
            return f"No files matching '{pattern}' found in '{path}'"

        return "\n".join(
            str(f.relative_to(root) if f.is_relative_to(root) else f) for f in safe_files
        )
    except PermissionError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error listing directory: {e}"


@tool
def file_info(path: str) -> str:
    """Get information about a file (size, type, modification time).

    Args:
        path: Path to the file (relative to project root)

    Returns:
        File information as formatted string
    """
    from datetime import datetime

    try:
        resolved = safe_path(path)

        if is_sensitive_file(resolved):
            return f"Error: Access to sensitive file '{path}' is blocked"

        if not resolved.exists():
            return f"Error: File '{path}' does not exist"

        stat = resolved.stat()

        if resolved.is_dir():
            file_type = "directory"
        elif resolved.is_symlink():
            file_type = "symlink"
        else:
            file_type = resolved.suffix or "file"

        size = stat.st_size
        if size < 1024:
            size_str = f"{size} bytes"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"

        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

        return f"Path: {path}\nType: {file_type}\nSize: {size_str}\nModified: {mtime}"
    except PermissionError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error getting file info: {e}"


@tool
def git_diff(staged: bool = False, file_path: str = "") -> str:
    """Get git diff output showing changes.

    Args:
        staged: If True, show only staged changes. If False, show unstaged changes.
        file_path: Optional specific file to diff (empty string for all files)

    Returns:
        Git diff output or error message
    """
    import subprocess

    args = ["git", "diff"]
    if staged:
        args.append("--cached")
    if file_path:
        args.extend(["--", file_path])

    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        if not result.stdout.strip():
            return "No changes found" + (" (staged)" if staged else " (unstaged)")
        output = result.stdout
        if len(output) > 50000:
            return output[:50000] + f"\n\n... (truncated, {len(output)} total chars)"
        return output
    except subprocess.TimeoutExpired:
        return "Error: Git command timed out"
    except FileNotFoundError:
        return "Error: Git is not installed"
    except Exception as e:
        return f"Error running git: {e}"


@tool
def git_status() -> str:
    """Get git status showing current branch and changes summary.

    Returns:
        Git status output
    """
    import subprocess

    try:
        result = subprocess.run(
            ["git", "status", "--short", "--branch"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        if not result.stdout.strip():
            return "Working tree clean"
        return result.stdout
    except subprocess.TimeoutExpired:
        return "Error: Git command timed out"
    except FileNotFoundError:
        return "Error: Git is not installed"
    except Exception as e:
        return f"Error running git: {e}"


@tool
def git_log(count: int = 10) -> str:
    """Get recent git commit history.

    Args:
        count: Number of commits to show (default: 10, max: 50)

    Returns:
        Git log output in oneline format
    """
    import subprocess

    try:
        result = subprocess.run(
            ["git", "log", f"-{min(count, 50)}", "--oneline"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        if not result.stdout.strip():
            return "No commits found"
        return result.stdout
    except subprocess.TimeoutExpired:
        return "Error: Git command timed out"
    except FileNotFoundError:
        return "Error: Git is not installed"
    except Exception as e:
        return f"Error running git: {e}"


@tool
def git_changed_files(staged: bool = False, include_untracked: bool = False) -> str:
    """Get list of changed files in the repository.

    Args:
        staged: If True, list only staged files. If False, list modified files.
        include_untracked: If True, also include untracked files

    Returns:
        Newline-separated list of changed file paths
    """
    import subprocess

    args = ["git", "diff", "--name-only", "--diff-filter=ACMR"]
    if staged:
        args.insert(2, "--cached")

    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return f"Error: {result.stderr}"

        files = [f for f in result.stdout.strip().split("\n") if f]

        if include_untracked:
            result2 = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result2.returncode == 0:
                untracked = [f for f in result2.stdout.strip().split("\n") if f]
                files.extend(untracked)

        if not files:
            return "No changed files found"

        return "\n".join(sorted(set(files)))
    except subprocess.TimeoutExpired:
        return "Error: Git command timed out"
    except FileNotFoundError:
        return "Error: Git is not installed"
    except Exception as e:
        return f"Error running git: {e}"


# All available tools
ALL_TOOLS = [
    read_file,
    list_directory,
    file_info,
    git_diff,
    git_status,
    git_log,
    git_changed_files,
]


# ============================================================================
# Agent
# ============================================================================


def create_agent(model_id: str, verbose: bool = False) -> CodeAgent:
    """Create a Smolagents CodeAgent with the configured model.

    Args:
        model_id: Ollama model ID (e.g., "qwen3:latest")
        verbose: Enable verbose output

    Returns:
        Configured CodeAgent instance
    """
    model = LiteLLMModel(
        model_id=f"ollama/{model_id}",
        api_base="http://localhost:11434",
    )

    verbosity = 2 if verbose else 0

    return CodeAgent(
        tools=ALL_TOOLS,
        model=model,
        verbosity_level=verbosity,
    )


def run_smolagent(
    prompt: str,
    model: str = "qwen3:latest",
    verbose: bool = False,
) -> str:
    """Run a task using the Smolagents CodeAgent.

    Args:
        prompt: User's request
        model: Ollama model name
        verbose: Print execution details

    Returns:
        The agent's final response
    """
    try:
        agent = create_agent(model, verbose)
        result = agent.run(prompt)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

