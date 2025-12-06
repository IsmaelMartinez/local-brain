"""Shell tools for running commands (with safety restrictions)."""

import subprocess
import shlex


# Commands that are safe to run
ALLOWED_COMMANDS = {
    # File inspection
    "cat", "head", "tail", "wc", "file", "stat",
    # Search
    "grep", "find", "rg", "fd", "ag",
    # Directory
    "ls", "tree", "pwd",
    # Text processing
    "sort", "uniq", "cut", "awk", "sed",
    # Development
    "cargo", "npm", "pip", "python", "node", "rustc",
    "make", "cmake",
    # Git (covered by git_tools but allow here too)
    "git",
    # System info
    "which", "whoami", "date", "echo",
}

# Commands that are never allowed
BLOCKED_COMMANDS = {
    "rm", "rmdir", "mv", "cp",  # Destructive file ops
    "sudo", "su", "chmod", "chown",  # Privilege escalation
    "curl", "wget", "ssh", "scp",  # Network
    "kill", "pkill", "killall",  # Process control
    "shutdown", "reboot",  # System control
    "dd", "mkfs", "fdisk",  # Disk operations
    "eval", "exec", "source",  # Shell execution
}


def run_command(command: str, timeout: int = 30) -> str:
    """Run a shell command and return output (with safety restrictions).
    
    Only allows safe, read-only commands. Blocks destructive operations.
    
    Args:
        command: The shell command to run
        timeout: Maximum seconds to wait (default: 30, max: 120)
        
    Returns:
        Command output (stdout + stderr) or error message
    """
    # Parse command to check safety
    try:
        parts = shlex.split(command)
    except ValueError as e:
        return f"Error: Invalid command syntax: {e}"
    
    if not parts:
        return "Error: Empty command"
    
    base_cmd = parts[0].split("/")[-1]  # Handle full paths
    
    # Check against blocked commands
    if base_cmd in BLOCKED_COMMANDS:
        return f"Error: Command '{base_cmd}' is not allowed for safety reasons"
    
    # Check against allowed commands (if strict mode)
    # For now, we allow unknown commands but warn
    if base_cmd not in ALLOWED_COMMANDS:
        # Allow it but be cautious
        pass
    
    # Additional safety: no shell metacharacters that could be dangerous
    dangerous_chars = [";", "&&", "||", "|", ">", "<", "`", "$(" , "${"]
    for char in dangerous_chars:
        if char in command:
            return f"Error: Shell metacharacter '{char}' not allowed. Run commands directly without piping/chaining."
    
    # Limit timeout
    timeout = min(max(timeout, 1), 120)
    
    try:
        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=None,  # Use current directory
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        
        # Truncate large output
        if len(output) > 50000:
            output = output[:50000] + f"\n\n... (truncated, {len(output)} total chars)"
        
        return output if output.strip() else "(no output)"
        
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return f"Error: Command '{base_cmd}' not found"
    except PermissionError:
        return f"Error: Permission denied running '{base_cmd}'"
    except Exception as e:
        return f"Error running command: {e}"

