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

## Planned Features (TODO)

- Telegram bot integration for proactive messaging
- Hourly cron job for Claude communication
- Custom scripts integration
