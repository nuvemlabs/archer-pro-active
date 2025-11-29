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
su - dev -c "~/.tmux/plugins/tpm/bin/install_plugins" 2>/dev/null || true

# Initialize LazyVim (headless to download plugins)
echo "Initializing LazyVim plugins (this may take a moment)..."
su - dev -c "nvim --headless '+Lazy! sync' +qa" 2>/dev/null || true

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
echo "To authenticate Claude Code, run: claude"
echo "============================================"
echo ""

# Keep container running
tail -f /dev/null
