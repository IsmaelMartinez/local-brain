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

    @patch("local_brain.cli.run_agent")
    def test_basic_prompt(self, mock_run_agent):
        """Test basic prompt execution."""
        mock_run_agent.return_value = "Test response"

        runner = CliRunner()
        result = runner.invoke(main, ["Hello world"])

        assert result.exit_code == 0
        assert "Test response" in result.output
        mock_run_agent.assert_called_once()

    @patch("local_brain.cli.run_agent")
    def test_model_option(self, mock_run_agent):
        """Test --model option."""
        mock_run_agent.return_value = "Response"

        runner = CliRunner()
        result = runner.invoke(main, ["-m", "llama3.2", "Hello"])

        assert result.exit_code == 0
        # Check that model was passed
        call_kwargs = mock_run_agent.call_args[1]
        assert call_kwargs["model"] == "llama3.2"

    @patch("local_brain.cli.run_agent")
    def test_verbose_option(self, mock_run_agent):
        """Test --verbose option."""
        mock_run_agent.return_value = "Response"

        runner = CliRunner()
        result = runner.invoke(main, ["-v", "Hello"])

        assert result.exit_code == 0
        call_kwargs = mock_run_agent.call_args[1]
        assert call_kwargs["verbose"] is True
