"""
Unit tests for scripts/telegram/send_message.py

Tests CLI utility for sending Telegram messages.
"""

import pytest
import sys
from unittest.mock import Mock, patch
from io import StringIO

pytestmark = pytest.mark.unit


class TestLogOutgoing:
    """Tests for log_outgoing() function."""

    def test_log_outgoing_creates_file(self, temp_mind_dir, fixed_datetime):
        """Test that log_outgoing creates conversation file."""
        from scripts.telegram.send_message import log_outgoing

        log_outgoing("Test message")

        log_file = temp_mind_dir["conversations"] / "2025-01-15.md"
        assert log_file.exists()

    def test_log_outgoing_correct_format(self, temp_mind_dir, fixed_datetime):
        """Test log entry format."""
        from scripts.telegram.send_message import log_outgoing

        log_outgoing("Hello from Claude")

        content = (temp_mind_dir["conversations"] / "2025-01-15.md").read_text()
        assert "## 12:30:" in content  # Check time prefix
        assert "- Claude (outgoing)" in content
        assert "Hello from Claude" in content


class TestSendMessage:
    """Tests for send_message() async function."""

    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_env, mock_telegram_bot, temp_mind_dir):
        """Test successful message sending."""
        from scripts.telegram.send_message import send_message

        with patch('scripts.telegram.send_message.Bot') as mock_bot_class:
            mock_bot_class.return_value = mock_telegram_bot
            result = await send_message("Test")

        assert result is True
        mock_telegram_bot.send_message.assert_called_once_with(
            chat_id="12345",
            text="Test"
        )

    @pytest.mark.asyncio
    async def test_send_message_missing_token(self, monkeypatch):
        """Test failure when BOT_TOKEN missing."""
        from scripts.telegram.send_message import send_message

        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

        result = await send_message("Test")

        assert result is False

    @pytest.mark.asyncio
    async def test_send_message_missing_chat_id(self, monkeypatch):
        """Test failure when CHAT_ID missing."""
        from scripts.telegram.send_message import send_message

        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

        result = await send_message("Test")

        assert result is False

    @pytest.mark.asyncio
    async def test_send_message_telegram_api_error(self, mock_env, mock_telegram_bot):
        """Test handling of Telegram API errors."""
        from scripts.telegram.send_message import send_message

        mock_telegram_bot.send_message.side_effect = Exception("Network error")

        with patch('scripts.telegram.send_message.Bot', return_value=mock_telegram_bot):
            result = await send_message("Test")

        assert result is False


class TestMainFunction:
    """Tests for main() CLI function."""

    def test_main_argv_input(self, mock_env, mock_telegram_bot, temp_mind_dir, monkeypatch):
        """Test reading message from command line arguments."""
        from scripts.telegram.send_message import main

        monkeypatch.setattr(sys, 'argv', ['send-telegram', 'Hello', 'world'])

        with patch('scripts.telegram.send_message.Bot') as mock_bot_class:
            mock_bot_class.return_value = mock_telegram_bot
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        mock_telegram_bot.send_message.assert_called_once()

    def test_main_stdin_input(self, mock_env, mock_telegram_bot, temp_mind_dir, monkeypatch):
        """Test reading message from stdin."""
        from scripts.telegram.send_message import main

        monkeypatch.setattr(sys, 'stdin', StringIO("Hello from stdin"))
        monkeypatch.setattr(sys.stdin, 'isatty', lambda: False)
        monkeypatch.setattr(sys, 'argv', ['send-telegram'])

        with patch('scripts.telegram.send_message.Bot') as mock_bot_class:
            mock_bot_class.return_value = mock_telegram_bot
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        # Verify message was sent
        assert mock_telegram_bot.send_message.called

    def test_main_no_input_exits_with_error(self, monkeypatch):
        """Test that main() exits with error when no input provided."""
        from scripts.telegram.send_message import main

        monkeypatch.setattr(sys, 'argv', ['send-telegram'])
        monkeypatch.setattr(sys.stdin, 'isatty', lambda: True)

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    def test_main_empty_message_exits_with_error(self, mock_env, monkeypatch):
        """Test that main() exits with error for empty message."""
        from scripts.telegram.send_message import main

        monkeypatch.setattr(sys, 'argv', ['send-telegram', ''])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    def test_main_success_exits_zero(self, mock_env, mock_telegram_bot, temp_mind_dir, monkeypatch):
        """Test that main() exits with 0 on success."""
        from scripts.telegram.send_message import main

        monkeypatch.setattr(sys, 'argv', ['send-telegram', 'Success test'])

        with patch('scripts.telegram.send_message.Bot') as mock_bot_class:
            mock_bot_class.return_value = mock_telegram_bot
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0

    def test_main_failure_exits_one(self, mock_env, mock_telegram_bot, temp_mind_dir, monkeypatch):
        """Test that main() exits with 1 on failure."""
        from scripts.telegram.send_message import main

        # Make send_message fail
        mock_telegram_bot.send_message.side_effect = Exception("Network error")

        monkeypatch.setattr(sys, 'argv', ['send-telegram', 'Failure test'])

        with patch('scripts.telegram.send_message.Bot') as mock_bot_class:
            mock_bot_class.return_value = mock_telegram_bot
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1
