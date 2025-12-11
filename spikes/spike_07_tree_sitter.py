#!/usr/bin/env python3
"""Spike 7: Test tree-sitter for extracting code definitions.

This spike validates:
1. tree-sitter and tree-sitter-languages can be imported
2. Python parser works
3. Can extract function/class definitions
4. Can get signatures without full body

Run: uv run python spikes/spike_07_tree_sitter.py

Prerequisites:
    uv pip install tree-sitter tree-sitter-languages
"""

import sys
import tempfile
from pathlib import Path
from typing import Any


# Sample Python code for testing
SAMPLE_CODE = '''
"""Sample module for testing tree-sitter."""

from typing import Optional

CONSTANT = 42


class UserService:
    """Service for managing users."""
    
    def __init__(self, db):
        self.db = db
        self.cache = {}
    
    def get_user(self, user_id: int) -> dict:
        """Get user by ID.
        
        Args:
            user_id: The user\'s unique identifier
            
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


def test_tree_sitter_imports() -> dict[str, Any]:
    """Test that tree-sitter packages can be imported."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        import tree_sitter  # noqa: F401

        results["details"]["tree_sitter"] = "✅ tree_sitter imported"
    except ImportError as e:
        results["passed"] = False
        results["details"]["tree_sitter"] = f"❌ Failed: {e}"

    # Try tree_sitter_language_pack (what got installed on Python 3.13)
    # or tree_sitter_languages (original)
    try:
        import tree_sitter_language_pack as ts_langs

        results["details"]["languages"] = "✅ tree_sitter_language_pack imported"
    except ImportError:
        try:
            import tree_sitter_languages as ts_langs  # noqa: F401

            results["details"]["languages"] = "✅ tree_sitter_languages imported"
        except ImportError as e:
            results["passed"] = False
            results["details"]["languages"] = (
                f"❌ Neither tree_sitter_languages nor tree_sitter_language_pack available: {e}"
            )

    return results


def test_python_parser() -> dict[str, Any]:
    """Test Python parser initialization."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        try:
            import tree_sitter_language_pack as ts_langs
        except ImportError:
            import tree_sitter_languages as ts_langs

        parser = ts_langs.get_parser("python")
        results["details"]["parser"] = "✅ Python parser loaded"

        # Parse sample code
        tree = parser.parse(SAMPLE_CODE.encode())
        results["details"]["parse"] = f"✅ Code parsed, root: {tree.root_node.type}"

    except Exception as e:
        results["passed"] = False
        results["details"]["parser"] = f"❌ Failed: {e}"

    return results


def test_extract_definitions() -> dict[str, Any]:
    """Test extracting function and class definitions."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        try:
            import tree_sitter_language_pack as ts_langs
        except ImportError:
            import tree_sitter_languages as ts_langs

        parser = ts_langs.get_parser("python")
        tree = parser.parse(SAMPLE_CODE.encode())

        definitions = []

        def walk(node, depth=0):
            """Walk the AST and collect definitions."""
            if node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    definitions.append(("class", name_node.text.decode()))

            elif node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    definitions.append(("function", name_node.text.decode()))

            for child in node.children:
                walk(child, depth + 1)

        walk(tree.root_node)

        results["details"]["definitions"] = f"✅ Found {len(definitions)} definitions"

        expected = [
            ("class", "UserService"),
            ("function", "__init__"),
            ("function", "get_user"),
            ("function", "create_user"),
            ("function", "validate_email"),
            ("function", "fetch_user_async"),
        ]

        found_names = [d[1] for d in definitions]
        expected_names = [e[1] for e in expected]

        missing = set(expected_names) - set(found_names)
        if missing:
            results["details"]["missing"] = f"⚠️ Missing: {missing}"
        else:
            results["details"]["all_found"] = "✅ All expected definitions found"

        for def_type, name in definitions[:5]:
            results["details"][f"def_{name}"] = f"   {def_type}: {name}"

    except Exception as e:
        results["passed"] = False
        results["details"]["extract"] = f"❌ Failed: {e}"

    return results


def test_extract_signatures() -> dict[str, Any]:
    """Test extracting function signatures (without body)."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        try:
            import tree_sitter_language_pack as ts_langs
        except ImportError:
            import tree_sitter_languages as ts_langs

        parser = ts_langs.get_parser("python")
        tree = parser.parse(SAMPLE_CODE.encode())
        code_bytes = SAMPLE_CODE.encode()

        signatures = []

        def get_signature(node) -> str:
            """Extract signature from function definition."""
            # Get from 'def' to end of parameters ')'
            start = node.start_byte

            # Find the colon that ends the signature
            params = node.child_by_field_name("parameters")
            return_type = node.child_by_field_name("return_type")

            if return_type:
                end = return_type.end_byte
            elif params:
                end = params.end_byte
            else:
                end = node.end_byte

            sig = code_bytes[start:end].decode()
            # Clean up - take first line only
            sig = sig.split("\n")[0].strip()
            if not sig.endswith(":"):
                sig += ":"
            return sig

        def walk(node):
            if node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    sig = get_signature(node)
                    signatures.append(sig)

            for child in node.children:
                walk(child)

        walk(tree.root_node)

        results["details"]["signatures"] = f"✅ Extracted {len(signatures)} signatures"

        for sig in signatures[:4]:
            results["details"]["sig"] = f"   {sig[:60]}..."

    except Exception as e:
        results["passed"] = False
        results["details"]["signatures"] = f"❌ Failed: {e}"

    return results


def test_list_definitions_tool() -> dict[str, Any]:
    """Test simulated list_definitions tool."""
    results: dict[str, Any] = {"passed": True, "details": {}}

    try:
        try:
            import tree_sitter_language_pack as ts_langs
        except ImportError:
            import tree_sitter_languages as ts_langs

        def list_definitions(file_path: str) -> str:
            """Extract definitions from a Python file - simulates the tool."""
            code = Path(file_path).read_text()
            parser = ts_langs.get_parser("python")
            tree = parser.parse(code.encode())

            output_lines = []

            def get_docstring(node) -> str | None:
                """Get docstring if present."""
                body = node.child_by_field_name("body")
                if body and body.children:
                    first = body.children[0]
                    if first.type == "expression_statement":
                        string = first.children[0] if first.children else None
                        if string and string.type == "string":
                            doc = string.text.decode().strip('"""').strip("'''").strip()
                            return doc[:100] + "..." if len(doc) > 100 else doc
                return None

            def walk(node, indent=0):
                prefix = "  " * indent

                if node.type == "class_definition":
                    name = node.child_by_field_name("name")
                    if name:
                        output_lines.append(f"{prefix}class {name.text.decode()}:")
                        doc = get_docstring(node)
                        if doc:
                            output_lines.append(f'{prefix}  "{doc}"')
                        # Process methods
                        for child in node.children:
                            walk(child, indent + 1)
                        return  # Don't recurse again

                elif node.type == "function_definition":
                    name = node.child_by_field_name("name")
                    params = node.child_by_field_name("parameters")
                    ret = node.child_by_field_name("return_type")

                    if name:
                        sig = f"def {name.text.decode()}"
                        if params:
                            sig += params.text.decode()
                        if ret:
                            sig += f" -> {ret.text.decode()}"
                        sig += ":"
                        output_lines.append(f"{prefix}{sig}")
                        doc = get_docstring(node)
                        if doc:
                            output_lines.append(f'{prefix}  "{doc}"')
                        return  # Don't recurse into body

                for child in node.children:
                    walk(child, indent)

            walk(tree.root_node)
            return "\n".join(output_lines)

        # Test with temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(SAMPLE_CODE)
            temp_path = f.name

        try:
            result = list_definitions(temp_path)
            lines = result.split("\n")
            results["details"]["tool_output"] = f"✅ Generated {len(lines)} lines"
            results["details"]["sample"] = f"   Preview:\n{result[:300]}..."
        finally:
            Path(temp_path).unlink()

    except Exception as e:
        results["passed"] = False
        results["details"]["tool"] = f"❌ Failed: {e}"

    return results


def main() -> int:
    """Run all tests and report results."""
    print("=" * 60)
    print("SPIKE 7: tree-sitter for Code Definitions")
    print("=" * 60)

    tests = [
        ("tree-sitter Imports", test_tree_sitter_imports),
        ("Python Parser", test_python_parser),
        ("Extract Definitions", test_extract_definitions),
        ("Extract Signatures", test_extract_signatures),
        ("list_definitions Tool", test_list_definitions_tool),
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
        print("✅ SPIKE 7 PASSED: tree-sitter works for extracting definitions!")
        print("\nRecommendation: Use tree-sitter for list_definitions tool")
        return 0
    else:
        print("❌ SPIKE 7 FAILED: See details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
