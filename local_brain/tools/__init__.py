"""Built-in tools for Local Brain.

Tools are Python functions that models can call to interact with the environment.
Each tool must have:
- Type hints for all parameters
- A docstring with Args section describing each parameter
- Return type hint

The ollama-python library automatically generates JSON schemas from these.
"""

from typing import Callable

from .file_tools import read_file, list_directory, file_info
from .git_tools import git_diff, git_changed_files, git_status, git_log
from .shell_tools import run_command

# Tool registry - maps tool names to functions (read-only for security)
TOOL_REGISTRY: dict[str, Callable[..., str]] = {
    # File tools (read-only)
    "read_file": read_file,
    "list_directory": list_directory,
    "file_info": file_info,
    # Git tools
    "git_diff": git_diff,
    "git_changed_files": git_changed_files,
    "git_status": git_status,
    "git_log": git_log,
    # Shell tools
    "run_command": run_command,
}

# All tools as a list (for passing to ollama.chat)
ALL_TOOLS = list(TOOL_REGISTRY.values())


def get_tools(tool_names: list[str] | None = None) -> list:
    """Get tool functions by name.

    Args:
        tool_names: List of tool names to get. If None, returns all tools.

    Returns:
        List of tool functions.
    """
    if tool_names is None:
        return ALL_TOOLS
    return [TOOL_REGISTRY[name] for name in tool_names if name in TOOL_REGISTRY]
