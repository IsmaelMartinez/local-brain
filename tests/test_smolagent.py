"""Tests for the smolagent module."""

from unittest.mock import MagicMock, patch

from local_brain.security import set_project_root
from local_brain.smolagent import (
    create_agent,
    file_info,
    git_log,
    git_status,
    list_directory,
    list_definitions,
    read_file,
    run_smolagent,
    search_code,
)


class TestSmolagentTools:
    """Tests for smolagent tools."""

    def test_read_file_success(self, tmp_path):
        """Test reading an existing file within project root."""
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


class TestSmolagentGitTools:
    """Tests for smolagent git tools."""

    def test_git_status(self):
        """Test git status returns something."""
        result = git_status()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_git_log(self):
        """Test git log returns something."""
        result = git_log(count=5)
        assert isinstance(result, str)
        assert len(result) > 0


class TestSmolagentAgent:
    """Tests for the smolagent CodeAgent."""

    @patch("local_brain.smolagent.LiteLLMModel")
    @patch("local_brain.smolagent.CodeAgent")
    def test_create_agent(self, mock_agent_class, mock_model):
        """Test agent creation."""
        mock_model_instance = MagicMock()
        mock_model.return_value = mock_model_instance

        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        agent = create_agent("qwen3:latest", verbose=True)

        mock_model.assert_called_once()
        mock_agent_class.assert_called_once()
        assert agent == mock_agent_instance

    @patch("local_brain.smolagent.create_agent")
    def test_run_smolagent(self, mock_create_agent):
        """Test running the smolagent."""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "Test response"
        mock_create_agent.return_value = mock_agent

        result = run_smolagent("Hello", model="qwen3:latest", verbose=False)

        assert result == "Test response"
        mock_agent.run.assert_called_once_with("Hello")

    @patch("local_brain.smolagent.create_agent")
    def test_run_smolagent_handles_error(self, mock_create_agent):
        """Test smolagent handles errors gracefully."""
        mock_create_agent.side_effect = Exception("Connection refused")

        result = run_smolagent("Hello")

        assert "Error" in result
        assert "Connection refused" in result


class TestSearchCodeTool:
    """Tests for the search_code AST-aware search tool."""

    SAMPLE_PYTHON_CODE = '''"""Sample module for testing."""

class UserService:
    """Service for managing users."""
    
    def __init__(self, db):
        self.db = db
        self.cache = {}
    
    def get_user(self, user_id: int) -> dict:
        """Get user by ID."""
        if user_id in self.cache:
            return self.cache[user_id]
        return self.db.query(user_id)
    
    def create_user(self, name: str, email: str) -> int:
        """Create a new user."""
        user_id = self.db.insert({"name": name, "email": email})
        return user_id


def validate_email(email: str) -> bool:
    """Check if email is valid."""
    return "@" in email and "." in email
'''

    def test_search_code_finds_pattern(self, tmp_path):
        """Test that search_code finds patterns in files."""
        set_project_root(tmp_path)

        test_file = tmp_path / "test_service.py"
        test_file.write_text(self.SAMPLE_PYTHON_CODE)

        result = search_code("user_id", str(test_file))
        assert "user_id" in result
        # Should include context (AST-aware)
        assert "def " in result or "class " in result

    def test_search_code_case_insensitive(self, tmp_path):
        """Test case insensitive search."""
        set_project_root(tmp_path)

        test_file = tmp_path / "test.py"
        test_file.write_text(self.SAMPLE_PYTHON_CODE)

        result = search_code("USERSERVICE", str(test_file), ignore_case=True)
        assert "UserService" in result

    def test_search_code_no_matches(self, tmp_path):
        """Test search_code with no matches."""
        set_project_root(tmp_path)

        test_file = tmp_path / "test.py"
        test_file.write_text(self.SAMPLE_PYTHON_CODE)

        result = search_code("nonexistent_pattern_xyz", str(test_file))
        assert "No matches" in result

    def test_search_code_file_not_found(self, tmp_path):
        """Test search_code with non-existent file."""
        set_project_root(tmp_path)

        result = search_code("pattern", "nonexistent.py")
        assert "Error" in result
        assert "not found" in result

    def test_search_code_outside_root(self, tmp_path):
        """Test search_code blocks files outside project root."""
        set_project_root(tmp_path)

        result = search_code("pattern", "/etc/passwd")
        assert "Error" in result
        assert "outside project root" in result

    def test_search_code_sensitive_file(self, tmp_path):
        """Test search_code blocks sensitive files."""
        set_project_root(tmp_path)

        env_file = tmp_path / ".env"
        env_file.write_text("SECRET=value")

        result = search_code("SECRET", str(env_file))
        assert "Error" in result
        assert "sensitive" in result.lower() or "blocked" in result.lower()

    def test_search_code_unsupported_language(self, tmp_path):
        """Test search_code falls back to simple grep for unsupported languages."""
        set_project_root(tmp_path)

        test_file = tmp_path / "config.unknown"
        test_file.write_text("key=value\nkey2=value2")

        result = search_code("key", str(test_file))
        # Should still find matches via simple grep fallback
        assert "key" in result


class TestListDefinitionsTool:
    """Tests for the list_definitions AST tool."""

    SAMPLE_PYTHON_CODE = '''"""Sample module for testing."""

from typing import Optional

CONSTANT = 42


class UserService:
    """Service for managing users."""
    
    def __init__(self, db):
        self.db = db
    
    def get_user(self, user_id: int) -> dict:
        """Get user by ID."""
        return self.db.query(user_id)
    
    def create_user(self, name: str, email: str) -> int:
        """Create a new user."""
        return self.db.insert({"name": name, "email": email})


def validate_email(email: str) -> bool:
    """Check if email is valid."""
    return "@" in email
'''

    def test_list_definitions_extracts_class(self, tmp_path):
        """Test that list_definitions extracts class definitions."""
        set_project_root(tmp_path)

        test_file = tmp_path / "service.py"
        test_file.write_text(self.SAMPLE_PYTHON_CODE)

        result = list_definitions(str(test_file))
        assert "class UserService:" in result

    def test_list_definitions_extracts_functions(self, tmp_path):
        """Test that list_definitions extracts function definitions."""
        set_project_root(tmp_path)

        test_file = tmp_path / "service.py"
        test_file.write_text(self.SAMPLE_PYTHON_CODE)

        result = list_definitions(str(test_file))
        assert "def validate_email" in result
        assert "def get_user" in result
        assert "def create_user" in result

    def test_list_definitions_includes_docstrings(self, tmp_path):
        """Test that list_definitions includes docstrings."""
        set_project_root(tmp_path)

        test_file = tmp_path / "service.py"
        test_file.write_text(self.SAMPLE_PYTHON_CODE)

        result = list_definitions(str(test_file))
        assert "Service for managing users" in result

    def test_list_definitions_includes_type_hints(self, tmp_path):
        """Test that list_definitions includes type hints."""
        set_project_root(tmp_path)

        test_file = tmp_path / "service.py"
        test_file.write_text(self.SAMPLE_PYTHON_CODE)

        result = list_definitions(str(test_file))
        assert "-> dict" in result or "dict:" in result
        assert "-> bool" in result or "bool:" in result

    def test_list_definitions_file_not_found(self, tmp_path):
        """Test list_definitions with non-existent file."""
        set_project_root(tmp_path)

        result = list_definitions("nonexistent.py")
        assert "Error" in result
        assert "not found" in result

    def test_list_definitions_outside_root(self, tmp_path):
        """Test list_definitions blocks files outside project root."""
        set_project_root(tmp_path)

        result = list_definitions("/etc/passwd")
        assert "Error" in result
        assert "outside project root" in result

    def test_list_definitions_unsupported_language(self, tmp_path):
        """Test list_definitions with unsupported file type."""
        set_project_root(tmp_path)

        test_file = tmp_path / "config.xyz"
        test_file.write_text("some content")

        result = list_definitions(str(test_file))
        assert "Error" in result
        assert "Unsupported" in result

    def test_list_definitions_empty_file(self, tmp_path):
        """Test list_definitions with file containing no definitions."""
        set_project_root(tmp_path)

        test_file = tmp_path / "empty.py"
        test_file.write_text("# Just a comment\nCONSTANT = 42")

        result = list_definitions(str(test_file))
        assert "No definitions found" in result or result.strip() == ""
