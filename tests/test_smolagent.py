"""Tests for the smolagent module."""

from unittest.mock import MagicMock, patch

from local_brain.security import set_project_root


class TestSmolagentTools:
    """Tests for smolagent tools."""

    def test_read_file_success(self, tmp_path):
        """Test reading an existing file within project root."""
        from local_brain.smolagent import read_file

        set_project_root(tmp_path)

        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")

        result = read_file(str(test_file))
        assert result == "Hello, world!"

    def test_read_file_not_found(self, tmp_path):
        """Test reading a non-existent file within project root."""
        from local_brain.smolagent import read_file

        set_project_root(tmp_path)

        result = read_file("nonexistent_file.txt")
        assert "Error" in result
        assert "not found" in result

    def test_read_file_outside_root(self, tmp_path):
        """Test that reading files outside project root is blocked."""
        from local_brain.smolagent import read_file

        set_project_root(tmp_path)

        result = read_file("/etc/passwd")
        assert "Error" in result
        assert "outside project root" in result

    def test_list_directory_success(self, tmp_path):
        """Test listing a directory within project root."""
        from local_brain.smolagent import list_directory

        set_project_root(tmp_path)

        # Create some files
        (tmp_path / "test1.py").write_text("# test")
        (tmp_path / "test2.py").write_text("# test")

        result = list_directory(str(tmp_path), "*.py")
        assert "test1.py" in result
        assert "test2.py" in result

    def test_list_directory_not_found(self, tmp_path):
        """Test listing a non-existent directory within project root."""
        from local_brain.smolagent import list_directory

        set_project_root(tmp_path)

        result = list_directory("nonexistent_subdir")
        assert "Error" in result

    def test_list_directory_outside_root(self, tmp_path):
        """Test that listing directories outside project root is blocked."""
        from local_brain.smolagent import list_directory

        set_project_root(tmp_path)

        result = list_directory("/etc")
        assert "Error" in result
        assert "outside project root" in result

    def test_file_info_success(self, tmp_path):
        """Test getting file info within project root."""
        from local_brain.smolagent import file_info

        set_project_root(tmp_path)

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = file_info(str(test_file))
        assert "Path:" in result
        assert "Size:" in result
        assert "Modified:" in result

    def test_file_info_not_found(self, tmp_path):
        """Test file info for non-existent file within project root."""
        from local_brain.smolagent import file_info

        set_project_root(tmp_path)

        result = file_info("nonexistent.txt")
        assert "Error" in result

    def test_file_info_outside_root(self, tmp_path):
        """Test that file info outside project root is blocked."""
        from local_brain.smolagent import file_info

        set_project_root(tmp_path)

        result = file_info("/etc/passwd")
        assert "Error" in result
        assert "outside project root" in result


class TestSmolagentGitTools:
    """Tests for smolagent git tools."""

    def test_git_status(self):
        """Test git status returns something."""
        from local_brain.smolagent import git_status

        result = git_status()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_git_log(self):
        """Test git log returns something."""
        from local_brain.smolagent import git_log

        result = git_log(count=5)
        assert isinstance(result, str)
        assert len(result) > 0


class TestSmolagentAgent:
    """Tests for the smolagent CodeAgent."""

    @patch("local_brain.smolagent.LiteLLMModel")
    @patch("local_brain.smolagent.CodeAgent")
    def test_create_agent(self, mock_code_agent, mock_model):
        """Test agent creation."""
        from local_brain.smolagent import create_agent

        mock_model_instance = MagicMock()
        mock_model.return_value = mock_model_instance

        mock_agent_instance = MagicMock()
        mock_code_agent.return_value = mock_agent_instance

        agent = create_agent("qwen3:latest", verbose=True)

        mock_model.assert_called_once()
        mock_code_agent.assert_called_once()
        assert agent == mock_agent_instance

    @patch("local_brain.smolagent.create_agent")
    def test_run_smolagent(self, mock_create_agent):
        """Test running the smolagent."""
        from local_brain.smolagent import run_smolagent

        mock_agent = MagicMock()
        mock_agent.run.return_value = "Test response"
        mock_create_agent.return_value = mock_agent

        result = run_smolagent("Hello", model="qwen3:latest", verbose=False)

        assert result == "Test response"
        mock_agent.run.assert_called_once_with("Hello")

    @patch("local_brain.smolagent.create_agent")
    def test_run_smolagent_handles_error(self, mock_create_agent):
        """Test smolagent handles errors gracefully."""
        from local_brain.smolagent import run_smolagent

        mock_create_agent.side_effect = Exception("Connection refused")

        result = run_smolagent("Hello")

        assert "Error" in result
        assert "Connection refused" in result

