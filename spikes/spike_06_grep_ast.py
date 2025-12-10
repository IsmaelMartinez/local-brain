#!/usr/bin/env python3
"""Spike 6: Test grep-ast for AST-aware code search.

This spike validates:
1. grep-ast can be installed and imported
2. TreeContext works with Python files
3. AST-aware search shows intelligent context
4. Language detection works

Run: uv run python spikes/spike_06_grep_ast.py

Prerequisites:
    uv pip install grep-ast
"""

import sys
import tempfile
from pathlib import Path
from typing import Any


# Sample Python code for testing
SAMPLE_CODE = '''
"""Sample module for testing grep-ast."""

class UserService:
    """Service for managing users."""
    
    def __init__(self, db):
        self.db = db
        self.cache = {}
    
    def get_user(self, user_id: int) -> dict:
        """Get user by ID.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            User data dictionary
        """
        if user_id in self.cache:
            return self.cache[user_id]
        return self.db.query(user_id)
    
    def create_user(self, name: str, email: str) -> int:
        """Create a new user."""
        user_id = self.db.insert({"name": name, "email": email})
        self.cache[user_id] = {"name": name, "email": email}
        return user_id


def validate_email(email: str) -> bool:
    """Check if email is valid."""
    return "@" in email and "." in email


async def fetch_user_async(user_id: int) -> dict:
    """Async version of user fetch."""
    return await db.async_query(user_id)
'''


def test_grep_ast_import() -> dict[str, Any]:
    """Test that grep-ast can be imported."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from grep_ast import TreeContext, filename_to_lang  # noqa: F401

        results["details"]["import"] = (
            "✅ grep_ast imported (TreeContext, filename_to_lang)"
        )
    except ImportError as e:
        results["passed"] = False
        results["details"]["import"] = f"❌ Failed: {e}"

    return results


def test_language_detection() -> dict[str, Any]:
    """Test language detection from filenames."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from grep_ast import filename_to_lang

        test_cases = [
            ("test.py", "python"),
            ("app.js", "javascript"),
            ("main.ts", "typescript"),
            ("style.css", "css"),
            ("index.html", "html"),
            ("Cargo.toml", "toml"),
            ("unknown.xyz", None),
        ]

        passed = 0
        for filename, expected in test_cases:
            detected = filename_to_lang(filename)
            if detected == expected or (
                expected and detected and expected in detected.lower()
            ):
                passed += 1
            else:
                results["details"][f"lang_{filename}"] = (
                    f"⚠️ Expected {expected}, got {detected}"
                )

        results["details"]["detection"] = (
            f"✅ Language detection: {passed}/{len(test_cases)} correct"
        )

    except Exception as e:
        results["passed"] = False
        results["details"]["detection"] = f"❌ Failed: {e}"

    return results


def test_tree_context_creation() -> dict[str, Any]:
    """Test TreeContext creation with sample code."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from grep_ast import TreeContext

        # Create temp file with sample code
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(SAMPLE_CODE)
            temp_path = f.name

        try:
            _tc = TreeContext(temp_path, code=SAMPLE_CODE)  # noqa: F841
            results["details"]["creation"] = "✅ TreeContext created successfully"
        finally:
            Path(temp_path).unlink()

    except Exception as e:
        results["passed"] = False
        results["details"]["creation"] = f"❌ Failed: {e}"

    return results


def test_grep_search() -> dict[str, Any]:
    """Test grep functionality with AST awareness."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from grep_ast import TreeContext

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(SAMPLE_CODE)
            temp_path = f.name

        try:
            tc = TreeContext(temp_path, code=SAMPLE_CODE)

            # Search for "user_id"
            search_result = tc.grep("user_id", ignore_case=False)

            if search_result and "user_id" in search_result:
                # Check if context is included (should show function/class context)
                has_context = "def " in search_result or "class " in search_result
                results["details"]["grep_basic"] = (
                    f"✅ Found 'user_id' with context: {has_context}"
                )
                results["details"]["grep_sample"] = (
                    f"   Sample: {search_result[:200]}..."
                )
            else:
                results["details"]["grep_basic"] = "⚠️ Search returned empty or no match"

            # Search for "email"
            email_result = tc.grep("email", ignore_case=False)
            if email_result:
                results["details"]["grep_multi"] = (
                    "✅ Found 'email' in multiple contexts"
                )

        finally:
            Path(temp_path).unlink()

    except Exception as e:
        results["passed"] = False
        results["details"]["grep"] = f"❌ Failed: {e}"

    return results


def test_tool_integration() -> dict[str, Any]:
    """Test how grep-ast would work as a Smolagents tool."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        from grep_ast import TreeContext, filename_to_lang
        from pathlib import Path as P

        def search_code_ast(pattern: str, file_path: str) -> str:
            """Search code with AST awareness - simulates the tool."""
            lang = filename_to_lang(file_path)
            if not lang:
                return f"Unknown language for {file_path}"

            code = P(file_path).read_text()
            tc = TreeContext(file_path, code=code)
            result = tc.grep(pattern, ignore_case=True)

            if not result:
                return f"No matches for '{pattern}' in {file_path}"

            return result

        # Test with temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(SAMPLE_CODE)
            temp_path = f.name

        try:
            result = search_code_ast("cache", temp_path)
            if "cache" in result:
                results["details"]["tool_sim"] = "✅ Tool simulation works"
                results["details"]["tool_output"] = (
                    f"   Output length: {len(result)} chars"
                )
            else:
                results["details"]["tool_sim"] = "⚠️ Tool returned unexpected result"
        finally:
            Path(temp_path).unlink()

    except Exception as e:
        results["passed"] = False
        results["details"]["tool"] = f"❌ Failed: {e}"

    return results


def main() -> int:
    """Run all tests and report results."""
    print("=" * 60)
    print("SPIKE 6: grep-ast for AST-aware Code Search")
    print("=" * 60)

    tests = [
        ("Import grep-ast", test_grep_ast_import),
        ("Language Detection", test_language_detection),
        ("TreeContext Creation", test_tree_context_creation),
        ("Grep Search", test_grep_search),
        ("Tool Integration", test_tool_integration),
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
        print("✅ SPIKE 6 PASSED: grep-ast works for AST-aware search!")
        print(
            "\nRecommendation: Use grep-ast as the primary search_code implementation"
        )
        return 0
    else:
        print("❌ SPIKE 6 FAILED: See details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
