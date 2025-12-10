"""Tests for the security module - path jailing, truncation, timeouts."""

import os
import time
from pathlib import Path

import pytest

from local_brain.security import (
    set_project_root,
    get_project_root,
    is_path_safe,
    safe_path,
    validate_path,
    is_sensitive_file,
    truncate_output,
    with_timeout,
    ToolTimeoutError,
    BLOCKED_PATTERNS,
)


class TestPathJailing:
    """Tests for path jailing security features."""

    def test_set_and_get_project_root(self, tmp_path):
        """Test setting and getting project root."""
        result = set_project_root(tmp_path)
        assert result == tmp_path.resolve()
        assert get_project_root() == tmp_path.resolve()

    def test_set_project_root_none_uses_cwd(self):
        """Test that None uses current working directory."""
        original_cwd = Path.cwd().resolve()
        result = set_project_root(None)
        assert result == original_cwd

    def test_is_path_safe_within_root(self, tmp_path):
        """Test that paths within root are safe."""
        set_project_root(tmp_path)
        test_file = tmp_path / "safe_file.txt"
        test_file.touch()

        # Absolute paths within root
        assert is_path_safe(test_file) is True
        assert is_path_safe(str(test_file)) is True
        # Note: is_path_safe resolves paths, so relative paths are resolved against cwd
        # Use safe_path() for relative path resolution against project root

    def test_is_path_safe_outside_root(self, tmp_path):
        """Test that paths outside root are not safe."""
        set_project_root(tmp_path)

        assert is_path_safe("/etc/passwd") is False
        assert is_path_safe("/tmp") is False
        assert is_path_safe("..") is False

    def test_is_path_safe_traversal_attack(self, tmp_path):
        """Test path traversal attacks are blocked."""
        set_project_root(tmp_path)

        # Various traversal attempts
        assert is_path_safe("../../../etc/passwd") is False
        assert is_path_safe("subdir/../../etc/passwd") is False
        assert is_path_safe("./../../etc/passwd") is False

    def test_is_path_safe_nested_directory(self, tmp_path):
        """Test nested directories within root are safe."""
        set_project_root(tmp_path)
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)
        nested_file = nested / "file.txt"
        nested_file.touch()

        # Absolute paths within root
        assert is_path_safe(nested_file) is True
        assert is_path_safe(str(nested_file)) is True

    def test_safe_path_resolves_correctly(self, tmp_path):
        """Test safe_path returns resolved paths."""
        set_project_root(tmp_path)
        test_file = tmp_path / "test.txt"
        test_file.touch()

        resolved = safe_path("test.txt")
        assert resolved == test_file.resolve()
        assert resolved.is_absolute()

    def test_safe_path_raises_on_escape(self, tmp_path):
        """Test safe_path raises PermissionError on path escape."""
        set_project_root(tmp_path)

        with pytest.raises(PermissionError) as exc_info:
            safe_path("/etc/passwd")

        assert "outside project root" in str(exc_info.value)

    def test_safe_path_raises_on_traversal(self, tmp_path):
        """Test safe_path raises on path traversal."""
        set_project_root(tmp_path)

        with pytest.raises(PermissionError):
            safe_path("../../../etc/passwd")

    def test_validate_path_returns_tuple(self, tmp_path):
        """Test validate_path returns correct tuple."""
        set_project_root(tmp_path)
        test_file = tmp_path / "valid.txt"
        test_file.touch()

        # Valid path
        is_valid, message = validate_path(str(test_file))
        assert is_valid is True
        assert str(test_file.resolve()) in message

        # Invalid path
        is_valid, message = validate_path("/etc/passwd")
        assert is_valid is False
        assert "outside project root" in message

    def test_symlink_escape_blocked(self, tmp_path):
        """Test that symlinks pointing outside root are blocked."""
        set_project_root(tmp_path)

        # Create a symlink pointing outside the project
        link_path = tmp_path / "escape_link"
        try:
            link_path.symlink_to("/etc")

            # The symlink itself is in the project, but resolves outside
            assert is_path_safe(link_path) is False
        except OSError:
            pytest.skip("Symlink creation not supported")


class TestSensitiveFileBlocking:
    """Tests for sensitive file detection."""

    def test_env_files_blocked(self, tmp_path):
        """Test .env files are detected as sensitive."""
        set_project_root(tmp_path)

        assert is_sensitive_file(".env") is True
        assert is_sensitive_file(".env.local") is True
        assert is_sensitive_file(".env.production") is True
        assert is_sensitive_file(tmp_path / ".env") is True

    def test_git_config_blocked(self, tmp_path):
        """Test .git/config is detected as sensitive."""
        assert is_sensitive_file(".git/config") is True
        assert is_sensitive_file(tmp_path / ".git" / "config") is True

    def test_key_files_blocked(self):
        """Test private key files are detected as sensitive."""
        assert is_sensitive_file("server.pem") is True
        assert is_sensitive_file("private.key") is True
        assert is_sensitive_file("id_rsa") is True
        assert is_sensitive_file("id_ed25519") is True

    def test_normal_files_not_blocked(self):
        """Test normal files are not blocked."""
        assert is_sensitive_file("main.py") is False
        assert is_sensitive_file("config.json") is False
        assert is_sensitive_file("README.md") is False
        assert is_sensitive_file(".gitignore") is False

    def test_blocked_patterns_constant(self):
        """Test BLOCKED_PATTERNS contains expected patterns."""
        assert ".env" in BLOCKED_PATTERNS
        assert ".git/config" in BLOCKED_PATTERNS
        assert "*.pem" in BLOCKED_PATTERNS
        assert "*.key" in BLOCKED_PATTERNS


class TestOutputTruncation:
    """Tests for output truncation utility."""

    def test_short_content_unchanged(self):
        """Test short content is not truncated."""
        content = "Hello, world!\nLine 2\nLine 3"
        result = truncate_output(content, max_lines=100, max_chars=10000)
        assert result == content
        assert "[TRUNCATED" not in result

    def test_line_truncation(self):
        """Test content is truncated by line count."""
        lines = [f"Line {i}" for i in range(200)]
        content = "\n".join(lines)

        result = truncate_output(content, max_lines=50, max_chars=100000)

        assert "[TRUNCATED" in result
        assert "200 lines" in result
        result_lines = result.split("\n")
        # 50 lines + blank line + truncation message
        assert result_lines[0] == "Line 0"
        assert "Line 49" in result

    def test_char_truncation(self):
        """Test content is truncated by character count."""
        content = "x" * 5000

        result = truncate_output(content, max_lines=1000, max_chars=1000)

        assert "[TRUNCATED" in result
        assert "5000 chars" in result
        assert len(result) > 1000  # Includes truncation message
        assert result.startswith("x" * 1000)

    def test_combined_truncation(self):
        """Test both line and char limits are respected."""
        lines = ["x" * 100 for _ in range(100)]
        content = "\n".join(lines)

        result = truncate_output(content, max_lines=10, max_chars=500)

        assert "[TRUNCATED" in result
        # Should be truncated by chars (500) before lines (10 * 100 = 1000)

    def test_truncation_message_format(self):
        """Test truncation message contains useful information."""
        content = "a\n" * 200

        result = truncate_output(content, max_lines=50, max_chars=10000)

        assert "TRUNCATED" in result
        assert "Use more specific queries" in result

    def test_empty_content(self):
        """Test empty content is handled."""
        result = truncate_output("", max_lines=100, max_chars=10000)
        assert result == ""
        assert "[TRUNCATED" not in result

    def test_single_line_content(self):
        """Test single line content works."""
        content = "Single line"
        result = truncate_output(content, max_lines=100, max_chars=10000)
        assert result == "Single line"


class TestTimeoutDecorator:
    """Tests for the timeout decorator."""

    def test_fast_function_succeeds(self):
        """Test fast functions complete normally."""

        @with_timeout(5)
        def fast_func():
            return "success"

        result = fast_func()
        assert result == "success"

    def test_slow_function_times_out(self):
        """Test slow functions raise ToolTimeoutError."""

        @with_timeout(1)
        def slow_func():
            time.sleep(5)
            return "should not reach"

        # This test only works on Unix (SIGALRM)
        if not hasattr(os, "fork"):
            pytest.skip("SIGALRM not available on this platform")

        with pytest.raises(ToolTimeoutError) as exc_info:
            slow_func()

        assert "timed out" in str(exc_info.value)
        assert "slow_func" in str(exc_info.value)

    def test_timeout_preserves_function_metadata(self):
        """Test decorator preserves function name and docstring."""

        @with_timeout(5)
        def documented_func():
            """This is the docstring."""
            return 42

        assert documented_func.__name__ == "documented_func"
        assert "docstring" in documented_func.__doc__

    def test_timeout_with_arguments(self):
        """Test timeout works with function arguments."""

        @with_timeout(5)
        def func_with_args(a, b, keyword=None):
            return (a, b, keyword)

        result = func_with_args(1, 2, keyword="test")
        assert result == (1, 2, "test")

    def test_timeout_with_return_value(self):
        """Test timeout preserves return values."""

        @with_timeout(5)
        def complex_return():
            return {"key": "value", "list": [1, 2, 3]}

        result = complex_return()
        assert result == {"key": "value", "list": [1, 2, 3]}

    def test_timeout_propagates_exceptions(self):
        """Test non-timeout exceptions are propagated."""

        @with_timeout(5)
        def raises_error():
            raise ValueError("test error")

        with pytest.raises(ValueError) as exc_info:
            raises_error()

        assert "test error" in str(exc_info.value)


class TestIntegrationPathJailingWithTools:
    """Integration tests for path jailing with tool functions."""

    def test_read_file_respects_jail(self, tmp_path):
        """Test read_file tool respects path jail."""
        from local_brain.smolagent import read_file

        set_project_root(tmp_path)

        # Create a file inside the jail
        safe_file = tmp_path / "safe.txt"
        safe_file.write_text("Safe content")

        # Should succeed
        result = read_file(str(safe_file))
        assert "Safe content" in result

        # Should fail - outside jail
        result = read_file("/etc/passwd")
        assert "Error" in result
        assert "outside project root" in result

    def test_list_directory_respects_jail(self, tmp_path):
        """Test list_directory tool respects path jail."""
        from local_brain.smolagent import list_directory

        set_project_root(tmp_path)

        # Create files inside the jail
        (tmp_path / "file1.py").touch()
        (tmp_path / "file2.py").touch()

        # Should succeed
        result = list_directory(str(tmp_path), "*.py")
        assert "file1.py" in result
        assert "file2.py" in result

        # Should fail - outside jail
        result = list_directory("/etc")
        assert "Error" in result

    def test_file_info_respects_jail(self, tmp_path):
        """Test file_info tool respects path jail."""
        from local_brain.smolagent import file_info

        set_project_root(tmp_path)

        # Create a file inside the jail
        safe_file = tmp_path / "info_test.txt"
        safe_file.write_text("content")

        # Should succeed
        result = file_info(str(safe_file))
        assert "Path:" in result
        assert "Size:" in result

        # Should fail - outside jail
        result = file_info("/etc/passwd")
        assert "Error" in result

    def test_sensitive_file_blocked_in_tools(self, tmp_path):
        """Test sensitive files are blocked even within jail."""
        from local_brain.smolagent import read_file

        set_project_root(tmp_path)

        # Create a .env file inside the jail
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET=value")

        # Should be blocked
        result = read_file(str(env_file))
        assert "Error" in result
        assert "sensitive" in result.lower() or "blocked" in result.lower()
