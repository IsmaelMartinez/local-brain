"""Tests for the CLI module."""

from unittest.mock import patch

from click.testing import CliRunner

from local_brain.cli import main
from local_brain import __version__


class TestCLI:
    """Tests for the CLI."""

    def test_version_flag(self):
        """Test --version flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_help_flag(self):
        """Test --help flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Chat with local Ollama models" in result.output

    @patch("local_brain.cli.check_model_available")
    @patch("local_brain.cli.run_agent")
    def test_basic_prompt(self, mock_run_agent, mock_check_model):
        """Test basic prompt execution."""
        mock_run_agent.return_value = "Test response"
        mock_check_model.return_value = True

        runner = CliRunner()
        result = runner.invoke(main, ["Hello world"])

        assert result.exit_code == 0
        assert "Test response" in result.output
        mock_run_agent.assert_called_once()

    @patch("local_brain.cli.check_model_available")
    @patch("local_brain.cli.run_agent")
    def test_model_option(self, mock_run_agent, mock_check_model):
        """Test --model option with an installed model."""
        mock_run_agent.return_value = "Response"
        mock_check_model.return_value = True

        runner = CliRunner()
        result = runner.invoke(main, ["-m", "llama3.2:1b", "Hello"])

        assert result.exit_code == 0
        # Check that model was passed
        call_kwargs = mock_run_agent.call_args[1]
        assert call_kwargs["model"] == "llama3.2:1b"

    @patch("local_brain.cli.check_model_available")
    @patch("local_brain.cli.run_agent")
    def test_verbose_option(self, mock_run_agent, mock_check_model):
        """Test --verbose option."""
        mock_run_agent.return_value = "Response"
        mock_check_model.return_value = True

        runner = CliRunner()
        result = runner.invoke(main, ["-v", "Hello"])

        assert result.exit_code == 0
        call_kwargs = mock_run_agent.call_args[1]
        assert call_kwargs["verbose"] is True

    @patch("local_brain.cli.get_available_models_summary")
    def test_list_models_flag(self, mock_summary):
        """Test --list-models flag."""
        mock_summary.return_value = "Installed models:\n  ✅ qwen3:latest"

        runner = CliRunner()
        result = runner.invoke(main, ["--list-models"])

        assert result.exit_code == 0
        assert "Installed models" in result.output
        mock_summary.assert_called_once()

    @patch("local_brain.cli.check_model_available")
    def test_model_not_available(self, mock_check_model):
        """Test error when model is not available."""
        mock_check_model.return_value = False

        runner = CliRunner()
        result = runner.invoke(main, ["-m", "nonexistent:model", "Hello"])

        assert result.exit_code == 1
        assert "not installed" in result.output
