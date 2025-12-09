"""Tests for the tools module."""

from local_brain.security import set_project_root
from local_brain.tools.file_tools import read_file, list_directory, file_info
from local_brain.tools.git_tools import git_status, git_log
from local_brain.tools.shell_tools import (
    run_command,
    ALLOWED_COMMANDS,
    BLOCKED_COMMANDS,
)


class TestFileTools:
    """Tests for file tools."""

    def test_read_file_success(self, tmp_path):
        """Test reading an existing file within project root."""
        # Set project root to tmp_path for this test
        set_project_root(tmp_path)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")
        
        result = read_file(str(test_file))
        assert result == "Hello, world!"

    def test_read_file_not_found(self, tmp_path):
        """Test reading a non-existent file within project root."""
        set_project_root(tmp_path)
        
        result = read_file("nonexistent_file.txt")
        assert "Error" in result
        assert "not found" in result

    def test_read_file_outside_root(self, tmp_path):
        """Test that reading files outside project root is blocked."""
        set_project_root(tmp_path)
        
        result = read_file("/etc/passwd")
        assert "Error" in result
        assert "outside project root" in result

    def test_list_directory_success(self, tmp_path):
        """Test listing a directory within project root."""
        set_project_root(tmp_path)
        
        # Create some files
        (tmp_path / "test1.py").write_text("# test")
        (tmp_path / "test2.py").write_text("# test")

        result = list_directory(str(tmp_path), "*.py")
        assert "test1.py" in result
        assert "test2.py" in result

    def test_list_directory_not_found(self, tmp_path):
        """Test listing a non-existent directory within project root."""
        set_project_root(tmp_path)
        
        result = list_directory("nonexistent_subdir")
        assert "Error" in result

    def test_list_directory_outside_root(self, tmp_path):
        """Test that listing directories outside project root is blocked."""
        set_project_root(tmp_path)
        
        result = list_directory("/etc")
        assert "Error" in result
        assert "outside project root" in result

    def test_file_info_success(self, tmp_path):
        """Test getting file info within project root."""
        set_project_root(tmp_path)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        result = file_info(str(test_file))
        assert "Path:" in result
        assert "Size:" in result
        assert "Modified:" in result

    def test_file_info_not_found(self, tmp_path):
        """Test file info for non-existent file within project root."""
        set_project_root(tmp_path)
        
        result = file_info("nonexistent.txt")
        assert "Error" in result

    def test_file_info_outside_root(self, tmp_path):
        """Test that file info outside project root is blocked."""
        set_project_root(tmp_path)
        
        result = file_info("/etc/passwd")
        assert "Error" in result
        assert "outside project root" in result


class TestGitTools:
    """Tests for git tools."""

    def test_git_status(self):
        """Test git status returns something."""
        result = git_status()
        # Either shows status or error (if not in a git repo)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_git_log(self):
        """Test git log returns something."""
        result = git_log(count=5)
        assert isinstance(result, str)
        assert len(result) > 0


class TestShellTools:
    """Tests for shell tools."""

    def test_allowed_commands_list(self):
        """Test that allowed commands list is populated."""
        assert "ls" in ALLOWED_COMMANDS
        assert "cat" in ALLOWED_COMMANDS
        assert "grep" in ALLOWED_COMMANDS

    def test_blocked_commands_list(self):
        """Test that blocked commands list includes dangerous commands."""
        assert "rm" in BLOCKED_COMMANDS
        assert "sudo" in BLOCKED_COMMANDS
        assert "bash" in BLOCKED_COMMANDS
        assert "python" in BLOCKED_COMMANDS

    def test_run_allowed_command(self):
        """Test running an allowed command."""
        result = run_command("echo hello")
        assert "hello" in result

    def test_run_blocked_command(self):
        """Test that blocked commands are rejected."""
        result = run_command("rm -rf /")
        assert "Error" in result
        assert "blocked" in result.lower()

    def test_run_unknown_command(self):
        """Test that unknown commands are rejected (allow-list enforcement)."""
        result = run_command("someunknowncommand")
        assert "Error" in result
        assert "not in the allowed list" in result

    def test_shell_metacharacters_blocked(self):
        """Test that shell metacharacters are blocked."""
        result = run_command("echo hello; rm -rf /")
        assert "Error" in result
        assert "metacharacter" in result.lower()

    def test_pipe_blocked(self):
        """Test that pipes are blocked."""
        result = run_command("ls | grep test")
        assert "Error" in result

    def test_shell_interpreter_blocked(self):
        """Test that shell interpreters are blocked."""
        result = run_command("bash -c 'echo hello'")
        assert "Error" in result
        assert "blocked" in result.lower()


