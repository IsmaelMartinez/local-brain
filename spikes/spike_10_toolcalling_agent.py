#!/usr/bin/env python3
"""Spike: Test ToolCallingAgent vs CodeAgent for qwen3-coder models

Problem:
========
qwen3-coder:30b tries to output ```python code blocks instead of using
the smolagents tool calling mechanism. The CodeAgent sandbox catches this
and rejects it with:
  "Your code snippet is invalid, because the regex pattern ```python(.*?)```
   was not found in it."

Hypothesis:
===========
ToolCallingAgent uses JSON-based tool calls instead of Python code execution.
This might work better for qwen3-coder models because:
1. It doesn't expect Python code blocks
2. It uses structured JSON for tool calls
3. The model doesn't execute code, it just calls tools via JSON

RESULTS (2025-01-10):
=====================
Both agents work with qwen3-coder:30b!

CodeAgent:        PASS (25.1s) - 2 steps
ToolCallingAgent: PASS (9.8s)  - 3 steps

ToolCallingAgent is 2.5x faster despite taking more steps.

The earlier failure with qwen3-coder was due to complex tasks where the model
tried to generate analysis code instead of using tools. For simple tool-calling
tasks, both agents work fine.

RECOMMENDATION:
===============
- For qwen3-coder models: ToolCallingAgent is faster and more direct
- For qwen3 base models: CodeAgent works well (tested elsewhere)
- Consider adding agent_type to ModelInfo for model-specific agent selection
"""

import sys
import time
from pathlib import Path

# Add local_brain to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from smolagents import CodeAgent, ToolCallingAgent, LiteLLMModel, tool
from local_brain.security import set_project_root

# Set project root
set_project_root(str(Path(__file__).parent.parent))


@tool
def list_files(path: str = ".") -> str:
    """List files in a directory.

    Args:
        path: Directory path to list

    Returns:
        List of files
    """
    from pathlib import Path as P

    try:
        files = list(P(path).iterdir())
        return "\n".join(f.name for f in files[:10])
    except Exception as e:
        return f"Error: {e}"


@tool
def read_file_content(path: str) -> str:
    """Read a file's contents.

    Args:
        path: Path to the file

    Returns:
        File contents (first 500 chars)
    """
    from pathlib import Path as P

    try:
        content = P(path).read_text()
        return content[:500] + ("..." if len(content) > 500 else "")
    except Exception as e:
        return f"Error: {e}"


def test_agent(agent_type: str, model_id: str, task: str) -> dict:
    """Test an agent type with a model."""
    print(f"\n{'='*60}")
    print(f"Testing {agent_type} with {model_id}")
    print(f"Task: {task}")
    print(f"{'='*60}\n")

    model = LiteLLMModel(
        model_id=f"ollama_chat/{model_id}",
        api_base="http://localhost:11434",
        num_ctx=8192,
    )

    tools = [list_files, read_file_content]

    start_time = time.time()

    try:
        if agent_type == "CodeAgent":
            agent = CodeAgent(
                tools=tools,
                model=model,
                verbosity_level=2,
                code_block_tags="markdown",
            )
        else:
            agent = ToolCallingAgent(
                tools=tools,
                model=model,
                verbosity_level=2,
            )

        result = agent.run(task)
        duration = time.time() - start_time

        return {
            "success": True,
            "result": str(result)[:500],
            "duration": duration,
            "error": None,
        }

    except Exception as e:
        duration = time.time() - start_time
        return {
            "success": False,
            "result": None,
            "duration": duration,
            "error": str(e),
        }


def main():
    """Run comparison tests."""
    model = "qwen3-coder:30b"
    task = "List the files in the current directory and tell me what you see."

    # Check if model is available
    import subprocess

    result = subprocess.run(
        ["ollama", "list"], capture_output=True, text=True, timeout=10
    )
    if model not in result.stdout:
        print(f"Model {model} not found. Available models:")
        print(result.stdout)
        print(f"\nInstall with: ollama pull {model}")
        return

    print("=" * 60)
    print("SPIKE: ToolCallingAgent vs CodeAgent for qwen3-coder")
    print("=" * 60)

    # Test CodeAgent (expected to have issues)
    code_result = test_agent("CodeAgent", model, task)
    print("\nCodeAgent Result:")
    print(f"  Success: {code_result['success']}")
    print(f"  Duration: {code_result['duration']:.1f}s")
    if code_result["error"]:
        print(f"  Error: {code_result['error'][:200]}")
    else:
        print(f"  Result: {code_result['result'][:200]}")

    # Test ToolCallingAgent (hypothesis: should work better)
    tool_result = test_agent("ToolCallingAgent", model, task)
    print("\nToolCallingAgent Result:")
    print(f"  Success: {tool_result['success']}")
    print(f"  Duration: {tool_result['duration']:.1f}s")
    if tool_result["error"]:
        print(f"  Error: {tool_result['error'][:200]}")
    else:
        print(f"  Result: {tool_result['result'][:200]}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"CodeAgent:       {'PASS' if code_result['success'] else 'FAIL'} ({code_result['duration']:.1f}s)")
    print(f"ToolCallingAgent: {'PASS' if tool_result['success'] else 'FAIL'} ({tool_result['duration']:.1f}s)")

    if tool_result["success"] and not code_result["success"]:
        print("\nConclusion: ToolCallingAgent works better for qwen3-coder!")
        print("Recommendation: Use ToolCallingAgent for qwen3-coder models")
    elif code_result["success"] and tool_result["success"]:
        print("\nConclusion: Both agents work. CodeAgent may be preferred for code-gen.")
    elif not code_result["success"] and not tool_result["success"]:
        print("\nConclusion: Neither agent works well with this model.")
    else:
        print("\nConclusion: CodeAgent works better than ToolCallingAgent.")


if __name__ == "__main__":
    main()
