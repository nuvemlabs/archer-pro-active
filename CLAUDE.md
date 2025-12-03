# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a portable Docker development environment ("Claude Dev Environment") that packages Claude Code with a full development stack. The container provides SSH access to a pre-configured environment with multiple shells, editors, runtimes, and cloud CLIs.

## Build and Run Commands

```bash
# Build the image (first build takes 10-20 minutes)
docker compose build

# Build with verbose output (for debugging)
docker compose build --progress=plain

# Start the container
docker compose up -d

# Stop the container
docker compose down

# View container logs
docker compose logs -f

# Rebuild from scratch
docker compose build --no-cache && docker compose up -d

# Access container as root
docker exec -it claude-dev-env bash

# Access container as dev user
docker exec -it -u dev claude-dev-env zsh
```

## Architecture

### Container Structure

- **Base**: Debian Bookworm (slim)
- **User**: `dev` with passwordless sudo, default shell zsh
- **Exposed ports**: 22 (SSH), 80 (nginx), 443 (nginx)

### Key Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build defining all installed tools and user setup |
| `docker-compose.yml` | Container orchestration with volume mounts and environment config |
| `entrypoint.sh` | Runtime initialization (SSH, cron, nginx, Cloudflare tunnel, plugin setup) |

### Persistent Volumes

All user data persists across container restarts via named Docker volumes:
- `claude-workspace` → `/home/dev/workspace`
- `claude-scripts` → `/home/dev/scripts`
- `claude-ssh` → `/home/dev/.ssh`
- `claude-config` → `/home/dev/.config`
- `claude-local` → `/home/dev/.local`
- `claude-claude` → `/home/dev/.claude`
- `claude-tmux` → `/home/dev/.tmux`

### Installed Stack

**Shells**: zsh (Oh My Zsh), nushell, PowerShell
**Editor**: Neovim with LazyVim
**Terminal**: tmux with resurrect/continuum for session persistence
**Runtimes**: Node.js 20 + pnpm, Python 3 + pip, .NET 8, Rust + cargo
**Cloud**: AWS CLI, Azure CLI, Google Cloud CLI, Terraform
**Tools**: fd, ripgrep, Homebrew (linuxbrew)
**Infrastructure**: nginx, cron, SSH server, cloudflared

### Configuration

Environment variables in `docker-compose.yml`:
- `DEV_PASSWORD` - SSH password for dev user
- `SSH_PUBLIC_KEY` - Optional public key for key-based auth
- `CLOUDFLARE_TUNNEL_TOKEN` - Optional Cloudflare Tunnel token for external access
- `TELEGRAM_BOT_TOKEN` - Telegram bot token for messaging integration
- `TELEGRAM_CHAT_ID` - Authorized Telegram chat ID

## Persistent Mind Features

### Claude Session Management

The persistent Claude session is managed via `/usr/local/bin/claude-session` script:

```bash
claude-session start    # Start Claude in tmux
claude-session stop     # Stop Claude session
claude-session restart  # Restart session
claude-session status   # Check if running
claude-session attach   # Attach to interactive session
claude-session send "message"  # Send input to Claude
```

The session starts automatically on container boot with:
- **Bypass permissions mode** enabled (hands-free operation using `--permission-mode bypassPermissions`)
- **Theme wizard skipped** via `~/.claude.json` with `"hasCompletedOnboarding": true`
- **Automated warning acceptance** using tmux key automation (Down arrow + Enter)
- **Initial prompt** sent to begin persistent mind loop
- **Message queue** monitoring for Telegram integration

### Telegram Bot Integration

The Telegram bot (`/opt/scripts/telegram/bot.py`) runs automatically and:
- Polls for messages every 10 seconds
- Queues incoming messages to `/home/dev/workspace/mind/message_queue/`
- Only accepts messages from authorized `TELEGRAM_CHAT_ID`
- Provides `/opt/venv/bin/python /opt/scripts/telegram/send_message.py` for Claude to send replies

### Hourly Reflection Cron

A cron job runs every hour (`0 * * * *`) via `/opt/scripts/claude/reflection_cron.sh` to:
- Create a reflection checkpoint message in the message queue
- Prompt Claude to review journal entries and update memory
- Encourage periodic self-reflection and pattern recognition

### File Structure

```
/home/dev/workspace/mind/
├── system_prompt.md          # Claude's behavioral instructions
├── memory.md                 # Persistent memory storage
├── journal/                  # Daily journal entries (YYYY-MM-DD.md)
├── message_queue/            # Incoming messages (.msg files)
└── conversations/            # Conversation history backups
```

## Implementation Status

- ✅ Telegram bot integration (polling mode)
- ✅ Hourly cron-based reflection checkpoints
- ✅ Persistent Claude session with tmux
- ✅ Hands-free container startup (bypass permissions + wizard skip)
- ✅ Message queue system
- ✅ Journal and memory file structure
- ⏳ Claude message processing loop (manual for now)
- ⏳ End-to-end Telegram → Claude → Response flow
