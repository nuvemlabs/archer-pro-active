#!/bin/bash

# ============================================
# ENTRYPOINT SCRIPT
# ============================================

# Set dev user password if provided
if [ -n "$DEV_PASSWORD" ]; then
    echo "dev:$DEV_PASSWORD" | chpasswd
    echo "Password set for user 'dev'"
fi

# Add SSH public key if provided
if [ -n "$SSH_PUBLIC_KEY" ]; then
    mkdir -p /home/dev/.ssh
    echo "$SSH_PUBLIC_KEY" > /home/dev/.ssh/authorized_keys
    chmod 600 /home/dev/.ssh/authorized_keys
    chown -R dev:dev /home/dev/.ssh
    echo "SSH public key added"
fi

# Fix ownership of mounted volumes (they may be created as root)
echo "Fixing ownership of home directories..."
chown -R dev:dev /home/dev/.claude /home/dev/.config /home/dev/.local /home/dev/.ssh /home/dev/.tmux /home/dev/workspace /home/dev/scripts 2>/dev/null || true

# Initialize mind directory from template if empty
if [ ! -f /home/dev/workspace/mind/system_prompt.md ]; then
    echo "Initializing mind directory from template..."
    cp -rn /opt/mind-template/* /home/dev/workspace/mind/ 2>/dev/null || true
    chown -R dev:dev /home/dev/workspace/mind
fi

# Import Claude authentication if volume is empty and import exists
if [ ! -f /home/dev/.claude/.credentials.json ] && [ -f /opt/claude-auth-import/.credentials.json ]; then
    echo "Importing Claude authentication from host..."
    mkdir -p /home/dev/.claude
    # Copy all files including hidden ones
    cp -r /opt/claude-auth-import/. /home/dev/.claude/ 2>/dev/null || true
    chown -R dev:dev /home/dev/.claude
    echo "✅ Claude authentication imported successfully"
elif [ -f /home/dev/.claude/.credentials.json ]; then
    echo "Claude authentication already exists in volume"
else
    echo "No Claude authentication to import (run ./scripts/import-claude-auth.sh before building)"
fi

# Create .claude.json config to skip first-time setup wizard
if [ ! -f /home/dev/.claude.json ]; then
    echo "Creating .claude.json to skip onboarding wizard..."
    cp /opt/mind-template/default-claude-config.json /home/dev/.claude.json
    chown dev:dev /home/dev/.claude.json
fi

# Ensure settings have theme configuration
if [ -f /home/dev/.claude/settings.json ]; then
    # Check if settings.json has appearance.theme - if not, use defaults
    if ! grep -q '"appearance"' /home/dev/.claude/settings.json 2>/dev/null; then
        echo "Adding theme configuration to settings.json..."
        cp /opt/mind-template/default-settings.json /home/dev/.claude/settings.json
        chown dev:dev /home/dev/.claude/settings.json
    fi
else
    echo "Applying default settings.json..."
    cp /opt/mind-template/default-settings.json /home/dev/.claude/settings.json
    chown dev:dev /home/dev/.claude/settings.json
fi

if [ ! -f /home/dev/.claude/settings.local.json ]; then
    echo "Applying default settings.local.json..."
    cp /opt/mind-template/default-settings.local.json /home/dev/.claude/settings.local.json
    chown dev:dev /home/dev/.claude/settings.local.json
fi

# Start SSH server
echo "Starting SSH server..."
/usr/sbin/sshd

# Start cron
echo "Starting cron..."
service cron start

# Start nginx
echo "Starting nginx..."
service nginx start

# Setup Cloudflare Tunnel if token provided
if [ -n "$CLOUDFLARE_TUNNEL_TOKEN" ]; then
    echo "Starting Cloudflare Tunnel..."
    cloudflared service install "$CLOUDFLARE_TUNNEL_TOKEN"
fi

# Install tmux plugins for dev user
echo "Installing tmux plugins..."
su - dev -c "~/.tmux/plugins/tpm/bin/install_plugins" 2>/dev/null || true
echo "Tmux plugins installed"

# Initialize LazyVim (headless to download plugins)
# Disabled for now - can hang on first startup
# echo "Initializing LazyVim plugins (this may take a moment)..."
# timeout 30 su - dev -c "nvim --headless '+Lazy! sync' +qa" 2>/dev/null || true
echo "Skipping LazyVim initialization (run manually if needed)"

# ============================================
# SETUP HOURLY REFLECTION CRON JOB
# ============================================
echo "Setting up hourly reflection cron job..."
CRON_JOB="0 * * * * /opt/scripts/claude/reflection_cron.sh"
echo "$CRON_JOB" | crontab -u dev -
echo "Cron job configured"

# ============================================
# START TELEGRAM BOT (if configured)
# ============================================
echo "Checking Telegram configuration..."
echo "Bot token set: $([ -n "$TELEGRAM_BOT_TOKEN" ] && echo "yes" || echo "no")"
echo "Chat ID set: $([ -n "$TELEGRAM_CHAT_ID" ] && echo "yes" || echo "no")"

if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    echo "Starting Telegram bot..."
    # Run as dev user in background, using venv python
    su - dev -c "cd /home/dev/workspace/mind && TELEGRAM_BOT_TOKEN='$TELEGRAM_BOT_TOKEN' TELEGRAM_CHAT_ID='$TELEGRAM_CHAT_ID' nohup /opt/venv/bin/python /opt/scripts/telegram/bot.py > telegram-bot.log 2>&1 &"
    sleep 2
    echo "Telegram bot started (logs: ~/workspace/mind/telegram-bot.log)"
else
    echo "Telegram bot not started (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set)"
fi

# ============================================
# START CLAUDE SESSION (if authenticated)
# ============================================
echo "Checking Claude authentication..."
if [ -f /home/dev/.claude/.credentials.json ]; then
    echo "Claude authenticated - starting session..."
    su - dev -c "/usr/local/bin/claude-session start"
    sleep 3
    echo "Claude session started"
else
    echo "Claude not authenticated yet - run 'claude' to authenticate"
    echo "Then run 'claude-session start' to begin the persistent mind"
fi

echo ""
echo "============================================"
echo "  Claude Dev Environment Ready!"
echo "============================================"
echo ""
echo "SSH: ssh dev@<host> -p <port>"
echo "Default shell: zsh"
echo ""
echo "Installed tools:"
echo "  - Shells: zsh, nushell (nu), powershell (pwsh)"
echo "  - Editor: neovim with LazyVim"
echo "  - Terminal: tmux with session persistence"
echo "  - Search: fd, rg (ripgrep)"
echo "  - Runtimes: node, pnpm, python, pip, dotnet, cargo"
echo "  - Cloud: aws, az, gcloud, terraform"
echo "  - AI: claude (Claude Code)"
echo "  - Tunnel: cloudflared"
echo ""
echo "Claude Persistent Mind:"
echo "  - Telegram bot: $([ -n "$TELEGRAM_BOT_TOKEN" ] && echo "running" || echo "not configured")"
echo "  - Hourly reflection: enabled"
echo "  - Claude session: $(su - dev -c 'tmux has-session -t claude-mind 2>/dev/null' && echo "running" || echo "not started")"
echo "  - Attach to Claude: claude-session attach"
echo "  - Send to Claude: claude-session send \"message\""
echo "============================================"
echo ""

# Keep container running
tail -f /dev/null
