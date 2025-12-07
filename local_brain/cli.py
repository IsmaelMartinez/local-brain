"""Local Brain - Chat with local Ollama models that can use tools."""

import sys
import click
from pathlib import Path

from . import __version__
from .agent import run_agent
from .tools import ALL_TOOLS


SYSTEM_PROMPT = """You are a helpful assistant with access to tools for exploring codebases.

Use tools to help answer questions:
- read_file: Read file contents
- list_directory: List files (supports glob patterns)
- git_diff: See code changes
- git_status: Check repo status
- run_command: Run safe shell commands

Be concise and helpful."""

REVIEW_SYSTEM = """You are a code reviewer. Analyze the code and provide feedback as:

## Issues Found
- **Title**: Description (with line numbers)

## Simplifications  
- Opportunities to simplify

## Other
- General observations

Be concise (1-2 sentences per item)."""

COMMIT_SYSTEM = """Generate a git commit message from staged changes.

Use git_diff(staged=True) to see changes, then output ONLY the commit message:

<type>(<scope>): <subject>

<optional body>

Types: feat, fix, docs, refactor, test, chore"""


@click.command()
@click.argument("prompt", required=False, default="")
@click.option("--review", "-r", is_flag=True, help="Review mode (code review)")
@click.option("--commit", "-c", is_flag=True, help="Generate commit message")
@click.option("--model", "-m", default="qwen3:latest", help="Model to use")
@click.option("--verbose", "-v", is_flag=True, help="Show tool calls")
@click.option("--version", "-V", is_flag=True, help="Show version")
def main(prompt: str, review: bool, commit: bool, model: str, verbose: bool, version: bool):
    """Chat with local Ollama models that can explore your codebase.
    
    \b
    Examples:
        local-brain "What files changed recently?"
        local-brain "Explain src/main.py"
        local-brain --review                  # Review git changes
        local-brain --review src/utils.py     # Review specific file
        local-brain --commit                  # Generate commit message
        local-brain -v "What's in this repo?" # Verbose (show tool calls)
    """
    if version:
        click.echo(f"local-brain {__version__}")
        return
    
    # Determine mode and system prompt
    if commit:
        system = COMMIT_SYSTEM
        prompt = "Generate a commit message for the staged changes."
    elif review:
        system = REVIEW_SYSTEM
        if not prompt or prompt == ".":
            prompt = "Review the git changes (use git_diff and git_changed_files)"
        elif Path(prompt).exists():
            if Path(prompt).is_dir():
                prompt = f"Review the code in: {prompt}"
            else:
                prompt = f"Review this file: {prompt}"
    else:
        system = SYSTEM_PROMPT
        if not prompt:
            click.echo("Usage: local-brain \"your prompt here\"")
            click.echo("       local-brain --help for more options")
            sys.exit(1)
    
    # Run
    result = run_agent(
        prompt=prompt,
        system=system,
        model=model,
        tools=ALL_TOOLS,
        verbose=verbose,
    )
    
    click.echo(result)
    
    # Show commit hint
    if commit:
        first_line = result.strip().split('\n')[0]
        click.echo(f"\n---\ngit commit -m \"{first_line}\"")


if __name__ == "__main__":
    main()
