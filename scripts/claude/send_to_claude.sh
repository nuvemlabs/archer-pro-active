#!/bin/bash
#
# Send input to the Claude session
# Used by Telegram bot and cron jobs
#

SESSION_NAME="claude-mind"

if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Error: Claude session is not running" >&2
    exit 1
fi

if [ -z "$1" ]; then
    # Read from stdin if no argument
    INPUT=$(cat)
else
    INPUT="$*"
fi

if [ -z "$INPUT" ]; then
    echo "Error: No input provided" >&2
    exit 1
fi

tmux send-keys -t "$SESSION_NAME" "$INPUT" Enter
