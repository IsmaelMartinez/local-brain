"""Git tools for working with version control."""

import subprocess
from pathlib import Path


def _run_git(*args: str) -> tuple[str, str, int]:
    """Run a git command and return stdout, stderr, return code."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Error: Git command timed out", 1
    except FileNotFoundError:
        return "", "Error: Git is not installed", 1
    except Exception as e:
        return "", f"Error running git: {e}", 1


def git_diff(staged: bool = False, file_path: str | None = None) -> str:
    """Get git diff output showing changes.
    
    Args:
        staged: If True, show only staged changes (--cached). If False, show unstaged changes.
        file_path: Optional specific file to diff
        
    Returns:
        Git diff output or error message
    """
    args = ["diff"]
    if staged:
        args.append("--cached")
    if file_path:
        args.extend(["--", file_path])
    
    stdout, stderr, code = _run_git(*args)
    
    if code != 0:
        return f"Error: {stderr}"
    if not stdout.strip():
        return "No changes found" + (" (staged)" if staged else " (unstaged)")
    
    # Truncate very large diffs
    if len(stdout) > 50000:
        return stdout[:50000] + f"\n\n... (truncated, {len(stdout)} total chars)"
    return stdout


def git_changed_files(staged: bool = False, include_untracked: bool = False) -> str:
    """Get list of changed files in the repository.
    
    Args:
        staged: If True, list only staged files. If False, list modified files.
        include_untracked: If True, also include untracked files
        
    Returns:
        Newline-separated list of changed file paths
    """
    args = ["diff", "--name-only", "--diff-filter=ACMR"]
    if staged:
        args.insert(1, "--cached")
    
    stdout, stderr, code = _run_git(*args)
    
    if code != 0:
        return f"Error: {stderr}"
    
    files = [f for f in stdout.strip().split('\n') if f]
    
    # Optionally include untracked files
    if include_untracked:
        stdout2, _, code2 = _run_git("ls-files", "--others", "--exclude-standard")
        if code2 == 0:
            untracked = [f for f in stdout2.strip().split('\n') if f]
            files.extend(untracked)
    
    if not files:
        return "No changed files found"
    
    return "\n".join(sorted(set(files)))


def git_status() -> str:
    """Get git status showing current branch and changes summary.
    
    Returns:
        Git status output
    """
    stdout, stderr, code = _run_git("status", "--short", "--branch")
    
    if code != 0:
        return f"Error: {stderr}"
    if not stdout.strip():
        return "Working tree clean"
    
    return stdout


def git_log(count: int = 10, oneline: bool = True) -> str:
    """Get recent git commit history.
    
    Args:
        count: Number of commits to show (default: 10)
        oneline: If True, show compact one-line format
        
    Returns:
        Git log output
    """
    args = ["log", f"-{min(count, 50)}"]  # Cap at 50
    if oneline:
        args.append("--oneline")
    
    stdout, stderr, code = _run_git(*args)
    
    if code != 0:
        return f"Error: {stderr}"
    if not stdout.strip():
        return "No commits found"
    
    return stdout

