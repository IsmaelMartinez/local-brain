"""File system tools for reading and exploring files."""

from datetime import datetime
from pathlib import Path


def read_file(path: str) -> str:
    """Read the contents of a file.

    Args:
        path: Path to the file to read (absolute or relative)

    Returns:
        The file contents as a string, or error message if failed
    """
    try:
        content = Path(path).read_text()
        # Truncate very large files to avoid overwhelming context
        if len(content) > 50000:
            return content[:50000] + f"\n\n... (truncated, {len(content)} total chars)"
        return content
    except FileNotFoundError:
        return f"Error: File '{path}' not found"
    except PermissionError:
        return f"Error: Permission denied reading '{path}'"
    except Exception as e:
        return f"Error reading file: {e}"


def list_directory(path: str = ".", pattern: str = "*") -> str:
    """List files in a directory matching a pattern.

    Args:
        path: Directory path to list (default: current directory)
        pattern: Glob pattern to filter files (e.g., "*.py", "*.rs", "**/*.md")

    Returns:
        Newline-separated list of matching file paths, or error message
    """
    try:
        p = Path(path)
        if not p.exists():
            return f"Error: Directory '{path}' does not exist"
        if not p.is_dir():
            return f"Error: '{path}' is not a directory"

        # Handle recursive patterns
        if "**" in pattern:
            files = list(p.glob(pattern))
        else:
            files = list(p.glob(pattern))

        # Filter out hidden files and common ignore patterns
        files = [
            f
            for f in files
            if not any(part.startswith(".") for part in f.parts)
            and "node_modules" not in f.parts
            and "target" not in f.parts
            and "__pycache__" not in f.parts
            and ".venv" not in f.parts
        ]

        # Sort and limit
        files = sorted(files)[:100]  # Limit to 100 files

        if not files:
            return f"No files matching '{pattern}' found in '{path}'"

        return "\n".join(str(f) for f in files)
    except Exception as e:
        return f"Error listing directory: {e}"


def file_info(path: str) -> str:
    """Get information about a file (size, type, modification time).

    Args:
        path: Path to the file

    Returns:
        File information as formatted string
    """
    try:
        p = Path(path)
        if not p.exists():
            return f"Error: File '{path}' does not exist"

        stat = p.stat()

        # Determine file type
        if p.is_dir():
            file_type = "directory"
        elif p.is_symlink():
            file_type = "symlink"
        else:
            file_type = p.suffix or "file"

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
    except Exception as e:
        return f"Error getting file info: {e}"
