"""Model discovery and selection for Local Brain.

Automatically detects installed Ollama models and provides smart
model selection based on capabilities and task requirements.
"""

from dataclasses import dataclass
from typing import Literal

import ollama


@dataclass
class ModelInfo:
    """Information about an Ollama model."""

    name: str
    size_gb: float
    tool_support: Literal["excellent", "good", "limited", "none"]
    best_for: str
    tier: int  # 1 = best, 2 = good, 3 = fallback


# Recommended models for tool-calling tasks (ordered by preference)
# Based on testing documented in docs/model-performance-comparison.md
RECOMMENDED_MODELS: dict[str, ModelInfo] = {
    # Tier 1 - Excellent tool support (verified working)
    # qwen3:30b is first as it's the default and preferred model
    "qwen3:30b": ModelInfo(
        "qwen3:30b", 18.0, "excellent", "Default, complex reasoning", 1
    ),
    "qwen3:latest": ModelInfo("qwen3:latest", 5.2, "excellent", "General purpose", 1),
    "qwen3:8b": ModelInfo("qwen3:8b", 4.9, "excellent", "General purpose", 1),
    "qwen3:14b": ModelInfo("qwen3:14b", 9.0, "excellent", "Complex reasoning", 1),
    # Tier 1 - Small but excellent (tested excellent, 60% smaller than qwen3)
    "qwen2.5:3b": ModelInfo(
        "qwen2.5:3b", 1.9, "excellent", "Resource-constrained, fast", 1
    ),
    # Tier 2 - Good tool support
    "ministral-3:latest": ModelInfo(
        "ministral-3:latest", 6.0, "good", "Mistral AI, newer", 2
    ),
    "llama3.2:3b": ModelInfo("llama3.2:3b", 2.0, "good", "Fast, lightweight", 2),
    "llama3.1:8b": ModelInfo("llama3.1:8b", 4.7, "good", "Balanced performance", 2),
    "mistral:7b": ModelInfo("mistral:7b", 4.1, "good", "Balanced, reliable", 2),
    "mistral:latest": ModelInfo("mistral:latest", 4.1, "good", "Balanced, reliable", 2),
    # Tier 2 - Larger models (untested but likely good)
    "deepseek-coder-v2:16b": ModelInfo(
        "deepseek-coder-v2:16b", 8.9, "good", "Complex code analysis", 2
    ),
    "codellama:13b": ModelInfo("codellama:13b", 7.4, "good", "Code generation", 2),
    # Tier 3 - Limited but usable
    "gemma2:9b": ModelInfo("gemma2:9b", 5.4, "limited", "Google's model", 3),
    "phi3:mini": ModelInfo("phi3:mini", 2.2, "limited", "Microsoft's small model", 3),
}

# Models known to NOT work with local-brain (tool calling broken or unsupported)
# DO NOT add these to RECOMMENDED_MODELS
INCOMPATIBLE_MODELS = {
    # qwen2.5-coder family: outputs JSON instead of executing tools (CodeAgent incompatibility)
    "qwen2.5-coder:latest",
    "qwen2.5-coder:3b",
    "qwen2.5-coder:7b",
    "qwen2.5-coder:14b",
    "qwen2.5-coder:32b",
    # DeepSeek R1: no tool support at architecture level (Ollama returns 400 error)
    "deepseek-r1:latest",
    # Llama 3.2 1B: too small, hallucinates paths and tool calls
    "llama3.2:1b",
}

# Default model to suggest for installation
DEFAULT_MODEL = "qwen3:30b"


def list_installed_models() -> list:
    """Get all installed Ollama models.

    Returns:
        List of Model objects with name, size, etc.
    """
    try:
        response = ollama.list()
        # Handle both dict (old API) and ListResponse (new API) formats
        if hasattr(response, "models"):
            return list(response.models)
        elif isinstance(response, dict):
            return response.get("models", [])
        return []
    except Exception:
        return []


def get_installed_model_names() -> set[str]:
    """Get names of all installed models (including tag variations).

    Returns:
        Set of model names (e.g., {"qwen3:latest", "llama3.2:3b"}).
    """
    models = list_installed_models()
    names = set()

    for model in models:
        # Handle both dict and Model object formats
        if hasattr(model, "model"):
            name = model.model
        elif isinstance(model, dict):
            name = model.get("name", "") or model.get("model", "")
        else:
            continue

        if name:
            names.add(name)
            # Also add without tag for matching
            if ":" in name:
                base_name = name.split(":")[0]
                names.add(f"{base_name}:latest")

    return names


def find_best_model(task_type: str | None = None) -> str | None:
    """Find the best installed model for a given task.

    Args:
        task_type: Type of task ("code", "general", None for any).

    Returns:
        Model name if found, None if no suitable model installed.
    """
    installed = get_installed_model_names()

    if not installed:
        return None

    # Build candidate list based on task type
    candidates: list[tuple[int, str]] = []  # (tier, name)

    for model_name, info in RECOMMENDED_MODELS.items():
        # Check if this model (or a variant) is installed
        if model_name in installed:
            # Filter by task type if specified
            if task_type == "code":
                if "coder" in model_name.lower() or "code" in info.best_for.lower():
                    candidates.append((info.tier, model_name))
            elif task_type == "general":
                if "coder" not in model_name.lower():
                    candidates.append((info.tier, model_name))
            else:
                candidates.append((info.tier, model_name))

    if not candidates:
        # Fallback: return any installed model from recommendations
        for model_name in RECOMMENDED_MODELS:
            if model_name in installed:
                return model_name

        # Ultimate fallback: return first installed model
        return next(iter(installed), None)

    # Sort by tier (lower is better) and return best
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def check_model_available(model: str) -> bool:
    """Check if a specific model is installed.

    Args:
        model: Model name to check.

    Returns:
        True if installed, False otherwise.
    """
    installed = get_installed_model_names()
    return model in installed


def is_model_incompatible(model: str) -> bool:
    """Check if a model is known to be incompatible with local-brain.

    Args:
        model: Model name to check.

    Returns:
        True if model is known to be incompatible, False otherwise.
    """
    return model in INCOMPATIBLE_MODELS


def get_model_recommendation() -> tuple[str, str]:
    """Get a model recommendation with explanation.

    Returns:
        Tuple of (recommended_model, explanation).
    """
    best = find_best_model()

    if best:
        info = RECOMMENDED_MODELS.get(best)
        if info:
            return best, f"Using {best} ({info.best_for}, {info.size_gb}GB)"
        return best, f"Using {best}"

    return (
        DEFAULT_MODEL,
        f"No recommended models installed. Suggest: ollama pull {DEFAULT_MODEL}",
    )


def get_available_models_summary() -> str:
    """Get a summary of available models for display.

    Returns:
        Formatted string showing installed models and recommendations.
    """
    installed = get_installed_model_names()

    if not installed:
        return f"No Ollama models found. Run: ollama pull {DEFAULT_MODEL}"

    lines = ["Installed models:"]

    # Show recommended models that are installed
    recommended_installed = []
    incompatible_installed = []
    other_installed = []

    for name in installed:
        if name in INCOMPATIBLE_MODELS:
            incompatible_installed.append(f"  ❌ {name} - NOT COMPATIBLE")
        elif name in RECOMMENDED_MODELS:
            info = RECOMMENDED_MODELS[name]
            recommended_installed.append(f"  ✅ {name} - {info.best_for}")
        else:
            other_installed.append(f"  • {name}")

    if recommended_installed:
        lines.extend(recommended_installed)
    if other_installed:
        lines.append("Other:")
        lines.extend(other_installed[:5])  # Limit to 5
        if len(other_installed) > 5:
            lines.append(f"  ... and {len(other_installed) - 5} more")

    # Warn about incompatible models
    if incompatible_installed:
        lines.append("\nIncompatible (tool calling broken):")
        lines.extend(incompatible_installed)

    # Suggest missing good models
    missing_tier1 = [
        name
        for name, info in RECOMMENDED_MODELS.items()
        if info.tier == 1 and name not in installed
    ]
    if missing_tier1 and len(recommended_installed) < 2:
        lines.append(f"\nSuggested: ollama pull {missing_tier1[0]}")

    return "\n".join(lines)


def select_model_for_task(
    requested_model: str | None = None,
    task_hint: str | None = None,
) -> tuple[str, bool]:
    """Select the best model for a task, with fallback logic.

    Args:
        requested_model: User-requested model (if any).
        task_hint: Hint about the task type.

    Returns:
        Tuple of (model_name, was_fallback) where was_fallback indicates
        if we fell back from the requested model.
    """
    # If user requested a specific model
    if requested_model:
        # Check if requested model is incompatible
        if is_model_incompatible(requested_model):
            # Force fallback to compatible model
            best = find_best_model(task_hint)
            if best:
                return best, True
            return DEFAULT_MODEL, True

        if check_model_available(requested_model):
            return requested_model, False

        # Try to find an alternative
        best = find_best_model(task_hint)
        if best:
            return best, True

        # No fallback available - return requested (will fail at runtime)
        return requested_model, False

    # Auto-select best model
    best = find_best_model(task_hint)
    if best:
        return best, False

    # Default fallback
    return DEFAULT_MODEL, False
