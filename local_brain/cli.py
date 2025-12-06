"""CLI for Local Brain - skill-based LLM tasks with tool calling."""

import sys
import click
from pathlib import Path

from . import __version__
from .skill_loader import get_skill, list_skills, BUILTIN_SKILLS
from .agent import run_agent


@click.group(invoke_without_command=True)
@click.option("--version", "-V", is_flag=True, help="Show version")
@click.pass_context
def cli(ctx: click.Context, version: bool):
    """Local Brain - Skill-based LLM tasks using local Ollama models.
    
    Run a skill with a prompt:
    
        local-brain run code-review "Review the changed files"
        
        local-brain run commit-message
        
        local-brain run chat "What files are in src/?"
    
    List available skills:
    
        local-brain skills
    """
    if version:
        click.echo(f"local-brain {__version__}")
        return
    
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument("skill_name")
@click.argument("prompt", required=False, default="")
@click.option("--model", "-m", help="Override model selection")
@click.option("--verbose", "-v", is_flag=True, help="Show tool calls and intermediate steps")
@click.option("--max-turns", "-t", default=10, help="Maximum conversation turns")
def run(skill_name: str, prompt: str, model: str | None, verbose: bool, max_turns: int):
    """Run a skill with a prompt.
    
    Examples:
    
        local-brain run chat "What's in the src directory?"
        
        local-brain run code-review "Review src/main.rs"
        
        local-brain run commit-message
        
        local-brain run explain "Explain the architecture of this project"
    """
    try:
        skill = get_skill(skill_name)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    
    # Use skill's default prompt if none provided
    if not prompt:
        prompt = skill.render_user_prompt(input="")
        if not prompt.strip():
            click.echo(f"Error: Skill '{skill_name}' requires a prompt", err=True)
            sys.exit(1)
    
    if verbose:
        click.echo(f"🎯 Running skill: {skill.name}")
        click.echo(f"📝 Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        click.echo()
    
    # Run the agent
    result = run_agent(
        skill=skill,
        user_input=prompt,
        model=model,
        max_turns=max_turns,
        verbose=verbose,
    )
    
    # Output result
    click.echo(result)


@cli.command("skills")
def list_skills_cmd():
    """List available skills."""
    click.echo("Built-in skills:")
    for name, skill in BUILTIN_SKILLS.items():
        click.echo(f"  {name:20} - {skill.description}")
    
    # Also list file-based skills if any
    file_skills = list_skills()
    if file_skills:
        click.echo("\nFile-based skills:")
        for name in file_skills:
            click.echo(f"  {name}")


@cli.command()
@click.argument("prompt")
@click.option("--model", "-m", default="qwen3:latest", help="Model to use")
@click.option("--tools/--no-tools", default=True, help="Enable/disable tools")
@click.option("--verbose", "-v", is_flag=True, help="Show tool calls")
def chat(prompt: str, model: str, tools: bool, verbose: bool):
    """Quick chat with the model (uses 'chat' skill).
    
    Examples:
    
        local-brain chat "What files are in src/?"
        
        local-brain chat "Read and summarize README.md"
        
        local-brain chat --no-tools "Explain Python decorators"
    """
    skill = get_skill("chat")
    
    if not tools:
        # Create a no-tools version
        from .skill_loader import Skill
        skill = Skill({
            "name": "chat-no-tools",
            "system_prompt": "You are a helpful assistant.",
            "user_prompt_template": "{{ input }}",
            "tools": [],
        })
    
    result = run_agent(
        skill=skill,
        user_input=prompt,
        model=model,
        verbose=verbose,
    )
    
    click.echo(result)


@cli.command()
@click.option("--model", "-m", help="Model to use")
@click.option("--verbose", "-v", is_flag=True, help="Show tool calls")
def commit(model: str | None, verbose: bool):
    """Generate a commit message from staged changes.
    
    Equivalent to: local-brain run commit-message
    """
    skill = get_skill("commit-message")
    
    result = run_agent(
        skill=skill,
        user_input="Generate a commit message for the staged changes.",
        model=model,
        verbose=verbose,
    )
    
    click.echo(result)
    click.echo()
    click.echo("---")
    click.echo("To use this message:")
    
    # Extract first line for single-line commit suggestion
    first_line = result.strip().split('\n')[0]
    click.echo(f'  git commit -m "{first_line}"')


@cli.command()
@click.argument("target", required=False, default=".")
@click.option("--model", "-m", help="Model to use")
@click.option("--verbose", "-v", is_flag=True, help="Show tool calls")
def review(target: str, model: str | None, verbose: bool):
    """Review code (files, directories, or git changes).
    
    Examples:
    
        local-brain review                    # Review git changes
        
        local-brain review src/main.rs        # Review specific file
        
        local-brain review src/               # Review directory
    """
    skill = get_skill("code-review")
    
    # Build appropriate prompt based on target
    if target == ".":
        prompt = "Review the git changes (check git_changed_files and git_diff)"
    elif Path(target).is_file():
        prompt = f"Review the file: {target}"
    elif Path(target).is_dir():
        prompt = f"Review the code in directory: {target}"
    else:
        prompt = f"Review: {target}"
    
    result = run_agent(
        skill=skill,
        user_input=prompt,
        model=model,
        verbose=verbose,
    )
    
    click.echo(result)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()

