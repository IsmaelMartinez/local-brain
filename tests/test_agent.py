"""Tests for the agent module with mocked Ollama."""

from unittest.mock import MagicMock, patch


class TestAgent:
    """Tests for the agent module."""

    @patch("local_brain.agent.ollama")
    def test_run_agent_simple_response(self, mock_ollama):
        """Test agent with a simple response (no tool calls)."""
        from local_brain.agent import run_agent
        from local_brain.tools import ALL_TOOLS

        # Mock response with no tool calls
        mock_response = MagicMock()
        mock_response.message.content = "Hello! How can I help you?"
        mock_response.message.tool_calls = None
        mock_ollama.chat.return_value = mock_response

        result = run_agent(
            prompt="Hi",
            system="You are helpful.",
            model="test-model",
            tools=ALL_TOOLS,
        )

        assert result == "Hello! How can I help you?"
        mock_ollama.chat.assert_called_once()

    @patch("local_brain.agent.ollama")
    def test_run_agent_with_tool_call(self, mock_ollama):
        """Test agent with a tool call."""
        from local_brain.agent import run_agent
        from local_brain.tools import ALL_TOOLS

        # First response: tool call
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "git_status"
        mock_tool_call.function.arguments = {}

        mock_response1 = MagicMock()
        mock_response1.message.content = ""
        mock_response1.message.tool_calls = [mock_tool_call]

        # Second response: final answer
        mock_response2 = MagicMock()
        mock_response2.message.content = "The repo is clean."
        mock_response2.message.tool_calls = None

        mock_ollama.chat.side_effect = [mock_response1, mock_response2]

        result = run_agent(
            prompt="What's the git status?",
            system="You are helpful.",
            model="test-model",
            tools=ALL_TOOLS,
        )

        assert result == "The repo is clean."
        assert mock_ollama.chat.call_count == 2

    @patch("local_brain.agent.ollama")
    def test_run_agent_max_turns(self, mock_ollama):
        """Test agent respects max_turns limit."""
        from local_brain.agent import run_agent
        from local_brain.tools import ALL_TOOLS

        # Always return tool calls to trigger max turns
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "git_status"
        mock_tool_call.function.arguments = {}

        mock_response = MagicMock()
        mock_response.message.content = ""
        mock_response.message.tool_calls = [mock_tool_call]
        mock_ollama.chat.return_value = mock_response

        run_agent(
            prompt="Loop forever",
            system="You are helpful.",
            model="test-model",
            tools=ALL_TOOLS,
            max_turns=3,
        )

        # Should stop at max_turns
        assert mock_ollama.chat.call_count == 3

    @patch("local_brain.agent.ollama")
    def test_run_agent_handles_error(self, mock_ollama):
        """Test agent handles Ollama errors gracefully."""
        from local_brain.agent import run_agent
        from local_brain.tools import ALL_TOOLS

        mock_ollama.chat.side_effect = Exception("Connection refused")

        result = run_agent(
            prompt="Hi",
            system="You are helpful.",
            model="test-model",
            tools=ALL_TOOLS,
        )

        assert "Error" in result
        assert "Connection refused" in result

    @patch("local_brain.agent.ollama")
    def test_run_agent_unknown_tool(self, mock_ollama):
        """Test agent handles unknown tool calls."""
        from local_brain.agent import run_agent
        from local_brain.tools import ALL_TOOLS

        # Response with unknown tool
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "unknown_tool"
        mock_tool_call.function.arguments = {}

        mock_response1 = MagicMock()
        mock_response1.message.content = ""
        mock_response1.message.tool_calls = [mock_tool_call]

        mock_response2 = MagicMock()
        mock_response2.message.content = "I couldn't find that tool."
        mock_response2.message.tool_calls = None

        mock_ollama.chat.side_effect = [mock_response1, mock_response2]

        run_agent(
            prompt="Use unknown tool",
            system="You are helpful.",
            model="test-model",
            tools=ALL_TOOLS,
        )

        # Should handle gracefully
        assert mock_ollama.chat.call_count == 2
