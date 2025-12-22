"""
Shared test fixtures for archer-pro-active Telegram integration tests.

Fixture Scope Strategy:
- function: Default, recreated per test (most fixtures)
- module: Shared within a test module (expensive setup)
- session: Shared across entire test session (test configuration)
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================
# ENVIRONMENT FIXTURES
# ============================================

@pytest.fixture
def mock_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token-12345")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")

    # Also patch the module-level variables that were imported at module load time
    import scripts.telegram.bot as bot_module
    import scripts.telegram.send_message as send_module

    monkeypatch.setattr(bot_module, 'BOT_TOKEN', "test-token-12345")
    monkeypatch.setattr(bot_module, 'ALLOWED_CHAT_ID', "12345")
    monkeypatch.setattr(send_module, 'BOT_TOKEN', "test-token-12345")
    monkeypatch.setattr(send_module, 'CHAT_ID', "12345")

    return {
        "BOT_TOKEN": "test-token-12345",
        "CHAT_ID": "12345"
    }


@pytest.fixture
def mock_env_no_chat_id(monkeypatch):
    """Environment with no CHAT_ID (accept all)."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token-12345")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    # Also patch the module-level variables
    import scripts.telegram.bot as bot_module
    import scripts.telegram.send_message as send_module

    monkeypatch.setattr(bot_module, 'BOT_TOKEN', "test-token-12345")
    monkeypatch.setattr(bot_module, 'ALLOWED_CHAT_ID', None)
    monkeypatch.setattr(send_module, 'BOT_TOKEN', "test-token-12345")
    monkeypatch.setattr(send_module, 'CHAT_ID', None)

    return {
        "BOT_TOKEN": "test-token-12345",
        "CHAT_ID": None
    }


# ============================================
# FILESYSTEM FIXTURES
# ============================================

@pytest.fixture
def temp_mind_dir(tmp_path, monkeypatch):
    """Create temporary mind directory structure."""
    mind_dir = tmp_path / "mind"
    message_queue = mind_dir / "message_queue"
    conversations = mind_dir / "conversations"
    journal = mind_dir / "journal"

    message_queue.mkdir(parents=True)
    conversations.mkdir(parents=True)
    journal.mkdir(parents=True)

    # Patch module-level directory constants
    import scripts.telegram.bot as bot_module
    import scripts.telegram.send_message as send_module

    monkeypatch.setattr(bot_module, 'MIND_DIR', mind_dir)
    monkeypatch.setattr(bot_module, 'MESSAGE_QUEUE_DIR', message_queue)
    monkeypatch.setattr(bot_module, 'CONVERSATIONS_DIR', conversations)

    monkeypatch.setattr(send_module, 'MIND_DIR', mind_dir)
    monkeypatch.setattr(send_module, 'CONVERSATIONS_DIR', conversations)

    return {
        "mind": mind_dir,
        "queue": message_queue,
        "conversations": conversations,
        "journal": journal
    }


# ============================================
# TELEGRAM API FIXTURES
# ============================================

@pytest.fixture
def mock_telegram_update():
    """Mock telegram.Update object with realistic data."""
    update = Mock()
    update.effective_chat.id = 12345
    update.effective_user.username = "testuser"
    update.effective_user.first_name = "Test"
    update.effective_user.last_name = "User"
    update.message.text = "Hello Claude"
    update.message.message_id = 1001
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_telegram_update_unauthorized():
    """Mock Update from unauthorized user."""
    update = Mock()
    update.effective_chat.id = 99999  # Wrong ID
    update.effective_user.username = "hacker"
    update.effective_user.first_name = "Hacker"
    update.message.text = "Unauthorized access"
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Mock telegram.ext.ContextTypes.DEFAULT_TYPE."""
    return Mock()


@pytest.fixture
def mock_telegram_bot():
    """Mock telegram.Bot for send operations."""
    bot_instance = Mock()
    bot_instance.send_message = AsyncMock()
    return bot_instance


@pytest.fixture
def mock_application():
    """Mock telegram.ext.Application."""
    app_instance = Mock()
    builder_mock = Mock()
    builder_mock.token.return_value = builder_mock
    builder_mock.build.return_value = app_instance

    app_instance.add_handler = Mock()
    app_instance.run_polling = Mock()

    with patch('scripts.telegram.bot.Application') as mock_app_class:
        mock_app_class.builder.return_value = builder_mock
        yield app_instance


# ============================================
# TIME FIXTURES
# ============================================

@pytest.fixture
def fixed_datetime(monkeypatch):
    """Freeze time to 2025-01-15 12:30:45 for predictable timestamps."""
    import scripts.telegram.bot as bot_module
    import scripts.telegram.send_message as send_module
    from datetime import datetime as dt

    # Counter to generate unique timestamps for multiple calls in same test
    counter = {"value": 0}

    # Create a custom datetime class that has the real datetime methods
    # but with a mocked now()
    class FrozenDatetime(dt):
        @classmethod
        def now(cls, tz=None):
            # Add counter seconds to make timestamps unique
            base = dt(2025, 1, 15, 12, 30, 45)
            result = base.replace(second=45 + counter["value"])
            counter["value"] += 1
            return result

    monkeypatch.setattr(bot_module, 'datetime', FrozenDatetime)
    monkeypatch.setattr(send_module, 'datetime', FrozenDatetime)

    return FrozenDatetime.now()


# ============================================
# LOGGING FIXTURES
# ============================================

@pytest.fixture
def captured_logs(caplog):
    """Capture log messages for assertions."""
    import logging
    caplog.set_level(logging.INFO)
    return caplog
