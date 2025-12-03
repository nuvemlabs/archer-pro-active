#!/bin/bash
#
# Hourly Reflection Cron Job
# Triggers Claude to perform a structured reflection checkpoint
#

MIND_DIR="$HOME/workspace/mind"
MESSAGE_QUEUE="$MIND_DIR/message_queue"
LOG_FILE="$MIND_DIR/cron.log"

# Ensure directories exist
mkdir -p "$MESSAGE_QUEUE"

# Generate timestamp for the message file
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
MSG_FILE="$MESSAGE_QUEUE/${TIMESTAMP}-reflection.msg"

# Current hour for context
HOUR=$(date +%H)
DATE=$(date +"%A, %B %d, %Y")
TIME=$(date +"%H:%M")

# Create the reflection prompt
cat > "$MSG_FILE" << EOF
From: system (hourly reflection)
Time: $(date --iso-8601=seconds)

[HOURLY REFLECTION CHECKPOINT - $TIME on $DATE]

It's time for your hourly reflection. Please:

1. Review your recent journal entries from today
2. Check if there are any patterns or insights worth noting
3. Consider if there's anything important to update in memory.md
4. Think about what you want to explore or reflect on next
5. If there's anything significant the user should know about, send them a brief Telegram message

Take a moment to pause, reflect, and write your thoughts to today's journal.
EOF

# Log the cron execution
echo "$(date --iso-8601=seconds) - Hourly reflection triggered" >> "$LOG_FILE"

echo "Reflection prompt queued: $MSG_FILE"
