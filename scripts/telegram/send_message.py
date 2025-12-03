#!/opt/venv/bin/python
"""
Send a message to Telegram from Claude.

Usage:
    send-telegram "Your message here"
    echo "message" | send-telegram
"""

import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

from telegram import Bot

# Configuration from environment
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Paths for logging
MIND_DIR = Path.home() / "workspace" / "mind"
CONVERSATIONS_DIR = MIND_DIR / "conversations"


def log_outgoing(text: str):
    """Log outgoing message to daily conversation file."""
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    filepath = CONVERSATIONS_DIR / f"{today}.md"

    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"\n## {timestamp} - Claude (outgoing)\n\n{text}\n"

    with open(filepath, "a") as f:
        f.write(entry)


async def send_message(text: str) -> bool:
    """Send message to Telegram."""
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not set", file=sys.stderr)
        return False

    if not CHAT_ID:
        print("Error: TELEGRAM_CHAT_ID not set", file=sys.stderr)
        return False

    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text)
        log_outgoing(text)
        return True
    except Exception as e:
        print(f"Error sending message: {e}", file=sys.stderr)
        return False


def main():
    # Get message from argument or stdin
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    elif not sys.stdin.isatty():
        message = sys.stdin.read().strip()
    else:
        print("Usage: send-telegram \"message\"", file=sys.stderr)
        print("   or: echo \"message\" | send-telegram", file=sys.stderr)
        sys.exit(1)

    if not message:
        print("Error: Empty message", file=sys.stderr)
        sys.exit(1)

    success = asyncio.run(send_message(message))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
