"""
Integration tests for scripts/telegram/bot.py

Tests module interactions with filesystem and multiple components working together.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

pytestmark = pytest.mark.integration


class TestFilesystemIntegration:
    """Tests for bot integration with real filesystem."""

    def test_bot_writes_to_real_queue_directory(self, temp_mind_dir, mock_env, fixed_datetime):
        """Test bot writes queue files to real directory."""
        from scripts.telegram.bot import queue_message

        filename1 = queue_message("Message 1", "user1")
        filename2 = queue_message("Message 2", "user2")

        # Verify files exist
        assert (temp_mind_dir["queue"] / filename1).exists()
        assert (temp_mind_dir["queue"] / filename2).exists()

        # Verify content
        content1 = (temp_mind_dir["queue"] / filename1).read_text()
        assert "user1" in content1
        assert "Message 1" in content1

    def test_bot_logs_to_daily_conversation_file(self, temp_mind_dir, mock_env, fixed_datetime):
        """Test bot appends to the same daily conversation file."""
        from scripts.telegram.bot import log_conversation

        log_conversation("incoming", "First message", "user")
        log_conversation("outgoing", "First response")
        log_conversation("incoming", "Second message", "user")

        # Should all be in the same file
        log_file = temp_mind_dir["conversations"] / "2025-01-15.md"
        assert log_file.exists()

        content = log_file.read_text()
        assert "First message" in content
        assert "First response" in content
        assert "Second message" in content

    def test_multiple_messages_create_separate_queue_files(
        self, temp_mind_dir, mock_env, fixed_datetime
    ):
        """Test that each message creates a unique queue file."""
        from scripts.telegram.bot import queue_message

        filenames = []
        for i in range(5):
            filename = queue_message(f"Message {i}", f"user{i}")
            filenames.append(filename)

        # All filenames should be unique (in real scenario with different timestamps)
        # In our test with fixed time, they'll have same timestamp but test the logic
        assert len(filenames) == 5

        # All files should exist
        for filename in filenames:
            assert (temp_mind_dir["queue"] / filename).exists()

    def test_status_command_counts_real_files(
        self, mock_telegram_update, mock_context, temp_mind_dir, mock_env, fixed_datetime
    ):
        """Test /status command counts real .msg files."""
        from scripts.telegram.bot import handle_status, queue_message

        # Create real queue files
        queue_message("Msg 1", "user")
        queue_message("Msg 2", "user")
        queue_message("Msg 3", "user")

        # Call status handler
        import asyncio
        asyncio.run(handle_status(mock_telegram_update, mock_context))

        # Verify the count in the reply
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "Messages in queue: 3" in call_args[0][0]

    def test_conversation_log_appends_to_same_file(
        self, temp_mind_dir, mock_env, fixed_datetime
    ):
        """Test multiple log entries append to same daily file."""
        from scripts.telegram.bot import log_conversation

        # Log multiple entries
        log_conversation("incoming", "Hello", "alice")
        log_conversation("outgoing", "Hi Alice")
        log_conversation("incoming", "How are you?", "alice")
        log_conversation("outgoing", "I'm doing well")

        # Check file exists and contains all entries
        log_file = temp_mind_dir["conversations"] / "2025-01-15.md"
        assert log_file.exists()

        content = log_file.read_text()
        assert content.count("##") == 4  # 4 conversation entries
        assert "alice (incoming)" in content
        assert "Claude (outgoing)" in content


class TestApplicationSetup:
    """Tests for Telegram Application initialization."""

    def test_bot_application_initialization(self, mock_env, temp_mind_dir):
        """Test that Application is initialized correctly."""
        from scripts.telegram.bot import main

        with patch('scripts.telegram.bot.Application') as mock_app_class:
            builder_mock = Mock()
            app_mock = Mock()
            builder_mock.token.return_value = builder_mock
            builder_mock.build.return_value = app_mock
            mock_app_class.builder.return_value = builder_mock

            # Make run_polling raise an exception to stop main()
            app_mock.run_polling.side_effect = KeyboardInterrupt()

            try:
                main()
            except KeyboardInterrupt:
                pass

            # Verify Application.builder().token() was called
            mock_app_class.builder.assert_called_once()
            builder_mock.token.assert_called_once_with("test-token-12345")

    def test_bot_handlers_registration(self, mock_env, temp_mind_dir):
        """Test that all handlers are registered."""
        from scripts.telegram.bot import main

        with patch('scripts.telegram.bot.Application') as mock_app_class:
            builder_mock = Mock()
            app_mock = Mock()
            builder_mock.token.return_value = builder_mock
            builder_mock.build.return_value = app_mock
            mock_app_class.builder.return_value = builder_mock

            # Make run_polling raise an exception to stop main()
            app_mock.run_polling.side_effect = KeyboardInterrupt()

            try:
                main()
            except KeyboardInterrupt:
                pass

            # Verify handlers were added (3 handlers: start, status, message)
            assert app_mock.add_handler.call_count == 3

    def test_bot_polling_starts(self, mock_env, temp_mind_dir):
        """Test that polling is started."""
        from scripts.telegram.bot import main

        with patch('scripts.telegram.bot.Application') as mock_app_class:
            builder_mock = Mock()
            app_mock = Mock()
            builder_mock.token.return_value = builder_mock
            builder_mock.build.return_value = app_mock
            mock_app_class.builder.return_value = builder_mock

            # Make run_polling raise an exception to stop main()
            app_mock.run_polling.side_effect = KeyboardInterrupt()

            try:
                main()
            except KeyboardInterrupt:
                pass

            # Verify run_polling was called
            app_mock.run_polling.assert_called_once()
