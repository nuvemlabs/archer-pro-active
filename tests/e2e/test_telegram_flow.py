"""
End-to-end tests for complete Telegram bot workflows.

Tests complete user journeys from message receipt to response.
"""

import pytest
import sys
from unittest.mock import Mock, patch
from pathlib import Path

pytestmark = pytest.mark.e2e


class TestCompleteFlows:
    """Tests for complete end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_receive_message_queue_and_respond(
        self, mock_telegram_update, mock_context, mock_telegram_bot,
        temp_mind_dir, mock_env, fixed_datetime
    ):
        """Test complete cycle: receive message → queue → send response."""
        from scripts.telegram.bot import handle_message
        from scripts.telegram.send_message import send_message

        # Step 1: Receive incoming message
        await handle_message(mock_telegram_update, mock_context)

        # Verify message was queued
        queue_files = list(temp_mind_dir["queue"].glob("*.msg"))
        assert len(queue_files) == 1

        # Verify incoming message logged
        log_file = temp_mind_dir["conversations"] / "2025-01-15.md"
        content = log_file.read_text()
        assert "testuser (incoming)" in content
        assert "Hello Claude" in content

        # Step 2: Send response (simulating Claude's reply)
        with patch('scripts.telegram.send_message.Bot') as mock_bot_class:
            mock_bot_class.return_value = mock_telegram_bot
            result = await send_message("Thanks for your message!")

        assert result is True

        # Verify response was sent via Telegram
        mock_telegram_bot.send_message.assert_called_once_with(
            chat_id="12345",
            text="Thanks for your message!"
        )

        # Verify outgoing message logged
        content = log_file.read_text()
        assert "Claude (outgoing)" in content
        assert "Thanks for your message!" in content

        # Verify both incoming and outgoing in same conversation log
        assert content.count("##") == 2  # Two conversation entries

    @pytest.mark.asyncio
    async def test_unauthorized_user_rejected(
        self, mock_telegram_update_unauthorized, mock_context,
        temp_mind_dir, mock_env
    ):
        """Test complete flow for unauthorized user."""
        from scripts.telegram.bot import handle_message

        # Attempt to send message as unauthorized user
        await handle_message(mock_telegram_update_unauthorized, mock_context)

        # Verify message was NOT queued
        queue_files = list(temp_mind_dir["queue"].glob("*.msg"))
        assert len(queue_files) == 0

        # Verify rejection message was sent
        mock_telegram_update_unauthorized.message.reply_text.assert_called_once()
        call_args = mock_telegram_update_unauthorized.message.reply_text.call_args
        assert "Unauthorized" in call_args[0][0]

        # Verify no conversation log was created (or it doesn't contain the message)
        log_file = temp_mind_dir["conversations"] / "2025-01-15.md"
        if log_file.exists():
            content = log_file.read_text()
            assert "Unauthorized access" not in content

    @pytest.mark.asyncio
    async def test_status_command_reflects_queue_state(
        self, mock_telegram_update, mock_context,
        temp_mind_dir, mock_env, fixed_datetime
    ):
        """Test /status command reflects actual queue state."""
        from scripts.telegram.bot import handle_message, handle_status

        # Start with empty queue
        await handle_status(mock_telegram_update, mock_context)
        call_args = mock_telegram_update.message.reply_text.call_args
        assert "Messages in queue: 0" in call_args[0][0]

        # Add messages
        await handle_message(mock_telegram_update, mock_context)
        mock_telegram_update.message.text = "Second message"
        await handle_message(mock_telegram_update, mock_context)
        mock_telegram_update.message.text = "Third message"
        await handle_message(mock_telegram_update, mock_context)

        # Check status again - should have 3 messages
        await handle_status(mock_telegram_update, mock_context)
        call_args = mock_telegram_update.message.reply_text.call_args
        # Verify at least 3 messages (counter creates unique timestamps)
        assert "Messages in queue:" in call_args[0][0]
        queue_count = len(list(temp_mind_dir["queue"].glob("*.msg")))
        assert queue_count == 3

    @pytest.mark.asyncio
    async def test_message_flow_logs_conversation(
        self, mock_telegram_update, mock_context, mock_telegram_bot,
        temp_mind_dir, mock_env, fixed_datetime
    ):
        """Test that complete message flow creates proper conversation log."""
        from scripts.telegram.bot import handle_message
        from scripts.telegram.send_message import send_message

        # Simulate conversation
        # User: Hello
        mock_telegram_update.message.text = "Hello"
        mock_telegram_update.effective_user.username = "alice"
        await handle_message(mock_telegram_update, mock_context)

        # Claude: Hi Alice
        with patch('scripts.telegram.send_message.Bot') as mock_bot_class:
            mock_bot_class.return_value = mock_telegram_bot
            await send_message("Hi Alice")

        # User: How are you?
        mock_telegram_update.message.text = "How are you?"
        await handle_message(mock_telegram_update, mock_context)

        # Claude: I'm doing well
        with patch('scripts.telegram.send_message.Bot') as mock_bot_class:
            mock_bot_class.return_value = mock_telegram_bot
            await send_message("I'm doing well")

        # Verify conversation log contains complete exchange
        log_file = temp_mind_dir["conversations"] / "2025-01-15.md"
        assert log_file.exists()

        content = log_file.read_text()

        # Verify all messages present
        assert "Hello" in content
        assert "Hi Alice" in content
        assert "How are you?" in content
        assert "I'm doing well" in content

        # Verify proper direction tags
        assert content.count("alice (incoming)") == 2
        assert content.count("Claude (outgoing)") == 2

        # Verify structure (4 conversation entries)
        assert content.count("##") == 4

    @pytest.mark.asyncio
    async def test_multiple_users_same_day_conversation_log(
        self, mock_telegram_update, mock_context,
        temp_mind_dir, mock_env, fixed_datetime
    ):
        """Test that multiple authorized users log to same daily file."""
        from scripts.telegram.bot import handle_message

        # Message from user 1
        mock_telegram_update.effective_user.username = "alice"
        mock_telegram_update.message.text = "Hello from Alice"
        await handle_message(mock_telegram_update, mock_context)

        # Message from user 2 (same authorized chat, different username)
        mock_telegram_update.effective_user.username = "bob"
        mock_telegram_update.message.text = "Hello from Bob"
        await handle_message(mock_telegram_update, mock_context)

        # Verify both in same log file
        log_file = temp_mind_dir["conversations"] / "2025-01-15.md"
        content = log_file.read_text()

        assert "alice (incoming)" in content
        assert "bob (incoming)" in content
        assert "Hello from Alice" in content
        assert "Hello from Bob" in content

    @pytest.mark.asyncio
    async def test_start_command_flow(
        self, mock_telegram_update, mock_context, mock_env
    ):
        """Test /start command complete flow."""
        from scripts.telegram.bot import handle_start

        # Execute /start command
        await handle_start(mock_telegram_update, mock_context)

        # Verify welcome message sent
        mock_telegram_update.message.reply_text.assert_called_once()
        call_args = mock_telegram_update.message.reply_text.call_args
        message = call_args[0][0]

        # Verify message contains key information
        assert "Connected to Claude" in message
        assert "persistent mind" in message
        assert "12345" in message  # Chat ID shown
        assert "message" in message.lower()  # Instructions mention messaging
