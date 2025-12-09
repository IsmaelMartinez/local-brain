"""Security utilities for Local Brain.

Provides path jailing and other security features to prevent
unauthorized access outside the project root.
"""

from pathlib import Path


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
    ".git/config",      # Git credentials
    ".env",             # Environment secrets
    ".env.local",
    ".env.production",
    "*.pem",            # Private keys
    "*.key",
    "id_rsa",
    "id_ed25519",
}


def is_sensitive_file(path: str | Path) -> bool:
    """Check if a file is potentially sensitive.
    
    Args:
        path: Path to check.
        
    Returns:
        True if file matches sensitive patterns.
    """
    p = Path(path)
    name = p.name
    
    # Check exact matches
    for pattern in BLOCKED_PATTERNS:
        if "*" in pattern:
            # Simple glob matching
            if name.endswith(pattern.replace("*", "")):
                return True
        elif name == pattern or str(p).endswith(pattern):
            return True
    
    return False

