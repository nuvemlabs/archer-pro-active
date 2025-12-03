#!/opt/venv/bin/python
"""
Telegram Bot for Claude Persistent Mind

Polls Telegram for incoming messages and writes them to the message queue.
Claude processes the queue and responds via send_message.py.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# Configuration from environment
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Paths
MIND_DIR = Path.home() / "workspace" / "mind"
MESSAGE_QUEUE_DIR = MIND_DIR / "message_queue"
CONVERSATIONS_DIR = MIND_DIR / "conversations"

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def ensure_directories():
    """Create required directories if they don't exist."""
    MESSAGE_QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)


def is_authorized(chat_id: int) -> bool:
    """Check if the chat ID is authorized."""
    if not ALLOWED_CHAT_ID:
        logger.warning("TELEGRAM_CHAT_ID not set - accepting all messages")
        return True
    return str(chat_id) == str(ALLOWED_CHAT_ID)


def queue_message(text: str, username: str) -> str:
    """Write message to queue and return the filename."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}.msg"
    filepath = MESSAGE_QUEUE_DIR / filename

    content = f"From: {username}\nTime: {datetime.now().isoformat()}\n\n{text}"
    filepath.write_text(content)

    logger.info(f"Queued message: {filename}")
    return filename


def log_conversation(direction: str, text: str, username: str = "user"):
    """Log message to daily conversation file."""
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = CONVERSATIONS_DIR / f"{today}.md"

    timestamp = datetime.now().strftime("%H:%M:%S")

    if direction == "incoming":
        entry = f"\n## {timestamp} - {username} (incoming)\n\n{text}\n"
    else:
        entry = f"\n## {timestamp} - Claude (outgoing)\n\n{text}\n"

    with open(filepath, "a") as f:
        f.write(entry)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    chat_id = update.effective_chat.id
    username = update.effective_user.username or update.effective_user.first_name or "unknown"
    text = update.message.text

    if not is_authorized(chat_id):
        logger.warning(f"Unauthorized message from chat_id={chat_id}, user={username}")
        await update.message.reply_text("Unauthorized. This bot is private.")
        return

    logger.info(f"Received message from {username}: {text[:50]}...")

    # Queue the message for Claude
    queue_message(text, username)

    # Log the conversation
    log_conversation("incoming", text, username)

    # Acknowledge receipt (optional - can be removed for more natural flow)
    # await update.message.reply_text("Message received. Claude will respond shortly.")


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    chat_id = update.effective_chat.id

    if not is_authorized(chat_id):
        await update.message.reply_text("Unauthorized. This bot is private.")
        return

    await update.message.reply_text(
        "Connected to Claude's persistent mind.\n\n"
        "Send any message and Claude will respond when ready.\n\n"
        f"Your chat ID: {chat_id}"
    )


async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    chat_id = update.effective_chat.id

    if not is_authorized(chat_id):
        await update.message.reply_text("Unauthorized.")
        return

    # Count queued messages
    queue_count = len(list(MESSAGE_QUEUE_DIR.glob("*.msg")))

    # Get today's conversation file size
    today = datetime.now().strftime("%Y-%m-%d")
    conv_file = CONVERSATIONS_DIR / f"{today}.md"
    conv_size = conv_file.stat().st_size if conv_file.exists() else 0

    await update.message.reply_text(
        f"Status:\n"
        f"- Messages in queue: {queue_count}\n"
        f"- Today's conversation log: {conv_size} bytes"
    )


def main():
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        sys.exit(1)

    ensure_directories()

    logger.info("Starting Telegram bot...")
    if ALLOWED_CHAT_ID:
        logger.info(f"Authorized chat ID: {ALLOWED_CHAT_ID}")
    else:
        logger.warning("No TELEGRAM_CHAT_ID set - bot will accept messages from anyone!")

    # Create application
    app = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("status", handle_status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling
    logger.info("Bot started, polling for messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
