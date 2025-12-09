"""Shell tools for running commands (with strict safety restrictions).

All commands are executed within the project root directory (path jailing).
"""

import shlex
import subprocess

from ..security import get_project_root, is_path_safe

# Commands that are explicitly allowed (default-deny posture)
ALLOWED_COMMANDS = {
    # File inspection (read-only)
    "cat",
    "head",
    "tail",
    "wc",
    "file",
    "stat",
    # Search (read-only)
    "grep",
    "find",
    "rg",
    "fd",
    "ag",
    # Directory listing (read-only)
    "ls",
    "tree",
    "pwd",
    # Text processing (read-only)
    "sort",
    "uniq",
    "cut",
    # System info (read-only)
    "which",
    "whoami",
    "date",
    "echo",
    # Git (read-only operations)
    "git",
}

# Commands that are explicitly blocked (extra safety layer)
BLOCKED_COMMANDS = {
    # Destructive file operations
    "rm",
    "rmdir",
    "mv",
    "cp",
    "touch",
    "mkdir",
    # Privilege escalation
    "sudo",
    "su",
    "chmod",
    "chown",
    "chgrp",
    # Network operations
    "curl",
    "wget",
    "ssh",
    "scp",
    "rsync",
    "nc",
    "netcat",
    # Process control
    "kill",
    "pkill",
    "killall",
    "nohup",
    # System control
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
    # Disk operations
    "dd",
    "mkfs",
    "fdisk",
    "mount",
    "umount",
    # Shell execution / interpreters (prevent bypass)
    "bash",
    "sh",
    "zsh",
    "fish",
    "csh",
    "tcsh",
    "ksh",
    "dash",
    "eval",
    "exec",
    "source",
    "python",
    "python3",
    "node",
    "ruby",
    "perl",
    "php",
    # Package managers (can install arbitrary code)
    "pip",
    "npm",
    "yarn",
    "cargo",
    "gem",
    "apt",
    "brew",
    # Editors (interactive)
    "vi",
    "vim",
    "nano",
    "emacs",
    # Dangerous text processors
    "awk",
    "sed",
}


def _validate_path_arguments(parts: list[str]) -> str | None:
    """Validate that path arguments don't escape the project root.

    Args:
        parts: Command parts (command + arguments).

    Returns:
        Error message if validation fails, None if valid.
    """
    # Skip the command itself, check arguments that look like paths
    for arg in parts[1:]:
        # Skip flags
        if arg.startswith("-"):
            continue
        # Skip non-path-like arguments
        if not any(c in arg for c in ["/", "\\", ".."]):
            continue
        # Check if it looks like a path and validate it
        if "/" in arg or "\\" in arg or arg.startswith(".."):
            if not is_path_safe(arg):
                return f"Error: Path '{arg}' is outside project root"
    return None


def run_command(command: str, timeout: int = 30) -> str:
    """Run a safe, read-only shell command and return output.

    Only allows explicitly approved commands. Blocks all others.
    All commands are executed within the project root directory.

    Args:
        command: The shell command to run
        timeout: Maximum seconds to wait (default: 30, max: 60)

    Returns:
        Command output (stdout + stderr) or error message
    """
    # Parse command
    try:
        parts = shlex.split(command)
    except ValueError as e:
        return f"Error: Invalid command syntax: {e}"

    if not parts:
        return "Error: Empty command"

    base_cmd = parts[0].split("/")[-1]  # Handle full paths like /bin/ls

    # Check against blocked commands first
    if base_cmd in BLOCKED_COMMANDS:
        return f"Error: Command '{base_cmd}' is blocked for security reasons"

    # Strict allow-list enforcement (default-deny)
    if base_cmd not in ALLOWED_COMMANDS:
        return f"Error: Command '{base_cmd}' is not in the allowed list. Allowed: {', '.join(sorted(ALLOWED_COMMANDS))}"

    # Block dangerous shell metacharacters
    dangerous_patterns = [";", "&&", "||", "|", ">", "<", "`", "$(", "${", "\n"]
    for pattern in dangerous_patterns:
        if pattern in command:
            return f"Error: Shell metacharacter '{pattern}' not allowed"

    # Validate path arguments don't escape project root
    path_error = _validate_path_arguments(parts)
    if path_error:
        return path_error

    # Limit timeout
    timeout = min(max(timeout, 1), 60)

    # Get project root for cwd
    project_root = get_project_root()

    try:
        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(project_root),  # Execute within project root
        )

        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"

        # Truncate large output
        if len(output) > 50000:
            output = output[:50000] + f"\n\n... (truncated, {len(output)} total chars)"

        return output.strip() if output.strip() else "(no output)"

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return f"Error: Command '{base_cmd}' not found"
    except PermissionError:
        return f"Error: Permission denied running '{base_cmd}'"
    except Exception as e:
        return f"Error running command: {e}"
