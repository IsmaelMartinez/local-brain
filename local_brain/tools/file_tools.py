"""File system tools for reading and exploring files.

All file operations are restricted to the project root directory (path jailing).
"""

from datetime import datetime
from pathlib import Path

from ..security import safe_path, is_sensitive_file, get_project_root


def read_file(path: str) -> str:
    """Read the contents of a file.

    Args:
        path: Path to the file to read (absolute or relative to project root)

    Returns:
        The file contents as a string, or error message if failed
    """
    try:
        # Jail check - ensure path is within project root
        resolved = safe_path(path)
        
        # Block sensitive files
        if is_sensitive_file(resolved):
            return f"Error: Access to sensitive file '{path}' is blocked"
        
        content = resolved.read_text()
        # Truncate very large files to avoid overwhelming context
        if len(content) > 50000:
            return content[:50000] + f"\n\n... (truncated, {len(content)} total chars)"
        return content
    except PermissionError as e:
        return f"Error: {e}"
    except FileNotFoundError:
        return f"Error: File '{path}' not found"
    except Exception as e:
        return f"Error reading file: {e}"


def list_directory(path: str = ".", pattern: str = "*") -> str:
    """List files in a directory matching a pattern.

    Args:
        path: Directory path to list (default: current directory, relative to project root)
        pattern: Glob pattern to filter files (e.g., "*.py", "*.rs", "**/*.md")

    Returns:
        Newline-separated list of matching file paths, or error message
    """
    try:
        # Jail check - ensure path is within project root
        resolved = safe_path(path)
        
        if not resolved.exists():
            return f"Error: Directory '{path}' does not exist"
        if not resolved.is_dir():
            return f"Error: '{path}' is not a directory"

        # Handle recursive patterns
        files = list(resolved.glob(pattern))

        # Get project root for relative path display
        root = get_project_root()

        # Filter out hidden files and common ignore patterns
        # Also filter any files outside project root (shouldn't happen, but safety first)
        safe_files = []
        for f in files:
            # Skip hidden files/dirs
            if any(part.startswith(".") for part in f.parts):
                continue
            # Skip common non-code directories
            if any(d in f.parts for d in ("node_modules", "target", "__pycache__", ".venv")):
                continue
            # Skip sensitive files
            if is_sensitive_file(f):
                continue
            # Double-check jail (for symlinks that might escape)
            try:
                f.resolve().relative_to(root)
                safe_files.append(f)
            except ValueError:
                continue

        # Sort and limit
        safe_files = sorted(safe_files)[:100]  # Limit to 100 files

        if not safe_files:
            return f"No files matching '{pattern}' found in '{path}'"

        # Return paths relative to project root for cleaner output
        return "\n".join(str(f.relative_to(root) if f.is_relative_to(root) else f) for f in safe_files)
    except PermissionError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error listing directory: {e}"


def file_info(path: str) -> str:
    """Get information about a file (size, type, modification time).

    Args:
        path: Path to the file (relative to project root)

    Returns:
        File information as formatted string
    """
    try:
        # Jail check - ensure path is within project root
        resolved = safe_path(path)
        
        # Block sensitive files
        if is_sensitive_file(resolved):
            return f"Error: Access to sensitive file '{path}' is blocked"
        
        if not resolved.exists():
            return f"Error: File '{path}' does not exist"

        stat = resolved.stat()

        # Determine file type
        if resolved.is_dir():
            file_type = "directory"
        elif resolved.is_symlink():
            file_type = "symlink"
        else:
            file_type = resolved.suffix or "file"

        # Format size
        size = stat.st_size
        if size < 1024:
            size_str = f"{size} bytes"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"

        # Format time
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

        return f"Path: {path}\nType: {file_type}\nSize: {size_str}\nModified: {mtime}"
    except PermissionError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error getting file info: {e}"
