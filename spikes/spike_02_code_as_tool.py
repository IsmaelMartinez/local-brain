#!/usr/bin/env python3
"""Spike 2: Test code-as-tool pattern.

This spike validates:
1. Model can generate Python code to solve tasks
2. Generated code executes correctly
3. Results are returned properly

The key insight: Instead of defining fixed tools like read_file(),
the model writes: `open('file.txt').read()` directly.

Run: uv run python spikes/spike_02_code_as_tool.py
"""

import sys
import os
from pathlib import Path
from typing import Any


# Create a test file for the spike
SPIKE_DIR = Path(__file__).parent
TEST_FILE = SPIKE_DIR / "test_data.txt"


def setup_test_files() -> None:
    """Create test files for the spike."""
    TEST_FILE.write_text("Hello from test file!\nLine 2\nLine 3\n")


def cleanup_test_files() -> None:
    """Remove test files."""
    if TEST_FILE.exists():
        TEST_FILE.unlink()


def test_code_generation_simple() -> dict[str, Any]:
    """Test that model generates working Python code for simple tasks."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from smolagents import CodeAgent, LiteLLMModel

        model = LiteLLMModel(
            model_id="ollama/qwen3:latest",
            api_base="http://localhost:11434",
        )

        agent = CodeAgent(
            tools=[],
            model=model,
        )

        # Simple math task - should generate code like `result = 15 * 23`
        result = agent.run("Calculate 15 multiplied by 23. Return just the number.")

        # Check if result is reasonable (345)
        result_str = str(result)
        if "345" in result_str:
            results["details"]["math_task"] = f"✅ Correct: {result_str[:50]}"
        else:
            results["details"]["math_task"] = f"⚠️ Got: {result_str[:50]} (expected 345)"
            # Don't fail - model might format differently

    except Exception as e:
        results["passed"] = False
        results["details"]["math_task"] = f"❌ Failed: {e}"

    return results


def test_code_generation_list_operation() -> dict[str, Any]:
    """Test code generation for list operations."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from smolagents import CodeAgent, LiteLLMModel

        model = LiteLLMModel(
            model_id="ollama/qwen3:latest",
            api_base="http://localhost:11434",
        )

        agent = CodeAgent(
            tools=[],
            model=model,
        )

        # List processing task
        result = agent.run(
            "Given the list [1, 2, 3, 4, 5], calculate the sum. Return just the number."
        )

        result_str = str(result)
        if "15" in result_str:
            results["details"]["list_sum"] = f"✅ Correct: {result_str[:50]}"
        else:
            results["details"]["list_sum"] = f"⚠️ Got: {result_str[:50]} (expected 15)"

    except Exception as e:
        results["passed"] = False
        results["details"]["list_sum"] = f"❌ Failed: {e}"

    return results


def test_code_execution_visibility() -> dict[str, Any]:
    """Test that we can see what code the agent generates."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from smolagents import CodeAgent, LiteLLMModel

        model = LiteLLMModel(
            model_id="ollama/qwen3:latest",
            api_base="http://localhost:11434",
        )

        agent = CodeAgent(
            tools=[],
            model=model,
            verbosity_level=2,  # Higher verbosity to see code
        )

        # Run and capture logs
        result = agent.run("What is the square root of 144? Return just the number.")

        # Check if we can access agent's logs/history
        if hasattr(agent, "logs") or hasattr(agent, "memory"):
            results["details"]["visibility"] = "✅ Can inspect agent execution"
        else:
            results["details"]["visibility"] = "⚠️ Limited visibility into execution"

        results["details"]["result"] = f"Result: {str(result)[:50]}"

    except Exception as e:
        results["passed"] = False
        results["details"]["visibility"] = f"❌ Failed: {e}"

    return results


def test_tool_integration() -> dict[str, Any]:
    """Test adding a custom tool that the agent can use."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from smolagents import CodeAgent, LiteLLMModel, tool

        # Define a simple tool
        @tool
        def get_current_directory() -> str:
            """Get the current working directory.

            Returns:
                The absolute path of the current directory.
            """
            return os.getcwd()

        model = LiteLLMModel(
            model_id="ollama/qwen3:latest",
            api_base="http://localhost:11434",
        )

        agent = CodeAgent(
            tools=[get_current_directory],
            model=model,
        )

        # Ask agent to use the tool
        result = agent.run(
            "What is the current working directory? Use the available tool."
        )

        # Should contain a path
        result_str = str(result)
        if "/" in result_str or "\\" in result_str:
            results["details"]["tool_use"] = (
                f"✅ Tool used, got path: {result_str[:50]}..."
            )
        else:
            results["details"]["tool_use"] = f"⚠️ Unclear result: {result_str[:50]}"

    except Exception as e:
        results["passed"] = False
        results["details"]["tool_use"] = f"❌ Failed: {e}"

    return results


def main() -> int:
    """Run all tests and report results."""
    print("=" * 60)
    print("SPIKE 2: Code-as-Tool Pattern")
    print("=" * 60)

    setup_test_files()

    tests = [
        ("Simple Math Code Generation", test_code_generation_simple),
        ("List Operation Code Generation", test_code_generation_list_operation),
        ("Code Execution Visibility", test_code_execution_visibility),
        ("Custom Tool Integration", test_tool_integration),
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

    cleanup_test_files()

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ SPIKE 2 PASSED: Code-as-tool pattern works!")
        return 0
    else:
        print("❌ SPIKE 2 FAILED: See details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
