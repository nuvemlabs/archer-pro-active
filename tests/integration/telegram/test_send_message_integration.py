"""
Integration tests for scripts/telegram/send_message.py

Tests CLI integration with filesystem and complete workflows.
"""

import pytest
import sys
from unittest.mock import Mock, patch
from io import StringIO

pytestmark = pytest.mark.integration


class TestCLIIntegration:
    """Tests for CLI functionality with real filesystem."""

    def test_send_via_cli_args(self, mock_env, mock_telegram_bot, temp_mind_dir, monkeypatch, fixed_datetime):
        """Test complete CLI flow with command line arguments."""
        from scripts.telegram.send_message import main

        monkeypatch.setattr(sys, 'argv', ['send-telegram', 'Hello', 'from', 'CLI'])

        with patch('scripts.telegram.send_message.Bot') as mock_bot_class:
            mock_bot_class.return_value = mock_telegram_bot
            with pytest.raises(SystemExit) as exc_info:
                main()

        # Verify success
        assert exc_info.value.code == 0

        # Verify message was sent
        mock_telegram_bot.send_message.assert_called_once_with(
            chat_id="12345",
            text="Hello from CLI"
        )

        # Verify conversation was logged
        log_file = temp_mind_dir["conversations"] / "2025-01-15.md"
        assert log_file.exists()
        content = log_file.read_text()
        assert "Hello from CLI" in content
        assert "Claude (outgoing)" in content

    def test_send_via_stdin_pipe(self, mock_env, mock_telegram_bot, temp_mind_dir, monkeypatch, fixed_datetime):
        """Test complete CLI flow with stdin input."""
        from scripts.telegram.send_message import main

        stdin_content = "Message from stdin pipe"
        monkeypatch.setattr(sys, 'stdin', StringIO(stdin_content))
        monkeypatch.setattr(sys.stdin, 'isatty', lambda: False)
        monkeypatch.setattr(sys, 'argv', ['send-telegram'])

        with patch('scripts.telegram.send_message.Bot') as mock_bot_class:
            mock_bot_class.return_value = mock_telegram_bot
            with pytest.raises(SystemExit) as exc_info:
                main()

        # Verify success
        assert exc_info.value.code == 0

        # Verify message was sent
        assert mock_telegram_bot.send_message.called
        call_args = mock_telegram_bot.send_message.call_args
        assert call_args[1]['text'] == stdin_content

        # Verify conversation was logged
        log_file = temp_mind_dir["conversations"] / "2025-01-15.md"
        assert log_file.exists()
        content = log_file.read_text()
        assert stdin_content in content

    def test_sends_and_logs_to_filesystem(
        self, mock_env, mock_telegram_bot, temp_mind_dir, monkeypatch, fixed_datetime
    ):
        """Test that both sending AND logging happen together."""
        from scripts.telegram.send_message import main

        monkeypatch.setattr(sys, 'argv', ['send-telegram', 'Integration test message'])

        with patch('scripts.telegram.send_message.Bot') as mock_bot_class:
            mock_bot_class.return_value = mock_telegram_bot
            with pytest.raises(SystemExit):
                main()

        # Verify Telegram API was called
        assert mock_telegram_bot.send_message.called

        # Verify filesystem logging occurred
        log_file = temp_mind_dir["conversations"] / "2025-01-15.md"
        assert log_file.exists()

        # Verify content matches
        content = log_file.read_text()
        assert "Integration test message" in content
        assert "12:30:" in content  # timestamp prefix from fixed_datetime
        assert "Claude (outgoing)" in content

    def test_multiple_sends_append_to_log(
        self, mock_env, mock_telegram_bot, temp_mind_dir, monkeypatch, fixed_datetime
    ):
        """Test that multiple CLI invocations append to the same log."""
        from scripts.telegram.send_message import main

        # Send first message
        monkeypatch.setattr(sys, 'argv', ['send-telegram', 'First message'])
        with patch('scripts.telegram.send_message.Bot') as mock_bot_class:
            mock_bot_class.return_value = mock_telegram_bot
            with pytest.raises(SystemExit):
                main()

        # Send second message
        monkeypatch.setattr(sys, 'argv', ['send-telegram', 'Second message'])
        with patch('scripts.telegram.send_message.Bot') as mock_bot_class:
            mock_bot_class.return_value = mock_telegram_bot
            with pytest.raises(SystemExit):
                main()

        # Verify both in same log file
        log_file = temp_mind_dir["conversations"] / "2025-01-15.md"
        content = log_file.read_text()
        assert "First message" in content
        assert "Second message" in content
        assert content.count("Claude (outgoing)") == 2
