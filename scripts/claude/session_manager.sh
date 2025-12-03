#!/bin/bash
#
# Claude Session Manager
# Manages the persistent Claude session in tmux
#

SESSION_NAME="claude-mind"
MIND_DIR="$HOME/workspace/mind"
SYSTEM_PROMPT="$MIND_DIR/system_prompt.md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 {start|stop|restart|status|attach|send}"
    echo ""
    echo "Commands:"
    echo "  start   - Start Claude session in tmux"
    echo "  stop    - Stop Claude session"
    echo "  restart - Restart Claude session"
    echo "  status  - Check if session is running"
    echo "  attach  - Attach to Claude session"
    echo "  send    - Send input to Claude session"
    exit 1
}

is_running() {
    tmux has-session -t "$SESSION_NAME" 2>/dev/null
}

start_session() {
    if is_running; then
        echo -e "${YELLOW}Session '$SESSION_NAME' is already running${NC}"
        return 0
    fi

    echo -e "${GREEN}Starting Claude session...${NC}"

    # Ensure mind directory exists
    mkdir -p "$MIND_DIR/journal" "$MIND_DIR/message_queue" "$MIND_DIR/conversations"

    # Build the initial prompt for Claude
    INIT_PROMPT=$(cat <<'EOF'
You are starting up as a persistent mind. Please:

1. Read your system prompt at ~/workspace/mind/system_prompt.md
2. Read your memory at ~/workspace/mind/memory.md
3. Check for any recent journal entries in ~/workspace/mind/journal/
4. Check for pending messages in ~/workspace/mind/message_queue/
5. Begin your internal monologue loop

Start by reading your system prompt to understand your role and capabilities.
EOF
)

    # Start tmux session with Claude
    tmux new-session -d -s "$SESSION_NAME" -x 200 -y 50

    # Give tmux a moment to initialize
    sleep 1

    # Start Claude in the session with the system prompt
    tmux send-keys -t "$SESSION_NAME" "cd $MIND_DIR && claude --permission-mode bypassPermissions" Enter

    # Wait for Claude to initialize and show the bypass permissions warning
    sleep 3

    # Navigate to "Yes, I accept" option (Down arrow moves cursor to option 2)
    tmux send-keys -t "$SESSION_NAME" Down
    sleep 0.5

    # Confirm the selection
    tmux send-keys -t "$SESSION_NAME" Enter

    # Wait for Claude to fully start
    sleep 5

    # Send the initial prompt
    tmux send-keys -t "$SESSION_NAME" "$INIT_PROMPT" Enter

    echo -e "${GREEN}Claude session started in tmux session '$SESSION_NAME'${NC}"
    echo "Use '$0 attach' to attach to the session"
    echo "Use '$0 send \"message\"' to send input"
}

stop_session() {
    if ! is_running; then
        echo -e "${YELLOW}Session '$SESSION_NAME' is not running${NC}"
        return 0
    fi

    echo -e "${RED}Stopping Claude session...${NC}"
    tmux kill-session -t "$SESSION_NAME"
    echo -e "${GREEN}Session stopped${NC}"
}

restart_session() {
    stop_session
    sleep 2
    start_session
}

check_status() {
    if is_running; then
        echo -e "${GREEN}Session '$SESSION_NAME' is running${NC}"

        # Show some stats
        QUEUE_COUNT=$(find "$MIND_DIR/message_queue" -name "*.msg" 2>/dev/null | wc -l)
        echo "  Messages in queue: $QUEUE_COUNT"

        TODAY=$(date +%Y-%m-%d)
        if [ -f "$MIND_DIR/journal/$TODAY.md" ]; then
            JOURNAL_LINES=$(wc -l < "$MIND_DIR/journal/$TODAY.md")
            echo "  Today's journal: $JOURNAL_LINES lines"
        else
            echo "  Today's journal: not started"
        fi

        return 0
    else
        echo -e "${RED}Session '$SESSION_NAME' is not running${NC}"
        return 1
    fi
}

attach_session() {
    if ! is_running; then
        echo -e "${RED}Session '$SESSION_NAME' is not running${NC}"
        echo "Start it with: $0 start"
        return 1
    fi

    tmux attach-session -t "$SESSION_NAME"
}

send_to_session() {
    if ! is_running; then
        echo -e "${RED}Session '$SESSION_NAME' is not running${NC}"
        return 1
    fi

    if [ -z "$1" ]; then
        echo "Usage: $0 send \"message\""
        return 1
    fi

    tmux send-keys -t "$SESSION_NAME" "$*" Enter
    echo -e "${GREEN}Sent to Claude session${NC}"
}

# Main
case "${1:-}" in
    start)
        start_session
        ;;
    stop)
        stop_session
        ;;
    restart)
        restart_session
        ;;
    status)
        check_status
        ;;
    attach)
        attach_session
        ;;
    send)
        shift
        send_to_session "$*"
        ;;
    *)
        usage
        ;;
esac
