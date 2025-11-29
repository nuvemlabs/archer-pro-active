# Claude Dev Environment

A portable Docker container with Claude Code and a full development environment, designed to give Claude a **persistent mind** with continuous internal reflection and bidirectional Telegram communication.

## Vision

This project creates an always-running Claude instance that:
- **Thinks continuously** - maintains an internal monologue, reflecting on past conversations, exploring ideas
- **Communicates via Telegram** - bidirectional messaging for human interaction
- **Remembers across restarts** - persistent memory and daily journals
- **Reflects on schedule** - hourly cron-triggered reflection checkpoints

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full technical design.

## Quick Start

### 1. Build and run

```bash
cd claude-dev-env

# Build the image (takes 10-20 minutes first time)
docker compose build

# Start the container
docker compose up -d
```

### 2. Connect via SSH

```bash
ssh dev@localhost -p 2222
# Password: changeme123 (change this in docker-compose.yml!)
```

### 3. Authenticate Claude Code

Once inside the container:

```bash
claude
```

This will give you a URL to open in your browser. Complete the authentication, and you're ready to go!

---

## Configuration

### Change the password

Edit `docker-compose.yml`:

```yaml
environment:
  - DEV_PASSWORD=your-secure-password
```

### Use SSH key authentication (recommended)

1. Get your public key: `cat ~/.ssh/id_rsa.pub` (or `id_ed25519.pub`)

2. Add it to `docker-compose.yml`:

```yaml
environment:
  - SSH_PUBLIC_KEY=ssh-rsa AAAA... your-key-here
```

3. Optionally disable password auth by editing `Dockerfile`:

```dockerfile
RUN sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
```

### Setup Cloudflare Tunnel (for external access)

1. Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. Create a tunnel under Access > Tunnels
3. Copy the tunnel token
4. Add to `docker-compose.yml`:

```yaml
environment:
  - CLOUDFLARE_TUNNEL_TOKEN=your-token-here
```

5. Configure the tunnel in Cloudflare dashboard to route to `localhost:22` for SSH

---

## What's Included

### Shells
- **zsh** (default, with Oh My Zsh)
- **nushell** (`nu`)
- **PowerShell** (`pwsh`)

### Editor
- **Neovim** with LazyVim pre-configured

### Terminal
- **tmux** with session persistence (resurrect + continuum)

### Search Tools
- **fd** (find replacement)
- **rg** (ripgrep - grep replacement)

### Runtimes
- **Node.js 20** + pnpm
- **Python 3** + pip
- **.NET 8**
- **Rust** + cargo

### Cloud CLIs
- **AWS CLI**
- **Azure CLI**
- **Google Cloud CLI**
- **Terraform**

### Infrastructure
- **nginx**
- **cron**
- **SSH server**
- **Cloudflare Tunnel** (cloudflared)

### AI
- **Claude Code** (`claude`)

---

## Useful Commands

### Container management

```bash
# Start
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f

# Rebuild after changes
docker compose build --no-cache
docker compose up -d

# Enter container as root (for debugging)
docker exec -it claude-dev-env bash

# Enter container as dev user
docker exec -it -u dev claude-dev-env zsh
```

### Inside the container

```bash
# Start tmux (sessions persist across restarts)
tmux

# Claude Code
claude

# Switch shells
nu      # nushell
pwsh    # powershell
zsh     # back to zsh
```

---

## Persisted Data

The following directories are persisted in Docker volumes:

| Path | Purpose |
|------|---------|
| `/home/dev/workspace` | Your main working directory |
| `/home/dev/scripts` | Your custom scripts |
| `/home/dev/.ssh` | SSH keys and config |
| `/home/dev/.config` | App configs (nvim, etc.) |
| `/home/dev/.local` | Local binaries, pip packages |
| `/home/dev/.claude` | Claude Code auth and settings |
| `/home/dev/.tmux` | Tmux plugins and resurrect data |

---

## Telegram Setup

To enable Claude's Telegram integration:

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow prompts to create your bot
3. Copy the bot token provided
4. Start a chat with your new bot and send any message
5. Get your chat ID by visiting: `https://api.telegram.org/bot<TOKEN>/getUpdates`
6. Add credentials to `docker-compose.yml`:

```yaml
environment:
  - TELEGRAM_BOT_TOKEN=your-bot-token
  - TELEGRAM_CHAT_ID=your-chat-id
```

---

## Roadmap

- [x] Basic Docker environment with Claude Code
- [ ] Telegram bot integration (polling)
- [ ] Persistent Claude session with internal monologue
- [ ] Memory and journal system
- [ ] Hourly reflection cron jobs
- [ ] Webhook-based Telegram (future)
- [ ] Migration to lighter base image (Alpine/Void experiment)

---

## Troubleshooting

### Build fails at a specific step

Try building with more verbose output:

```bash
docker compose build --progress=plain
```

### SSH connection refused

Make sure the container is running:

```bash
docker compose ps
```

Check if SSH is listening:

```bash
docker exec claude-dev-env service ssh status
```

### Claude Code auth not persisting

Make sure the `claude-claude` volume is mounted correctly. Check:

```bash
docker volume ls | grep claude
```

### Out of disk space

```bash
# Clean up Docker
docker system prune -a
```
