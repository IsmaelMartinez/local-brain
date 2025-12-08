"""Local Brain - Chat with local Ollama models that can use tools."""

import click

from . import __version__
from .agent import run_agent
from .models import (
    select_model_for_task,
    get_available_models_summary,
    check_model_available,
    DEFAULT_MODEL,
)
from .security import set_project_root, get_project_root
from .tools import ALL_TOOLS


SYSTEM_PROMPT = """You are a helpful assistant with access to tools for exploring codebases.

Available tools:
- read_file: Read file contents
- list_directory: List files (supports glob patterns)
- file_info: Get file metadata (size, modified time)
- git_diff: See code changes
- git_status: Check repo status
- git_changed_files: List changed files
- git_log: View commit history
- run_command: Run safe read-only shell commands

All file operations are restricted to the current project directory.
Use tools when they help answer the question. Be concise."""


@click.command()
@click.argument("prompt", required=False, default="")
@click.option("--model", "-m", default=None, help="Model to use (auto-selects if not specified)")
@click.option("--root", "-r", default=None, help="Project root directory (default: current directory)")
@click.option("--verbose", "-v", is_flag=True, help="Show tool calls")
@click.option("--list-models", is_flag=True, help="List available models and exit")
@click.option("--version", "-V", is_flag=True, help="Show version")
def main(
    prompt: str,
    model: str | None,
    root: str | None,
    verbose: bool,
    list_models: bool,
    version: bool,
):
    """Chat with local Ollama models that can explore your codebase.

    Examples:

    \b
        local-brain "What files are in this repo?"
        local-brain "Review the recent git changes"
        local-brain "Generate a commit message for staged changes"
        local-brain "Explain how src/main.py works"
        local-brain -v "What changed?"
        local-brain --list-models
        local-brain -m qwen2.5-coder:7b "Review this code"
    """
    if version:
        click.echo(f"local-brain {__version__}")
        return

    if list_models:
        click.echo(get_available_models_summary())
        return

    if not prompt:
        raise click.UsageError("Missing argument 'PROMPT'. Run with --help for usage.")

    # Initialize security - set project root for path jailing
    project_root = set_project_root(root)
    
    if verbose:
        click.echo(f"📁 Project root: {project_root}")

    # Smart model selection
    selected_model, was_fallback = select_model_for_task(model)
    
    if was_fallback:
        click.echo(
            f"⚠️  Model '{model}' not found. Using '{selected_model}' instead.",
            err=True
        )
    
    # Check if selected model is available
    if not check_model_available(selected_model):
        click.echo(
            f"❌ Model '{selected_model}' not installed.\n\n"
            f"Install with: ollama pull {selected_model}\n\n"
            f"Or try: ollama pull {DEFAULT_MODEL}",
            err=True
        )
        raise SystemExit(1)

    if verbose:
        click.echo(f"🤖 Model: {selected_model}")

    result = run_agent(
        prompt=prompt,
        system=SYSTEM_PROMPT,
        model=selected_model,
        tools=ALL_TOOLS,
        verbose=verbose,
    )

    click.echo(result)


if __name__ == "__main__":
    main()
