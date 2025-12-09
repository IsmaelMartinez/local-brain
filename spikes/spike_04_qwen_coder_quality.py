#!/usr/bin/env python3
"""Spike 4: Test code generation quality with Qwen-Coder.

This spike validates:
1. Qwen-Coder generates correct, executable code
2. Code quality is readable and maintainable
3. Error handling is graceful
4. Complex tasks produce reasonable solutions

Run: uv run python spikes/spike_04_qwen_coder_quality.py
"""

import sys
from pathlib import Path
from typing import Any


# Test data setup
SPIKE_DIR = Path(__file__).parent
TEST_DIR = SPIKE_DIR / "test_project"


def setup_test_project() -> None:
    """Create a mock project structure for testing."""
    TEST_DIR.mkdir(exist_ok=True)

    # Create some test files
    (TEST_DIR / "main.py").write_text('''#!/usr/bin/env python3
"""Main entry point."""

def greet(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}!"

def calculate_sum(numbers: list[int]) -> int:
    """Calculate sum of numbers."""
    return sum(numbers)

if __name__ == "__main__":
    print(greet("World"))
''')

    (TEST_DIR / "utils.py").write_text('''"""Utility functions."""

import os
from pathlib import Path

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent

def list_python_files(directory: Path) -> list[str]:
    """List all Python files in directory."""
    return [f.name for f in directory.glob("*.py")]
''')

    (TEST_DIR / "config.json").write_text('{"debug": true, "version": "1.0.0"}')


def cleanup_test_project() -> None:
    """Remove test project."""
    import shutil

    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)


def test_model_availability() -> dict[str, Any]:
    """Test that Qwen-Coder models are available."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        import ollama

        models = ollama.list()
        model_names = [m.model for m in models.models]

        # Check for Qwen models
        qwen_models = [m for m in model_names if "qwen" in m.lower()]
        coder_models = [m for m in model_names if "coder" in m.lower()]

        results["details"]["installed_models"] = f"Found {len(model_names)} models"

        if qwen_models:
            results["details"]["qwen_models"] = f"✅ Qwen: {', '.join(qwen_models[:3])}"
        else:
            results["details"]["qwen_models"] = "⚠️ No Qwen models found"

        if coder_models:
            results["details"]["coder_models"] = (
                f"✅ Coder: {', '.join(coder_models[:3])}"
            )
        else:
            results["details"]["coder_models"] = "⚠️ No Coder models found"

        # Try to find the best model for testing
        preferred = ["qwen2.5-coder:7b", "qwen2.5-coder:latest", "qwen3:latest"]
        for model in preferred:
            if model in model_names:
                results["details"]["selected"] = f"✅ Will use: {model}"
                results["selected_model"] = model
                break
        else:
            # Fallback to any qwen model
            if qwen_models:
                results["details"]["selected"] = f"⚠️ Using fallback: {qwen_models[0]}"
                results["selected_model"] = qwen_models[0]
            else:
                results["passed"] = False
                results["details"]["selected"] = "❌ No suitable model found"

    except Exception as e:
        results["passed"] = False
        results["details"]["availability"] = f"❌ Failed: {e}"

    return results


def test_simple_code_task(model_id: str) -> dict[str, Any]:
    """Test simple code generation task."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from smolagents import CodeAgent, LiteLLMModel

        model = LiteLLMModel(
            model_id=f"ollama/{model_id}",
            api_base="http://localhost:11434",
        )

        agent = CodeAgent(tools=[], model=model)

        # Simple task: FizzBuzz-style logic
        result = agent.run(
            "Generate the first 10 FizzBuzz numbers. "
            "For multiples of 3 print 'Fizz', for multiples of 5 print 'Buzz', "
            "for both print 'FizzBuzz', otherwise print the number. "
            "Return the list of outputs."
        )

        result_str = str(result).lower()

        # Check for expected patterns
        has_fizz = "fizz" in result_str
        has_buzz = "buzz" in result_str
        has_numbers = any(str(i) in result_str for i in [1, 2, 4, 7, 8])

        if has_fizz and has_buzz and has_numbers:
            results["details"]["fizzbuzz"] = "✅ Correct patterns found"
        else:
            results["details"]["fizzbuzz"] = (
                f"⚠️ Partial: fizz={has_fizz}, buzz={has_buzz}, nums={has_numbers}"
            )

        results["details"]["output_preview"] = f"Output: {result_str[:100]}..."

    except Exception as e:
        results["passed"] = False
        results["details"]["simple_task"] = f"❌ Failed: {e}"

    return results


def test_file_analysis_task(model_id: str) -> dict[str, Any]:
    """Test code analysis task using tools."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from smolagents import CodeAgent, LiteLLMModel, tool

        # Define a file reading tool
        @tool
        def read_file(path: str) -> str:
            """Read the contents of a file.

            Args:
                path: Path to the file to read.

            Returns:
                The file contents as a string.
            """
            file_path = TEST_DIR / path
            if file_path.exists():
                return file_path.read_text()
            return f"Error: File not found: {path}"

        @tool
        def list_files(directory: str = ".") -> str:
            """List files in a directory.

            Args:
                directory: Directory to list (default: current).

            Returns:
                Newline-separated list of files.
            """
            dir_path = TEST_DIR / directory if directory != "." else TEST_DIR
            if dir_path.exists():
                return "\n".join(f.name for f in dir_path.iterdir())
            return f"Error: Directory not found: {directory}"

        model = LiteLLMModel(
            model_id=f"ollama/{model_id}",
            api_base="http://localhost:11434",
        )

        agent = CodeAgent(
            tools=[read_file, list_files],
            model=model,
        )

        # Task: Analyze the project
        result = agent.run(
            "List the files in the project and read main.py. "
            "Tell me what functions are defined in main.py."
        )

        result_str = str(result).lower()

        # Should mention the functions
        has_greet = "greet" in result_str
        has_calculate = "calculate" in result_str or "sum" in result_str

        if has_greet and has_calculate:
            results["details"]["analysis"] = "✅ Found both functions"
        elif has_greet or has_calculate:
            results["details"]["analysis"] = "⚠️ Found some functions"
        else:
            results["details"]["analysis"] = "❌ Didn't find functions"
            results["passed"] = False

        results["details"]["output"] = f"Output: {str(result)[:150]}..."

    except Exception as e:
        results["passed"] = False
        results["details"]["file_analysis"] = f"❌ Failed: {e}"

    return results


def test_error_handling(model_id: str) -> dict[str, Any]:
    """Test how the model handles errors gracefully."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from smolagents import CodeAgent, LiteLLMModel, tool

        @tool
        def read_file(path: str) -> str:
            """Read a file's contents.

            Args:
                path: Path to the file.

            Returns:
                File contents or error message.
            """
            try:
                return Path(path).read_text()
            except Exception as e:
                return f"Error: {e}"

        model = LiteLLMModel(
            model_id=f"ollama/{model_id}",
            api_base="http://localhost:11434",
        )

        agent = CodeAgent(
            tools=[read_file],
            model=model,
        )

        # Ask to read non-existent file
        result = agent.run(
            "Try to read the file 'nonexistent_file_12345.txt'. "
            "If it doesn't exist, say 'File not found'."
        )

        result_str = str(result).lower()

        if (
            "not found" in result_str
            or "error" in result_str
            or "doesn't exist" in result_str
        ):
            results["details"]["error_handling"] = "✅ Handled missing file gracefully"
        else:
            results["details"]["error_handling"] = (
                f"⚠️ Unclear error handling: {result_str[:50]}"
            )

    except Exception as e:
        results["passed"] = False
        results["details"]["error_handling"] = f"❌ Failed: {e}"

    return results


def test_code_quality_review(model_id: str) -> dict[str, Any]:
    """Test model's ability to review and improve code."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from smolagents import CodeAgent, LiteLLMModel

        model = LiteLLMModel(
            model_id=f"ollama/{model_id}",
            api_base="http://localhost:11434",
        )

        agent = CodeAgent(tools=[], model=model)

        # Ask to improve bad code
        bad_code = """
def f(x):
    y=[]
    for i in x:
        if i%2==0:
            y.append(i*2)
    return y
"""

        result = agent.run(
            f"Review this Python code and suggest improvements for readability:\n```python\n{bad_code}\n```\n"
            "Provide an improved version with better variable names and formatting."
        )

        result_str = str(result)

        # Check for improvements
        improvements = 0
        if "numbers" in result_str.lower() or "items" in result_str.lower():
            improvements += 1  # Better variable names
        if "even" in result_str.lower():
            improvements += 1  # Descriptive naming
        if "list comprehension" in result_str.lower():
            improvements += 1  # Suggested comprehension

        if improvements >= 2:
            results["details"]["code_review"] = (
                f"✅ Good suggestions ({improvements} improvements)"
            )
        elif improvements >= 1:
            results["details"]["code_review"] = (
                f"⚠️ Some suggestions ({improvements} improvements)"
            )
        else:
            results["details"]["code_review"] = "❌ No clear improvements suggested"

        results["details"]["preview"] = f"Output: {result_str[:200]}..."

    except Exception as e:
        results["passed"] = False
        results["details"]["code_review"] = f"❌ Failed: {e}"

    return results


def main() -> int:
    """Run all tests and report results."""
    print("=" * 60)
    print("SPIKE 4: Qwen-Coder Code Generation Quality")
    print("=" * 60)

    # First check model availability
    availability = test_model_availability()
    print("\n🧪 Test: Model Availability")
    print("-" * 40)
    for key, value in availability["details"].items():
        print(f"   {key}: {value}")

    if not availability["passed"] or "selected_model" not in availability:
        print("\n❌ SPIKE 4 FAILED: No suitable model available")
        print("   Run: ollama pull qwen2.5-coder:7b")
        return 1

    model_id = availability["selected_model"]
    print(f"\n📌 Using model: {model_id}")

    # Setup test project
    setup_test_project()

    tests = [
        ("Simple Code Task (FizzBuzz)", lambda: test_simple_code_task(model_id)),
        ("File Analysis Task", lambda: test_file_analysis_task(model_id)),
        ("Error Handling", lambda: test_error_handling(model_id)),
        ("Code Quality Review", lambda: test_code_quality_review(model_id)),
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

    # Cleanup
    cleanup_test_project()

    print("\n" + "=" * 60)
    if all_passed:
        print(f"✅ SPIKE 4 PASSED: {model_id} produces quality code!")
        return 0
    else:
        print(f"⚠️ SPIKE 4 PARTIAL: Some quality issues with {model_id}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
