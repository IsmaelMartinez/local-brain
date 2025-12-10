"""Security utilities for Local Brain.

Provides path jailing, output truncation, timeouts, and other security
features to prevent unauthorized access and resource exhaustion.
"""

import signal
from functools import wraps
from pathlib import Path
from typing import TypeVar, Callable, ParamSpec

P = ParamSpec("P")
T = TypeVar("T")


# ============================================================================
# Output Truncation
# ============================================================================


def truncate_output(
    content: str,
    max_lines: int = 100,
    max_chars: int = 10000,
) -> str:
    """Clamp tool outputs with truncation metadata.

    Args:
        content: The content to potentially truncate.
        max_lines: Maximum number of lines to allow (default: 100).
        max_chars: Maximum number of characters to allow (default: 10000).

    Returns:
        The original content or truncated content with metadata.
    """
    lines = content.split("\n")
    truncated = False
    original_lines = len(lines)
    original_chars = len(content)

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        truncated = True

    result = "\n".join(lines)
    if len(result) > max_chars:
        result = result[:max_chars]
        truncated = True

    if truncated:
        result += (
            f"\n\n[TRUNCATED: {original_lines} lines, {original_chars} chars. "
            f"Output limited to {max_lines} lines / {max_chars} chars. "
            f"Use more specific queries.]"
        )

    return result


# ============================================================================
# Per-Call Timeouts
# ============================================================================


class ToolTimeoutError(Exception):
    """Raised when a tool exceeds its time limit."""

    pass


def with_timeout(seconds: int = 30) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to add a timeout to a function.

    Uses SIGALRM on Unix systems. Falls back to no timeout on Windows.

    Args:
        seconds: Maximum execution time in seconds (default: 30).

    Returns:
        Decorated function that raises ToolTimeoutError on timeout.

    Example:
        @with_timeout(10)
        def slow_function():
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Windows doesn't support SIGALRM
            if not hasattr(signal, "SIGALRM"):
                return func(*args, **kwargs)

            def handler(signum: int, frame: object) -> None:
                raise ToolTimeoutError(
                    f"Tool '{func.__name__}' timed out after {seconds} seconds"
                )

            # Set the alarm
            old_handler = signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds)
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

        return wrapper

    return decorator


# ============================================================================
# Path Jailing
# ============================================================================


# Global project root - set by CLI at startup
_PROJECT_ROOT: Path | None = None


def set_project_root(root: str | Path | None = None) -> Path:
    """Set the project root for path jailing.

    Args:
        root: Project root path. If None, uses current working directory.

    Returns:
        The resolved project root path.
    """
    global _PROJECT_ROOT

    if root is None:
        _PROJECT_ROOT = Path.cwd().resolve()
    else:
        _PROJECT_ROOT = Path(root).resolve()

    return _PROJECT_ROOT


def get_project_root() -> Path:
    """Get the current project root.

    Returns:
        The project root path, or cwd if not set.
    """
    if _PROJECT_ROOT is None:
        return Path.cwd().resolve()
    return _PROJECT_ROOT


def is_path_safe(path: str | Path) -> bool:
    """Check if a path is within the project root (jail check).

    Args:
        path: Path to check (absolute or relative).

    Returns:
        True if path is within project root, False otherwise.
    """
    root = get_project_root()

    try:
        # Resolve the path (handles .., symlinks, etc.)
        resolved = Path(path).resolve()

        # Check if it's within the project root
        resolved.relative_to(root)
        return True
    except ValueError:
        # relative_to raises ValueError if path is not relative to root
        return False


def safe_path(path: str | Path) -> Path:
    """Resolve a path and ensure it's within the project root.

    Args:
        path: Path to resolve (absolute or relative).

    Returns:
        Resolved Path object.

    Raises:
        PermissionError: If path is outside project root.
    """
    root = get_project_root()

    # Handle relative paths - resolve relative to project root
    p = Path(path)
    if not p.is_absolute():
        p = root / p

    resolved = p.resolve()

    try:
        resolved.relative_to(root)
        return resolved
    except ValueError:
        raise PermissionError(
            f"Access denied: '{path}' is outside project root '{root}'"
        )


def validate_path(path: str | Path) -> tuple[bool, str]:
    """Validate a path and return status with message.

    Args:
        path: Path to validate.

    Returns:
        Tuple of (is_valid, message).
    """
    try:
        resolved = safe_path(path)
        return True, str(resolved)
    except PermissionError as e:
        return False, str(e)


# Path patterns that are always blocked (even within project root)
BLOCKED_PATTERNS = {
    ".git/config",  # Git credentials
    ".env",  # Environment secrets
    ".env.local",
    ".env.production",
    "*.pem",  # Private keys
    "*.key",
    "id_*",
}


def is_sensitive_file(path: str | Path) -> bool:
    """Check if a file is potentially sensitive.

    Args:
        path: Path to check.

    Returns:
        True if file matches sensitive patterns.
    """
    import fnmatch

    p = Path(path)
    name = p.name
    path_str = str(p)

    # Check each pattern
    for pattern in BLOCKED_PATTERNS:
        if "*" in pattern:
            # Use fnmatch for glob patterns
            if fnmatch.fnmatch(name, pattern):
                return True
        elif name == pattern or path_str.endswith(pattern):
            return True

    return False
