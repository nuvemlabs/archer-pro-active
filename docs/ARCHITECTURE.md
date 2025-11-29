# Claude Persistent Mind - Architecture

This document describes the architecture for giving Claude a persistent "mind" with continuous internal reflection and bidirectional Telegram communication.

## Vision

Claude runs as a persistent session inside the container, maintaining:
- **Continuous internal monologue** - reflecting, planning, reviewing past conversations
- **Telegram interface** - for bidirectional human communication
- **Cron triggers** - scheduled reflection/check-in points
- **Memory persistence** - thoughts and context survive restarts

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Container                      │
│                                                          │
│  ┌──────────────┐    ┌─────────────────────────────┐    │
│  │   Telegram   │───▶│     Claude Session          │    │
│  │  Bot (Poll)  │◀───│     (persistent tmux)       │    │
│  └──────────────┘    │                             │    │
│                      │  - Internal monologue       │    │
│  ┌──────────────┐    │  - Responds to messages     │    │
│  │    Cron      │───▶│  - Scheduled reflections    │    │
│  │   (hourly)   │    │  - Journal writing          │    │
│  └──────────────┘    └─────────────────────────────┘    │
│                                                          │
│  Persistent Volumes:                                     │
│  - ~/.claude (auth)                                      │
│  - ~/workspace/mind (memory, journal, queue)            │
└─────────────────────────────────────────────────────────┘
```

## Directory Structure

```
/home/dev/scripts/
├── telegram/
│   ├── bot.py                 # Telegram polling bot daemon
│   ├── send_message.py        # CLI tool: send-telegram "message"
│   └── requirements.txt       # python-telegram-bot
│
└── claude/
    ├── session_manager.sh     # Start/manage Claude tmux session
    ├── send_to_claude.sh      # Pipe input to Claude session
    └── reflection_cron.sh     # Hourly reflection trigger

/home/dev/workspace/mind/
├── system_prompt.md           # Claude's personality and instructions
├── memory.md                  # Persistent memory across restarts
├── journal/                   # Daily journal files
│   └── YYYY-MM-DD.md          # One file per day
├── message_queue/             # Incoming messages (processed in order)
│   └── YYYYMMDD-HHMMSS.msg    # Timestamped message files
└── conversations/             # Telegram conversation logs
    └── YYYY-MM-DD.md          # Daily conversation log
```

## Component Details

### Telegram Bot (`bot.py`)

- **Polling frequency**: Every 2-3 seconds
- **Incoming messages**: Written to `message_queue/` with timestamp filename
- **Outgoing messages**: Triggered by `send_message.py` CLI tool
- **Configuration**: Bot token and chat ID from environment variables

### Claude Session (`session_manager.sh`)

- Runs in a **tmux session** named `claude-mind`
- Survives SSH disconnects and container exec sessions
- Initialized with `system_prompt.md` context
- Can receive input from multiple sources (Telegram, cron, manual)

### Message Queue Protocol

1. Telegram bot writes messages to `message_queue/YYYYMMDD-HHMMSS.msg`
2. Claude checks queue directory periodically
3. Processes oldest message first (sorted by filename)
4. Responds via `send-telegram "response"`
5. Deletes processed message file
6. Logs conversation to `conversations/YYYY-MM-DD.md`

### Cron Jobs

| Schedule | Script | Purpose |
|----------|--------|---------|
| Hourly | `reflection_cron.sh` | Trigger structured reflection checkpoint |

Reflection prompt example:
> "Hourly checkpoint: Review your recent thoughts and journal entries. Any insights, patterns, or action items to note?"

### Memory System

**memory.md** - Long-term persistent memory
- Key facts and preferences learned about the user
- Important decisions and their rationale
- Ongoing projects and their status
- Ideas to explore later

**journal/YYYY-MM-DD.md** - Daily stream of consciousness
- Timestamped entries throughout the day
- Internal monologue and reflections
- Responses to reflection prompts
- Processing of conversations

## Claude's Behavioral Loop

```
While running:
  1. Check message_queue/ for new messages
     → If found:
        - Process message
        - Respond via send-telegram
        - Log to conversations/
        - Update memory.md if relevant

  2. If no messages, continue internal monologue:
     → Review recent journal entries
     → Reflect on past conversations
     → Explore ideas and alternative viewpoints
     → Write thoughts to journal
     → Periodically consolidate insights to memory.md

  3. On hourly cron trigger:
     → Structured reflection checkpoint
     → Review and summarize recent activity
     → Identify action items or insights
     → Optionally message user with important updates
```

## Configuration

### Environment Variables (docker-compose.yml)

```yaml
environment:
  - TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
  - TELEGRAM_CHAT_ID=your-telegram-chat-id
```

### Getting Telegram Credentials

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow prompts to create bot
3. Copy the bot token provided
4. Start a chat with your new bot
5. Get your chat ID by messaging the bot, then visiting:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`

## Startup Sequence (entrypoint.sh)

1. Fix volume permissions
2. Start SSH, cron, nginx services
3. Start Telegram bot as background daemon
4. Launch Claude session in tmux with system prompt
5. Claude begins internal monologue loop

## Design Decisions

### File-based Message Queue
- **Why**: Simpler than sockets/pipes, survives restarts, easy to debug and inspect
- **Tradeoff**: Slightly higher latency than direct IPC

### Single Persistent Session
- **Why**: Maintains conversation context and continuity
- **Tradeoff**: Session may get long; may need periodic refresh with memory reload

### Daily Journal Files
- **Why**: Natural chunking, easy to review specific days
- **Tradeoff**: Need to handle day boundaries gracefully

### Polling vs Webhook (for now)
- **Why**: Simpler setup, no public URL dependency
- **Future**: Can migrate to webhook when Cloudflare Tunnel is configured

## Future Enhancements

- [ ] Webhook-based Telegram integration for instant message delivery
- [ ] Multiple conversation threads/topics
- [ ] Proactive notifications based on time or events
- [ ] Integration with external APIs (calendar, weather, news)
- [ ] Voice message support
- [ ] Session refresh with memory consolidation
