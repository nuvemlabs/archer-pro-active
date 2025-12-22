"""
Unit tests for scripts/telegram/bot.py

Tests individual functions in isolation with all external dependencies mocked.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit


class TestAuthorization:
    """Tests for authorization logic."""

    def test_is_authorized_with_chat_id_set(self, mock_env):
        """Test authorization succeeds with correct chat ID."""
        from scripts.telegram.bot import is_authorized

        result = is_authorized(12345)

        assert result is True

    def test_is_authorized_with_wrong_chat_id(self, mock_env):
        """Test authorization fails with wrong chat ID."""
        from scripts.telegram.bot import is_authorized

        result = is_authorized(99999)

        assert result is False

    def test_is_authorized_with_no_chat_id_set(self, mock_env_no_chat_id):
        """Test authorization accepts all when TELEGRAM_CHAT_ID not set."""
        from scripts.telegram.bot import is_authorized

        result = is_authorized(99999)

        assert result is True


class TestMessageQueuing:
    """Tests for message queue operations."""

    def test_queue_message_creates_file(self, temp_mind_dir, fixed_datetime):
        """Test that queue_message creates a .msg file."""
        from scripts.telegram.bot import queue_message

        filename = queue_message("Hello Claude", "testuser")

        # Check filename pattern (date-time format)
        assert filename.startswith("20250115-")
        assert filename.endswith(".msg")
        queue_file = temp_mind_dir["queue"] / filename
        assert queue_file.exists()

    def test_queue_message_correct_format(self, temp_mind_dir, fixed_datetime):
        """Test that queued message has correct format."""
        from scripts.telegram.bot import queue_message

        filename = queue_message("Test message", "alice")

        content = (temp_mind_dir["queue"] / filename).read_text()
        assert "From: alice" in content
        assert "Time: 2025-01-15T12:30:" in content  # Check date/time prefix
        assert "Test message" in content


class TestConversationLogging:
    """Tests for conversation logging."""

    def test_log_conversation_incoming_format(self, temp_mind_dir, fixed_datetime):
        """Test incoming message logging format."""
        from scripts.telegram.bot import log_conversation

        log_conversation("incoming", "Hello", "bob")

        log_file = temp_mind_dir["conversations"] / "2025-01-15.md"
        content = log_file.read_text()
        assert "## 12:30:" in content  # Check time prefix
        assert "- bob (incoming)" in content
        assert "Hello" in content

    def test_log_conversation_outgoing_format(self, temp_mind_dir, fixed_datetime):
        """Test outgoing message logging format."""
        from scripts.telegram.bot import log_conversation

        log_conversation("outgoing", "Hi there")

        log_file = temp_mind_dir["conversations"] / "2025-01-15.md"
        content = log_file.read_text()
        assert "## 12:30:" in content  # Check time prefix
        assert "- Claude (outgoing)" in content
        assert "Hi there" in content


class TestDirectorySetup:
    """Tests for directory creation."""

    def test_ensure_directories_creates_message_queue(self, temp_mind_dir, monkeypatch):
        """Test that ensure_directories creates message_queue dir."""
        from scripts.telegram.bot import ensure_directories

        # Remove the directory to test creation
        import shutil
        shutil.rmtree(temp_mind_dir["queue"])

        ensure_directories()

        assert temp_mind_dir["queue"].exists()

    def test_ensure_directories_creates_conversations(self, temp_mind_dir, monkeypatch):
        """Test that ensure_directories creates conversations dir."""
        from scripts.telegram.bot import ensure_directories

        # Remove the directory to test creation
        import shutil
        shutil.rmtree(temp_mind_dir["conversations"])

        ensure_directories()

        assert temp_mind_dir["conversations"].exists()

    def test_ensure_directories_idempotent(self, temp_mind_dir):
        """Test that ensure_directories can be called multiple times safely."""
        from scripts.telegram.bot import ensure_directories

        # Call multiple times
        ensure_directories()
        ensure_directories()
        ensure_directories()

        # Should not raise errors and dirs should still exist
        assert temp_mind_dir["queue"].exists()
        assert temp_mind_dir["conversations"].exists()


class TestAsyncHandlers:
    """Tests for async Telegram message handlers."""

    @pytest.mark.asyncio
    async def test_handle_message_authorized_user(
        self, mock_telegram_update, mock_context, temp_mind_dir, mock_env
    ):
        """Test handling message from authorized user."""
        from scripts.telegram.bot import handle_message

        await handle_message(mock_telegram_update, mock_context)

        # Verify message was queued
        queue_files = list(temp_mind_dir["queue"].glob("*.msg"))
        assert len(queue_files) == 1

        # Verify message content
        content = queue_files[0].read_text()
        assert "From: testuser" in content
        assert "Hello Claude" in content

    @pytest.mark.asyncio
    async def test_handle_message_unauthorized_user(
        self, mock_telegram_update_unauthorized, mock_context, temp_mind_dir, mock_env
    ):
        """Test handling message from unauthorized user."""
        from scripts.telegram.bot import handle_message

        await handle_message(mock_telegram_update_unauthorized, mock_context)

        # Verify no message was queued
        queue_files = list(temp_mind_dir["queue"].glob("*.msg"))
        assert len(queue_files) == 0

        # Verify rejection was sent
        mock_telegram_update_unauthorized.message.reply_text.assert_called_once()
        call_args = mock_telegram_update_unauthorized.message.reply_text.call_args
        assert "Unauthorized" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_message_logs_conversation(
        self, mock_telegram_update, mock_context, temp_mind_dir, mock_env, fixed_datetime
    ):
        """Test that handle_message logs to conversation file."""
        from scripts.telegram.bot import handle_message

        await handle_message(mock_telegram_update, mock_context)

        # Verify conversation was logged
        log_file = temp_mind_dir["conversations"] / "2025-01-15.md"
        assert log_file.exists()
        content = log_file.read_text()
        assert "testuser (incoming)" in content
        assert "Hello Claude" in content

    @pytest.mark.asyncio
    async def test_handle_start_authorized(
        self, mock_telegram_update, mock_context, mock_env
    ):
        """Test /start command for authorized user."""
        from scripts.telegram.bot import handle_start

        await handle_start(mock_telegram_update, mock_context)

        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "Connected to Claude" in call_args[0][0]
        assert "12345" in call_args[0][0]  # Chat ID shown

    @pytest.mark.asyncio
    async def test_handle_start_unauthorized(
        self, mock_telegram_update_unauthorized, mock_context, mock_env
    ):
        """Test /start command for unauthorized user."""
        from scripts.telegram.bot import handle_start

        await handle_start(mock_telegram_update_unauthorized, mock_context)

        mock_telegram_update_unauthorized.message.reply_text.assert_called_once()
        call_args = mock_telegram_update_unauthorized.message.reply_text.call_args
        assert "Unauthorized" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_status_shows_queue_count(
        self, mock_telegram_update, mock_context, temp_mind_dir, mock_env, fixed_datetime
    ):
        """Test /status command shows correct queue count."""
        from scripts.telegram.bot import handle_status, queue_message

        # Queue 3 messages
        queue_message("Msg 1", "user")
        queue_message("Msg 2", "user")
        queue_message("Msg 3", "user")

        await handle_status(mock_telegram_update, mock_context)

        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "Messages in queue: 3" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_status_shows_conversation_size(
        self, mock_telegram_update, mock_context, temp_mind_dir, mock_env, fixed_datetime
    ):
        """Test /status command shows conversation log size."""
        from scripts.telegram.bot import handle_status, log_conversation

        # Create some conversation log entries
        log_conversation("incoming", "Test message 1", "user")
        log_conversation("outgoing", "Response 1")

        await handle_status(mock_telegram_update, mock_context)

        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "conversation log:" in call_args[0][0]
        assert "bytes" in call_args[0][0]


class TestMainFunction:
    """Tests for main() function and application setup."""

    def test_main_missing_bot_token_exits(self, monkeypatch, temp_mind_dir):
        """Test that main() exits if TELEGRAM_BOT_TOKEN not set."""
        from scripts.telegram.bot import main

        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    def test_main_creates_directories(self, mock_env, temp_mind_dir):
        """Test that main() creates required directories."""
        from scripts.telegram.bot import main

        # Remove directories
        import shutil
        shutil.rmtree(temp_mind_dir["queue"])
        shutil.rmtree(temp_mind_dir["conversations"])

        # Mock Application to prevent actual bot startup
        with patch('scripts.telegram.bot.Application') as mock_app:
            builder_mock = Mock()
            app_mock = Mock()
            builder_mock.token.return_value = builder_mock
            builder_mock.build.return_value = app_mock
            mock_app.builder.return_value = builder_mock

            # Make run_polling raise an exception to stop main()
            app_mock.run_polling.side_effect = KeyboardInterrupt()

            try:
                main()
            except KeyboardInterrupt:
                pass

        # Directories should have been created before bot startup
        assert temp_mind_dir["queue"].exists()
        assert temp_mind_dir["conversations"].exists()
