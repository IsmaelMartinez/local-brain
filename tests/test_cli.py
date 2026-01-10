"""Tests for the CLI module."""

from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from local_brain.cli import main, doctor
from local_brain import __version__
from local_brain.models import DEFAULT_MODEL


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
    @patch("local_brain.cli.run_smolagent")
    def test_basic_prompt(self, mock_run_smolagent, mock_check_model):
        """Test basic prompt execution."""
        mock_run_smolagent.return_value = "Test response"
        mock_check_model.return_value = True

        runner = CliRunner()
        result = runner.invoke(main, ["Hello world"])

        assert result.exit_code == 0
        assert "Test response" in result.output
        mock_run_smolagent.assert_called_once()

    @patch("local_brain.cli.check_model_available")
    @patch("local_brain.cli.run_smolagent")
    def test_model_option(self, mock_run_smolagent, mock_check_model):
        """Test --model option with a compatible installed model."""
        mock_run_smolagent.return_value = "Response"
        mock_check_model.return_value = True

        runner = CliRunner()
        result = runner.invoke(main, ["-m", "qwen3:latest", "Hello"])

        assert result.exit_code == 0
        # Check that model was passed
        call_kwargs = mock_run_smolagent.call_args[1]
        assert call_kwargs["model"] == "qwen3:latest"

    @patch("local_brain.cli.check_model_available")
    @patch("local_brain.cli.run_smolagent")
    def test_incompatible_model_fallback(self, mock_run_smolagent, mock_check_model):
        """Test that incompatible models automatically fallback to compatible ones."""
        mock_run_smolagent.return_value = "Response"
        mock_check_model.return_value = True

        runner = CliRunner()
        # llama3.2:1b is incompatible, should fallback to DEFAULT_MODEL
        result = runner.invoke(main, ["-m", "llama3.2:1b", "Hello"])

        assert result.exit_code == 0
        # Should show warning about incompatible model
        assert "incompatible" in result.output.lower()
        # Should have used fallback model
        call_kwargs = mock_run_smolagent.call_args[1]
        assert call_kwargs["model"] == DEFAULT_MODEL

    @patch("local_brain.cli.check_model_available")
    @patch("local_brain.cli.run_smolagent")
    def test_verbose_option(self, mock_run_smolagent, mock_check_model):
        """Test --verbose option."""
        mock_run_smolagent.return_value = "Response"
        mock_check_model.return_value = True

        runner = CliRunner()
        result = runner.invoke(main, ["-v", "Hello"])

        assert result.exit_code == 0
        call_kwargs = mock_run_smolagent.call_args[1]
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

    @patch("local_brain.tracing.setup_tracing")
    @patch("local_brain.cli.check_model_available")
    @patch("local_brain.cli.run_smolagent")
    def test_trace_flag_enables_tracing(
        self, mock_run_smolagent, mock_check_model, mock_setup_tracing
    ):
        """Test --trace flag enables OTEL tracing."""
        mock_run_smolagent.return_value = "Response"
        mock_check_model.return_value = True
        mock_setup_tracing.return_value = True

        runner = CliRunner()
        result = runner.invoke(main, ["--trace", "Hello"])

        assert result.exit_code == 0
        mock_setup_tracing.assert_called_once()

    @patch("local_brain.tracing.setup_tracing")
    @patch("local_brain.cli.check_model_available")
    @patch("local_brain.cli.run_smolagent")
    def test_trace_flag_shows_warning_on_failure(
        self, mock_run_smolagent, mock_check_model, mock_setup_tracing
    ):
        """Test --trace shows warning when tracing setup fails."""
        mock_run_smolagent.return_value = "Response"
        mock_check_model.return_value = True
        mock_setup_tracing.return_value = False  # Tracing unavailable

        runner = CliRunner()
        result = runner.invoke(main, ["--trace", "Hello"])

        assert result.exit_code == 0
        assert "Tracing unavailable" in result.output


class TestDoctorCommand:
    """Tests for the doctor subcommand."""

    def test_doctor_help(self):
        """Test doctor --help shows command info."""
        runner = CliRunner()
        result = runner.invoke(doctor, ["--help"])

        assert result.exit_code == 0
        assert "Check system health" in result.output

    @patch("local_brain.cli.list_installed_models")
    @patch("local_brain.cli.subprocess.run")
    def test_doctor_all_checks_pass(self, mock_subprocess, mock_list_models):
        """Test doctor command when all checks pass."""
        # Mock ollama --version
        mock_subprocess.return_value = MagicMock(
            returncode=0, stdout="ollama version 0.4.1", stderr=""
        )

        # Mock installed models
        mock_model = MagicMock()
        mock_model.model = "qwen3:latest"
        mock_list_models.return_value = [mock_model]

        runner = CliRunner()
        result = runner.invoke(doctor)

        assert "Health Check" in result.output
        assert "Ollama" in result.output

    @patch("local_brain.cli.subprocess.run")
    def test_doctor_ollama_not_installed(self, mock_subprocess):
        """Test doctor when ollama is not installed."""
        mock_subprocess.side_effect = FileNotFoundError()

        runner = CliRunner()
        result = runner.invoke(doctor)

        assert "Ollama is not installed" in result.output

    @patch("local_brain.cli.list_installed_models")
    @patch("local_brain.cli.subprocess.run")
    def test_doctor_no_models(self, mock_subprocess, mock_list_models):
        """Test doctor when no models are installed."""
        mock_subprocess.return_value = MagicMock(
            returncode=0, stdout="ollama version 0.4.1", stderr=""
        )
        mock_list_models.return_value = []

        runner = CliRunner()
        result = runner.invoke(doctor)

        assert "No recommended models" in result.output or "0 models" in result.output
