"""Local Brain - Chat with local Ollama models that can use tools."""

import click

from . import __version__
from .agent import run_agent
from .tools import ALL_TOOLS


SYSTEM_PROMPT = """You are a helpful assistant with access to tools for exploring codebases.

Available tools:
- read_file: Read file contents
- list_directory: List files (supports glob patterns)
- git_diff: See code changes  
- git_status: Check repo status
- git_changed_files: List changed files
- git_log: View commit history
- run_command: Run safe shell commands
- write_file: Write to files

Use tools when they help answer the question. Be concise."""


@click.command()
@click.argument("prompt")
@click.option("--model", "-m", default="qwen3:latest", help="Model to use")
@click.option("--verbose", "-v", is_flag=True, help="Show tool calls")
@click.option("--version", "-V", is_flag=True, help="Show version")
def main(prompt: str, model: str, verbose: bool, version: bool):
    """Chat with local Ollama models that can explore your codebase.
    
    Examples:
    
    \b
        local-brain "What files are in this repo?"
        local-brain "Review the recent git changes"
        local-brain "Generate a commit message for staged changes"
        local-brain "Explain how src/main.py works"
        local-brain -v "What changed?" 
    """
    if version:
        click.echo(f"local-brain {__version__}")
        return
    
    result = run_agent(
        prompt=prompt,
        system=SYSTEM_PROMPT,
        model=model,
        tools=ALL_TOOLS,
        verbose=verbose,
    )
    
    click.echo(result)


if __name__ == "__main__":
    main()
