"""Local Brain - Chat with local Ollama models that can use tools."""

import subprocess

import click

from . import __version__
from .smolagent import run_smolagent, ALL_TOOLS
from .models import (
    select_model_for_task,
    get_available_models_summary,
    check_model_available,
    is_model_incompatible,
    list_installed_models,
    DEFAULT_MODEL,
    RECOMMENDED_MODELS,
)
from .security import set_project_root


def _setup_environment(
    root: str | None, verbose: bool, trace: bool, model: str | None
) -> tuple[str, str]:
    """Set up project root, tracing, and model selection.

    Args:
        root: Project root directory (or None for current directory)
        verbose: Whether to show verbose output
        trace: Whether to enable OTEL tracing
        model: Model name (or None for auto-selection)

    Returns:
        Tuple of (project_root, selected_model)
    """
    # Initialize security - set project root for path jailing
    project_root = set_project_root(root)

    if verbose:
        click.echo(f"📁 Project root: {project_root}")

    # Enable tracing if requested
    if trace:
        from .tracing import setup_tracing

        if setup_tracing():
            if verbose:
                click.echo("🔍 OTEL tracing enabled")
        else:
            click.echo(
                "⚠️  Tracing unavailable (install: pip install "
                "openinference-instrumentation-smolagents opentelemetry-sdk)",
                err=True,
            )

    # Smart model selection
    selected_model, was_fallback = select_model_for_task(model)

    if was_fallback:
        # Check if original model was incompatible
        if model and is_model_incompatible(model):
            click.echo(
                f"❌ Model '{model}' is incompatible (tool calling broken).\n"
                f"   Using '{selected_model}' instead.\n"
                f"   See docs/model-performance-comparison.md for details.",
                err=True,
            )
        else:
            click.echo(
                f"⚠️  Model '{model}' not found. Using '{selected_model}' instead.",
                err=True,
            )

    # Check if selected model is available
    if not check_model_available(selected_model):
        click.echo(
            f"❌ Model '{selected_model}' not installed.\n\n"
            f"Install with: ollama pull {selected_model}\n\n"
            f"Or try: ollama pull {DEFAULT_MODEL}",
            err=True,
        )
        raise SystemExit(1)

    if verbose:
        click.echo(f"🤖 Model: {selected_model}")

    return str(project_root), selected_model


@click.group(invoke_without_command=True)
@click.argument("prompt", required=False, default="")
@click.option(
    "--model", "-m", default=None, help="Model to use (auto-selects if not specified)"
)
@click.option(
    "--root",
    "-r",
    default=None,
    help="Project root directory (default: current directory)",
)
@click.option("--verbose", "-v", is_flag=True, help="Show execution details")
@click.option("--trace", "-t", is_flag=True, help="Enable OTEL tracing")
@click.option("--list-models", is_flag=True, help="List available models and exit")
@click.option("--version", "-V", is_flag=True, help="Show version")
@click.pass_context
def main(
    ctx: click.Context,
    prompt: str,
    model: str | None,
    root: str | None,
    verbose: bool,
    trace: bool,
    list_models: bool,
    version: bool,
):
    """Chat with local Ollama models that can explore your codebase.

    Uses Smolagents for secure, sandboxed code execution.

    Examples:

    \b
        local-brain "What files are in this repo?"
        local-brain "Review the recent git changes"
        local-brain "Generate a commit message for staged changes"
        local-brain "Explain how src/main.py works"
        local-brain -v "What changed?"
        local-brain --trace "Review the code"
        local-brain --list-models
        local-brain -m qwen2.5-coder:7b "Review this code"
        local-brain doctor
    """
    # If a subcommand is invoked, skip the main command logic
    if ctx.invoked_subcommand is not None:
        return

    # Handle subcommands as special cases - Click sees them as prompt due to positional arg
    if prompt == "doctor":
        ctx.invoke(doctor)
        return

    if version:
        click.echo(f"local-brain {__version__}")
        return

    if list_models:
        click.echo(get_available_models_summary())
        return

    if not prompt:
        raise click.UsageError("Missing argument 'PROMPT'. Run with --help for usage.")

    # Common setup: project root, tracing, and model selection
    project_root, selected_model = _setup_environment(root, verbose, trace, model)

    result = run_smolagent(
        prompt=prompt,
        model=selected_model,
        verbose=verbose,
    )

    click.echo(result)


@main.command()
def doctor():
    """Check system health and configuration.

    Verifies:
    - Ollama is running
    - Recommended models are installed
    - Tools can execute
    """
    import tempfile
    from pathlib import Path

    click.echo("🔍 Local Brain Health Check\n")

    all_ok = True

    # Check 1: Ollama is running
    click.echo("Checking Ollama...")
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            click.echo(f"  ✅ Ollama is installed ({version})")
        else:
            click.echo("  ❌ Ollama returned an error")
            all_ok = False
    except FileNotFoundError:
        click.echo("  ❌ Ollama is not installed")
        click.echo("     Install: https://ollama.ai/download")
        all_ok = False
    except subprocess.TimeoutExpired:
        click.echo("  ❌ Ollama command timed out")
        all_ok = False

    # Check 2: Ollama server is running (can list models)
    click.echo("\nChecking Ollama server...")
    models = None
    try:
        models = list_installed_models()
        if models is not None:
            click.echo(f"  ✅ Ollama server is running ({len(models)} models)")
        else:
            click.echo("  ⚠️  Could not connect to Ollama server")
            click.echo("     Start with: ollama serve")
            all_ok = False
    except Exception as e:
        click.echo(f"  ❌ Error connecting to Ollama: {e}")
        click.echo("     Start with: ollama serve")
        all_ok = False

    # Check 3: Recommended models installed
    click.echo("\nChecking recommended models...")
    installed = set()
    # Reuse models from previous check instead of calling list_installed_models() again
    if models:
        try:
            for m in models:
                if hasattr(m, "model"):
                    installed.add(m.model)
                elif isinstance(m, dict):
                    installed.add(m.get("name", "") or m.get("model", ""))
        except (TypeError, AttributeError) as e:
            click.echo(f"  ⚠️  Error parsing model list: {e}", err=True)

    tier1_models = [name for name, info in RECOMMENDED_MODELS.items() if info.tier == 1]
    tier1_installed = [m for m in tier1_models if m in installed]

    if tier1_installed:
        click.echo(f"  ✅ Recommended models installed: {', '.join(tier1_installed)}")
    else:
        click.echo("  ⚠️  No recommended models installed")
        click.echo(f"     Install with: ollama pull {DEFAULT_MODEL}")

    # Check 4: Tool execution test
    click.echo("\nChecking tools...")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            set_project_root(tmpdir)

            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello, Local Brain!")

            # Import and test read_file tool
            from .smolagent import read_file

            result = read_file(str(test_file))

            if "Hello, Local Brain!" in result:
                click.echo(f"  ✅ Tools working ({len(ALL_TOOLS)} tools available)")
            else:
                click.echo("  ❌ Tool test failed: unexpected result")
                all_ok = False
    except Exception as e:
        click.echo(f"  ❌ Tool test failed: {e}")
        all_ok = False

    # Check 5: Tracing dependencies (optional)
    click.echo("\nChecking optional features...")
    try:
        import importlib.util

        if importlib.util.find_spec(
            "openinference.instrumentation.smolagents"
        ) and importlib.util.find_spec("opentelemetry.sdk.trace"):
            click.echo("  ✅ OTEL tracing available (--trace flag)")
        else:
            raise ImportError("Missing tracing dependencies")
    except ImportError:
        click.echo("  ⚪ OTEL tracing not installed (optional)")
        click.echo(
            "     Install: pip install openinference-instrumentation-smolagents "
            "opentelemetry-sdk"
        )

    # Summary
    click.echo("\n" + "=" * 40)
    if all_ok:
        click.echo("✅ All checks passed! Local Brain is ready.")
    else:
        click.echo("⚠️  Some issues found. See above for details.")

    return 0 if all_ok else 1


if __name__ == "__main__":
    main()
