#!/usr/bin/env python3
"""Spike 1: Test basic Smolagents + Ollama integration via LiteLLM.

This spike validates:
1. Smolagents can be imported and initialized
2. LiteLLM can connect to Ollama
3. Basic agent creation works

Run: uv run python spikes/spike_01_smolagents_basic.py
"""

import sys
from typing import Any


def test_imports() -> dict[str, Any]:
    """Test that all required imports work."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        import smolagents  # noqa: F401

        results["details"]["smolagents"] = "✅ Imported"
    except ImportError as e:
        results["passed"] = False
        results["details"]["smolagents"] = f"❌ Failed: {e}"

    try:
        import litellm  # noqa: F401

        results["details"]["litellm"] = "✅ Imported"
    except ImportError as e:
        results["passed"] = False
        results["details"]["litellm"] = f"❌ Failed: {e}"

    return results


def test_litellm_ollama_connection() -> dict[str, Any]:
    """Test that LiteLLM can connect to Ollama."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        import litellm

        # Test simple completion with Ollama
        # LiteLLM uses "ollama/" prefix for Ollama models
        response = litellm.completion(
            model="ollama/qwen3:latest",
            messages=[{"role": "user", "content": "Say hello in one word"}],
            api_base="http://localhost:11434",
        )
        content = response.choices[0].message.content
        results["details"]["connection"] = f"✅ Connected, response: {content[:50]}..."
    except Exception as e:
        results["passed"] = False
        results["details"]["connection"] = f"❌ Failed: {e}"

    return results


def test_smolagents_model() -> dict[str, Any]:
    """Test Smolagents LiteLLMModel with Ollama."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from smolagents import LiteLLMModel

        # Create model pointing to Ollama
        model = LiteLLMModel(
            model_id="ollama/qwen3:latest",
            api_base="http://localhost:11434",
        )
        results["details"]["model_creation"] = "✅ LiteLLMModel created"

        # Test basic call - smolagents model returns a ChatMessage object
        response = model(
            [{"role": "user", "content": "What is 2+2? Reply with just the number."}]
        )
        # Access content from the ChatMessage
        content = getattr(response, "content", str(response))
        results["details"]["model_call"] = (
            f"✅ Model responded: {str(content)[:100]}..."
        )

    except Exception as e:
        results["passed"] = False
        results["details"]["model_call"] = f"❌ Failed: {e}"

    return results


def test_agent_creation() -> dict[str, Any]:
    """Test basic CodeAgent creation (no tools yet)."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from smolagents import CodeAgent, LiteLLMModel

        model = LiteLLMModel(
            model_id="ollama/qwen3:latest",
            api_base="http://localhost:11434",
        )

        # Create agent without tools first
        agent = CodeAgent(
            tools=[],
            model=model,
        )
        results["details"]["agent_creation"] = "✅ CodeAgent created"

        # Test simple run (no tools needed)
        result = agent.run("What is 5 * 7? Just give me the number.")
        results["details"]["agent_run"] = f"✅ Agent returned: {str(result)[:100]}..."

    except Exception as e:
        results["passed"] = False
        results["details"]["agent"] = f"❌ Failed: {e}"

    return results


def main() -> int:
    """Run all tests and report results."""
    print("=" * 60)
    print("SPIKE 1: Smolagents + Ollama Basic Integration")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("LiteLLM → Ollama Connection", test_litellm_ollama_connection),
        ("Smolagents LiteLLMModel", test_smolagents_model),
        ("CodeAgent Creation", test_agent_creation),
    ]

    all_passed = True

    for name, test_fn in tests:
        print(f"\n🧪 Test: {name}")
        print("-" * 40)

        result = test_fn()
        for key, value in result["details"].items():
            print(f"   {key}: {value}")

        if not result["passed"]:
            all_passed = False
            print("   ⚠️  TEST FAILED")
        else:
            print("   ✅ TEST PASSED")

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ SPIKE 1 PASSED: Basic integration works!")
        return 0
    else:
        print("❌ SPIKE 1 FAILED: See details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
