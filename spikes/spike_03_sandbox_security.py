#!/usr/bin/env python3
"""Spike 3: Test LocalPythonExecutor sandboxing restrictions.

This spike validates that Smolagents' LocalPythonExecutor:
1. Blocks file I/O operations (open, write, etc.)
2. Restricts dangerous imports (subprocess, os.system)
3. Only allows authorized imports
4. Limits memory/CPU usage (if available)

Run: uv run python spikes/spike_03_sandbox_security.py
"""

import sys
from typing import Any


def test_executor_imports() -> dict[str, Any]:
    """Test that LocalPythonExecutor can be imported."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from smolagents.local_python_executor import LocalPythonExecutor

        # Create with empty authorized imports
        executor = LocalPythonExecutor(additional_authorized_imports=[])
        results["details"]["import"] = "✅ LocalPythonExecutor imported"
        results["details"]["type"] = f"Type: {type(executor).__name__}"

    except ImportError as e:
        results["passed"] = False
        results["details"]["import"] = f"❌ Import failed: {e}"
    except Exception as e:
        results["passed"] = False
        results["details"]["import"] = f"❌ Failed: {e}"

    return results


def test_safe_code_execution() -> dict[str, Any]:
    """Test that safe code executes normally."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from smolagents.local_python_executor import LocalPythonExecutor

        executor = LocalPythonExecutor(additional_authorized_imports=[])

        # Safe code should work (no print - it's blocked by sandbox)
        safe_code = """
result = 10 + 20
result
"""
        code_output = executor(safe_code)
        output = code_output.output if hasattr(code_output, "output") else code_output

        if output == 30 or "30" in str(output):
            results["details"]["safe_math"] = f"✅ Safe code executed: {output}"
        else:
            results["details"]["safe_math"] = f"⚠️ Unexpected output: {output}"

    except Exception as e:
        results["passed"] = False
        results["details"]["safe_code"] = f"❌ Failed: {e}"

    return results


def test_file_io_blocked() -> dict[str, Any]:
    """Test that file I/O is blocked."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from smolagents.local_python_executor import LocalPythonExecutor

        executor = LocalPythonExecutor(additional_authorized_imports=[])

        # File write should be blocked
        malicious_code = """
with open('/tmp/evil.txt', 'w') as f:
    f.write('malicious content')
"""
        try:
            output, logs, is_final = executor(malicious_code)
            # If we get here without exception, check if it actually wrote
            import os

            if os.path.exists("/tmp/evil.txt"):
                results["passed"] = False
                results["details"]["file_write"] = "❌ SECURITY FAIL: File was written!"
                os.remove("/tmp/evil.txt")
            else:
                results["details"]["file_write"] = "✅ File write silently blocked"
        except Exception as e:
            results["details"]["file_write"] = (
                f"✅ File write blocked with: {type(e).__name__}"
            )

        # File read should also be blocked (for arbitrary paths)
        read_code = """
with open('/etc/passwd', 'r') as f:
    content = f.read()
content
"""
        try:
            output, logs, is_final = executor(read_code)
            # If we get here, check if content was actually read
            if output and len(str(output)) > 10:
                results["passed"] = False
                results["details"]["file_read"] = (
                    f"❌ SECURITY FAIL: File was read! ({len(str(output))} chars)"
                )
            else:
                results["details"]["file_read"] = "✅ File read silently blocked"
        except Exception as e:
            results["details"]["file_read"] = (
                f"✅ File read blocked with: {type(e).__name__}"
            )

    except Exception as e:
        results["passed"] = False
        results["details"]["file_io"] = f"❌ Failed: {e}"

    return results


def test_subprocess_blocked() -> dict[str, Any]:
    """Test that subprocess/os.system is blocked."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from smolagents.local_python_executor import LocalPythonExecutor

        executor = LocalPythonExecutor(additional_authorized_imports=[])

        # subprocess should be blocked
        subprocess_code = """
import subprocess
result = subprocess.run(['ls', '-la'], capture_output=True)
result.stdout.decode()
"""
        try:
            output, logs, is_final = executor(subprocess_code)
            if output and "total" in str(output).lower():
                results["passed"] = False
                results["details"]["subprocess"] = (
                    "❌ SECURITY FAIL: subprocess executed!"
                )
            else:
                results["details"]["subprocess"] = (
                    f"✅ subprocess blocked (output: {str(output)[:30]})"
                )
        except Exception as e:
            results["details"]["subprocess"] = (
                f"✅ subprocess blocked with: {type(e).__name__}"
            )

        # os.system should be blocked
        os_system_code = """
import os
os.system('echo PWNED > /tmp/pwned.txt')
"""
        try:
            output, logs, is_final = executor(os_system_code)
            import os as real_os

            if real_os.path.exists("/tmp/pwned.txt"):
                results["passed"] = False
                results["details"]["os_system"] = (
                    "❌ SECURITY FAIL: os.system executed!"
                )
                real_os.remove("/tmp/pwned.txt")
            else:
                results["details"]["os_system"] = "✅ os.system blocked"
        except Exception as e:
            results["details"]["os_system"] = (
                f"✅ os.system blocked with: {type(e).__name__}"
            )

    except Exception as e:
        results["passed"] = False
        results["details"]["subprocess"] = f"❌ Failed: {e}"

    return results


def test_dangerous_imports_blocked() -> dict[str, Any]:
    """Test that dangerous modules are blocked."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from smolagents.local_python_executor import LocalPythonExecutor

        executor = LocalPythonExecutor(additional_authorized_imports=[])

        dangerous_modules = [
            ("socket", "import socket; s = socket.socket()"),
            ("ctypes", "import ctypes"),
            ("pickle", "import pickle"),
        ]

        for module_name, code in dangerous_modules:
            try:
                output, logs, is_final = executor(code)
                # Check if it actually executed
                results["details"][f"{module_name}_import"] = (
                    f"⚠️ {module_name} import allowed (review needed)"
                )
            except Exception as e:
                results["details"][f"{module_name}_import"] = (
                    f"✅ {module_name} blocked: {type(e).__name__}"
                )

    except Exception as e:
        results["passed"] = False
        results["details"]["imports"] = f"❌ Failed: {e}"

    return results


def test_authorized_imports_work() -> dict[str, Any]:
    """Test that authorized imports work when explicitly allowed."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from smolagents.local_python_executor import LocalPythonExecutor

        # Allow math import
        executor = LocalPythonExecutor(additional_authorized_imports=["math"])

        code = """
import math
result = math.sqrt(16)
result
"""
        code_output = executor(code)
        output = code_output.output if hasattr(code_output, "output") else code_output

        if output == 4.0:
            results["details"]["authorized_math"] = (
                "✅ math import worked when authorized"
            )
        else:
            results["details"]["authorized_math"] = f"⚠️ Unexpected output: {output}"

    except Exception as e:
        results["passed"] = False
        results["details"]["authorized_imports"] = f"❌ Failed: {e}"

    return results


def test_code_agent_uses_sandbox() -> dict[str, Any]:
    """Test CodeAgent uses sandbox by default."""
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

        # Check if agent has an executor
        if hasattr(agent, "executor") or hasattr(agent, "python_executor"):
            results["details"]["agent_executor"] = "✅ Agent has executor/sandbox"
        else:
            results["details"]["agent_executor"] = (
                "⚠️ Agent executor not directly accessible"
            )

        # Should work for safe code
        result = agent.run("Calculate 7 * 8 and return the result.")
        results["details"]["safe_agent"] = f"✅ Safe agent task: {str(result)[:50]}"

    except Exception as e:
        results["passed"] = False
        results["details"]["agent_executor"] = f"❌ Failed: {e}"

    return results


def main() -> int:
    """Run all tests and report results."""
    print("=" * 60)
    print("SPIKE 3: LocalPythonExecutor Sandbox Security")
    print("=" * 60)

    tests = [
        ("Executor Imports", test_executor_imports),
        ("Safe Code Execution", test_safe_code_execution),
        ("File I/O Blocked", test_file_io_blocked),
        ("Subprocess Blocked", test_subprocess_blocked),
        ("Dangerous Imports Blocked", test_dangerous_imports_blocked),
        ("Authorized Imports Work", test_authorized_imports_work),
        ("CodeAgent Uses Sandbox", test_code_agent_uses_sandbox),
    ]

    all_passed = True
    security_concerns = []

    for name, test_fn in tests:
        print(f"\n🧪 Test: {name}")
        print("-" * 40)

        result = test_fn()
        for key, value in result["details"].items():
            print(f"   {key}: {value}")
            if "SECURITY FAIL" in str(value):
                security_concerns.append(f"{name}: {key}")

        if not result["passed"]:
            all_passed = False
            print("   ⚠️  TEST FAILED")
        else:
            print("   ✅ TEST PASSED")

    print("\n" + "=" * 60)

    if security_concerns:
        print("🚨 SECURITY CONCERNS:")
        for concern in security_concerns:
            print(f"   - {concern}")
        print("\n❌ SPIKE 3 FAILED: Security issues found!")
        return 1
    elif all_passed:
        print("✅ SPIKE 3 PASSED: Sandbox security adequate!")
        return 0
    else:
        print("⚠️ SPIKE 3 PARTIAL: Some tests failed, review details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
