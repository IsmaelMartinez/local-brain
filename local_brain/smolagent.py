"""Smolagents-based agent for Local Brain.

Uses HuggingFace's smolagents library with CodeAgent configured to accept
markdown code blocks (```python...```) which local Ollama models naturally produce.

See ADR 005 for the rationale behind using CodeAgent with markdown tags.
"""

import subprocess
import warnings
from datetime import datetime

# Suppress smolagents warning about decorators - we use LocalPythonExecutor (not remote)
# so the serialization warning doesn't apply to our use case
warnings.filterwarnings(
    "ignore",
    message="Function .* has decorators other than @tool",
    category=UserWarning,
    module="smolagents.tools",
)

from smolagents import CodeAgent, LiteLLMModel, tool  # noqa: E402

from .security import (  # noqa: E402
    safe_path,
    is_sensitive_file,
    get_project_root,
    truncate_output,
    with_timeout,
    ToolTimeoutError,
)

# AST-aware search tools
from grep_ast import TreeContext, filename_to_lang  # noqa: E402

# Tree-sitter for extracting definitions (Python 3.13 compatible)
try:
    import tree_sitter_language_pack as ts_langs
except ImportError:
    import tree_sitter_languages as ts_langs  # type: ignore


# ============================================================================
# Configuration
# ============================================================================

# Default limits for tool outputs
DEFAULT_MAX_LINES = 200
DEFAULT_MAX_CHARS = 20000
DEFAULT_TIMEOUT_SECONDS = 30


# ============================================================================
# Tools - Using @tool decorator for Smolagents
# ============================================================================


@tool
@with_timeout(DEFAULT_TIMEOUT_SECONDS)
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
        return truncate_output(
            content, max_lines=DEFAULT_MAX_LINES, max_chars=DEFAULT_MAX_CHARS
        )
    except PermissionError as e:
        return f"Error: {e}"
    except FileNotFoundError:
        return f"Error: File '{path}' not found"
    except ToolTimeoutError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error reading file: {e}"


@tool
@with_timeout(DEFAULT_TIMEOUT_SECONDS)
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
            if any(
                d in f.parts for d in ("node_modules", "target", "__pycache__", ".venv")
            ):
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

        result = "\n".join(
            str(f.relative_to(root) if f.is_relative_to(root) else f)
            for f in safe_files
        )
        return truncate_output(
            result, max_lines=DEFAULT_MAX_LINES, max_chars=DEFAULT_MAX_CHARS
        )
    except PermissionError as e:
        return f"Error: {e}"
    except ToolTimeoutError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error listing directory: {e}"


@tool
@with_timeout(DEFAULT_TIMEOUT_SECONDS)
def file_info(path: str) -> str:
    """Get information about a file (size, type, modification time).

    Args:
        path: Path to the file (relative to project root)

    Returns:
        File information as formatted string
    """
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
    except ToolTimeoutError as e:
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
    args = ["git", "diff"]
    if staged:
        args.append("--cached")
    if file_path:
        args.extend(["--", file_path])

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            cwd=get_project_root(),
        )
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        if not result.stdout.strip():
            return "No changes found" + (" (staged)" if staged else " (unstaged)")
        return truncate_output(
            result.stdout, max_lines=DEFAULT_MAX_LINES, max_chars=DEFAULT_MAX_CHARS
        )
    except subprocess.TimeoutExpired:
        return f"Error: Git command timed out after {DEFAULT_TIMEOUT_SECONDS}s"
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
    try:
        result = subprocess.run(
            ["git", "status", "--short", "--branch"],
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            cwd=get_project_root(),
        )
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        if not result.stdout.strip():
            return "Working tree clean"
        return truncate_output(
            result.stdout, max_lines=DEFAULT_MAX_LINES, max_chars=DEFAULT_MAX_CHARS
        )
    except subprocess.TimeoutExpired:
        return f"Error: Git command timed out after {DEFAULT_TIMEOUT_SECONDS}s"
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
    try:
        result = subprocess.run(
            ["git", "log", f"-{min(count, 50)}", "--oneline"],
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            cwd=get_project_root(),
        )
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        if not result.stdout.strip():
            return "No commits found"
        return truncate_output(
            result.stdout, max_lines=DEFAULT_MAX_LINES, max_chars=DEFAULT_MAX_CHARS
        )
    except subprocess.TimeoutExpired:
        return f"Error: Git command timed out after {DEFAULT_TIMEOUT_SECONDS}s"
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
    args = ["git", "diff", "--name-only", "--diff-filter=ACMR"]
    if staged:
        args.insert(2, "--cached")

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            cwd=get_project_root(),
        )
        if result.returncode != 0:
            return f"Error: {result.stderr}"

        files = [f for f in result.stdout.strip().split("\n") if f]

        if include_untracked:
            result2 = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                timeout=DEFAULT_TIMEOUT_SECONDS,
                cwd=get_project_root(),
            )
            if result2.returncode == 0:
                untracked = [f for f in result2.stdout.strip().split("\n") if f]
                files.extend(untracked)

        if not files:
            return "No changed files found"

        output = "\n".join(sorted(set(files)))
        return truncate_output(
            output, max_lines=DEFAULT_MAX_LINES, max_chars=DEFAULT_MAX_CHARS
        )
    except subprocess.TimeoutExpired:
        return f"Error: Git command timed out after {DEFAULT_TIMEOUT_SECONDS}s"
    except FileNotFoundError:
        return "Error: Git is not installed"
    except Exception as e:
        return f"Error running git: {e}"


# ============================================================================
# AST-Aware Navigation Tools (Phase B)
# ============================================================================


def _simple_grep(pattern: str, content: str, ignore_case: bool = True) -> str:
    """Fallback simple grep for non-parseable files."""
    import re

    flags = re.IGNORECASE if ignore_case else 0
    matches = []
    for i, line in enumerate(content.split("\n"), 1):
        if re.search(pattern, line, flags):
            matches.append(f"{i}: {line}")
    return "\n".join(matches) if matches else f"No matches for '{pattern}'"


@tool
@with_timeout(DEFAULT_TIMEOUT_SECONDS)
def search_code(pattern: str, file_path: str, ignore_case: bool = True) -> str:
    """Search code with AST awareness - shows intelligent context around matches.

    Unlike simple grep, this tool understands code structure and shows
    relevant context like function/class boundaries around matches.

    Args:
        pattern: Text pattern to search for (supports regex)
        file_path: File to search in (absolute or relative to project root)
        ignore_case: Whether to ignore case in search (default: True)

    Returns:
        Matches with AST-aware context showing function/class boundaries
    """
    try:
        resolved = safe_path(file_path)

        if is_sensitive_file(resolved):
            return f"Error: Access to sensitive file '{file_path}' is blocked"

        if not resolved.exists():
            return f"Error: File '{file_path}' not found"

        if not resolved.is_file():
            return f"Error: '{file_path}' is not a file"

        content = resolved.read_text()

        # Check if language is supported for AST parsing
        lang = filename_to_lang(str(resolved))
        if not lang:
            # Fall back to simple grep for unsupported languages
            result = _simple_grep(pattern, content, ignore_case)
            return truncate_output(
                result, max_lines=DEFAULT_MAX_LINES, max_chars=DEFAULT_MAX_CHARS
            )

        # Use AST-aware grep
        # grep() returns a set of line numbers where matches were found
        tc = TreeContext(str(resolved), code=content)
        lines_of_interest = tc.grep(pattern, ignore_case=ignore_case)

        if not lines_of_interest:
            return f"No matches for '{pattern}' in {file_path}"

        # Add matched lines and surrounding AST context
        tc.add_lines_of_interest(lines_of_interest)
        tc.add_context()
        result = tc.format()

        if not result or not result.strip():
            return f"No matches for '{pattern}' in {file_path}"

        return truncate_output(
            result, max_lines=DEFAULT_MAX_LINES, max_chars=DEFAULT_MAX_CHARS
        )
    except PermissionError as e:
        return f"Error: {e}"
    except ToolTimeoutError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error searching code: {e}"


# Supported languages for tree-sitter parsing
SUPPORTED_LANGUAGES = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
}


def _get_docstring(node, code_bytes: bytes) -> str | None:
    """Extract docstring from a class/function node."""
    import ast

    # Find the body/block - could be named "body" or be a "block" child
    body = node.child_by_field_name("body")
    if body is None:
        # Look for block child directly
        for child in node.children:
            if child.type == "block":
                body = child
                break

    if not (body and body.children):
        return None

    # First child of body could be expression_statement (Python) or string directly
    first = body.children[0]
    string_node = None
    if first.type == "expression_statement" and first.children:
        string_node = first.children[0]
    elif first.type == "string":
        string_node = first

    if string_node and string_node.type == "string":
        try:
            # Use ast.literal_eval for robust parsing of string literals.
            # It handles all quote types, prefixes (r, f, u), and escapes.
            doc = ast.literal_eval(string_node.text.decode())
            return doc[:80] + "..." if len(doc) > 80 else doc
        except (ValueError, SyntaxError):
            # Silently skip malformed docstrings - this can happen with:
            # - Incomplete/malformed string literals in parsed code
            # - Edge cases tree-sitter parses but ast.literal_eval rejects
            # Returning None is acceptable since docstrings are optional metadata
            return None

    return None


def _extract_python_definitions(tree, code_bytes: bytes) -> list[str]:
    """Extract Python class/function definitions."""
    output_lines: list[str] = []

    def walk(node, indent: int = 0):
        prefix = "  " * indent

        if node.type == "class_definition":
            name = node.child_by_field_name("name")
            if name:
                output_lines.append(f"{prefix}class {name.text.decode()}:")
                doc = _get_docstring(node, code_bytes)
                if doc:
                    output_lines.append(f'{prefix}  "{doc}"')
                # Process methods - get body directly instead of iterating all children
                body = node.child_by_field_name("body")
                if body:
                    for child in body.children:
                        walk(child, indent + 1)
                # Early return is intentional: we've already processed the class body above,
                # so we skip the generic child iteration below to avoid double-processing.
                # Sibling definitions at the same level are handled by the parent's walk loop.
                return

        elif node.type == "function_definition":
            name = node.child_by_field_name("name")
            params = node.child_by_field_name("parameters")
            ret = node.child_by_field_name("return_type")

            if name:
                sig = f"def {name.text.decode()}"
                if params:
                    sig += params.text.decode()
                if ret:
                    sig += f" -> {ret.text.decode()}"
                sig += ":"
                output_lines.append(f"{prefix}{sig}")
                doc = _get_docstring(node, code_bytes)
                if doc:
                    output_lines.append(f'{prefix}  "{doc}"')
                # Early return skips function body - we only want signatures, not implementation
                return

        for child in node.children:
            walk(child, indent)

    walk(tree.root_node)
    return output_lines


@tool
@with_timeout(DEFAULT_TIMEOUT_SECONDS)
def list_definitions(file_path: str) -> str:
    """Extract class and function definitions from a source file.

    Returns a compact overview of all classes and functions with their
    signatures and docstrings, without the full implementation code.
    Useful for understanding file structure without reading entire contents.

    Args:
        file_path: Path to the source file (absolute or relative to project root)

    Returns:
        List of classes/functions with signatures and docstrings
    """
    try:
        resolved = safe_path(file_path)

        if is_sensitive_file(resolved):
            return f"Error: Access to sensitive file '{file_path}' is blocked"

        if not resolved.exists():
            return f"Error: File '{file_path}' not found"

        if not resolved.is_file():
            return f"Error: '{file_path}' is not a file"

        # Check if language is supported
        suffix = resolved.suffix.lower()
        lang = SUPPORTED_LANGUAGES.get(suffix)

        if not lang:
            return f"Error: Unsupported language for '{file_path}'. Supported: {', '.join(SUPPORTED_LANGUAGES.keys())}"

        content = resolved.read_text()
        code_bytes = content.encode()

        try:
            parser = ts_langs.get_parser(lang)  # type: ignore[arg-type]
            tree = parser.parse(code_bytes)
        except Exception as e:
            return f"Error parsing {file_path}: {e}"

        # Currently only Python extraction is fully implemented
        if lang == "python":
            output_lines = _extract_python_definitions(tree, code_bytes)
        else:
            # For other languages, provide basic node type extraction
            output_lines = []

            def walk_generic(node, indent: int = 0):
                prefix = "  " * indent
                # Generic extraction for common definition types
                if node.type in (
                    "function_definition",
                    "function_declaration",
                    "method_definition",
                    "method_declaration",
                    "class_definition",
                    "class_declaration",
                    "struct_item",
                    "impl_item",
                ):
                    # Get the first line of the definition
                    start = node.start_byte
                    end_of_first_line = content.find("\n", start)
                    if end_of_first_line == -1:
                        end_of_first_line = node.end_byte
                    first_line = code_bytes[start:end_of_first_line].decode().strip()
                    output_lines.append(f"{prefix}{first_line}")

                for child in node.children:
                    walk_generic(child, indent)

            walk_generic(tree.root_node)

        if not output_lines:
            return f"No definitions found in {file_path}"

        result = "\n".join(output_lines)
        return truncate_output(
            result, max_lines=DEFAULT_MAX_LINES, max_chars=DEFAULT_MAX_CHARS
        )
    except PermissionError as e:
        return f"Error: {e}"
    except ToolTimeoutError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error extracting definitions: {e}"


# All available tools
ALL_TOOLS = [
    read_file,
    list_directory,
    file_info,
    git_diff,
    git_status,
    git_log,
    git_changed_files,
    search_code,
    list_definitions,
]


# ============================================================================
# Agent
# ============================================================================


def create_agent(model_id: str, verbose: bool = False) -> CodeAgent:
    """Create a Smolagents CodeAgent with the configured model.

    Uses CodeAgent with markdown code block tags to work with local Ollama models
    that naturally output ```python...``` format instead of <code>...</code> XML.

    Args:
        model_id: Ollama model ID (e.g., "qwen3:latest")
        verbose: Enable verbose output

    Returns:
        Configured CodeAgent instance
    """
    model = LiteLLMModel(
        model_id=f"ollama_chat/{model_id}",
        api_base="http://localhost:11434",
        num_ctx=8192,  # Increase context window from default 2048
    )

    verbosity = 2 if verbose else 0

    return CodeAgent(
        tools=ALL_TOOLS,
        model=model,
        verbosity_level=verbosity,
        code_block_tags="markdown",  # Accept markdown code blocks from local models
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
