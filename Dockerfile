FROM debian:bookworm-slim AS base

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install base dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    git \
    gnupg \
    lsb-release \
    software-properties-common \
    apt-transport-https \
    unzip \
    zip \
    jq \
    build-essential \
    cmake \
    pkg-config \
    libssl-dev \
    openssh-server \
    cron \
    nginx \
    sudo \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Generate locale
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# ============================================
# SHELLS: zsh, nushell, powershell
# ============================================
RUN apt-get update && apt-get install -y --no-install-recommends zsh \
    && rm -rf /var/lib/apt/lists/*

# Nushell
RUN curl -LO https://github.com/nushell/nushell/releases/download/0.98.0/nu-0.98.0-x86_64-unknown-linux-gnu.tar.gz \
    && tar -xzf nu-0.98.0-x86_64-unknown-linux-gnu.tar.gz \
    && mv nu-0.98.0-x86_64-unknown-linux-gnu/nu /usr/local/bin/ \
    && rm -rf nu-0.98.0-x86_64-unknown-linux-gnu*

# PowerShell
RUN curl -LO https://github.com/PowerShell/PowerShell/releases/download/v7.4.6/powershell_7.4.6-1.deb_amd64.deb \
    && dpkg -i powershell_7.4.6-1.deb_amd64.deb || apt-get install -f -y \
    && rm powershell_7.4.6-1.deb_amd64.deb

# ============================================
# SEARCH TOOLS: fd, ripgrep
# ============================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    fd-find \
    ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s $(which fdfind) /usr/local/bin/fd

# ============================================
# TERMINAL: tmux with session persistence
# ============================================
RUN apt-get update && apt-get install -y --no-install-recommends tmux \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# EDITOR: Neovim + LazyVim
# ============================================
RUN curl -LO https://github.com/neovim/neovim/releases/download/v0.10.2/nvim-linux64.tar.gz \
    && tar -xzf nvim-linux64.tar.gz \
    && mv nvim-linux64 /opt/nvim \
    && ln -s /opt/nvim/bin/nvim /usr/local/bin/nvim \
    && ln -s /opt/nvim/bin/nvim /usr/local/bin/vim \
    && rm nvim-linux64.tar.gz

# ============================================
# PYTHON
# ============================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3 /usr/local/bin/python

# ============================================
# NODE.JS + PNPM
# ============================================
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g pnpm

# ============================================
# .NET CORE
# ============================================
RUN curl -sSL https://dot.net/v1/dotnet-install.sh | bash /dev/stdin --channel 8.0 --install-dir /usr/share/dotnet \
    && ln -s /usr/share/dotnet/dotnet /usr/local/bin/dotnet

# ============================================
# RUST + CARGO
# ============================================
ENV RUSTUP_HOME=/opt/rustup
ENV CARGO_HOME=/opt/cargo
ENV PATH="/opt/cargo/bin:$PATH"
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path

# ============================================
# CLOUD CLIs
# ============================================

# AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf aws awscliv2.zip

# Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Google Cloud CLI
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && apt-get update && apt-get install -y google-cloud-cli \
    && rm -rf /var/lib/apt/lists/*

# Terraform
RUN curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list \
    && apt-get update && apt-get install -y terraform \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# CLOUDFLARE TUNNEL
# ============================================
RUN curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb \
    && dpkg -i cloudflared.deb \
    && rm cloudflared.deb

# ============================================
# CLAUDE CODE
# ============================================
RUN npm install -g @anthropic-ai/claude-code

# ============================================
# CREATE USER
# ============================================
RUN useradd -m -s /bin/zsh -G sudo dev \
    && echo "dev ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# ============================================
# SSH SERVER SETUP
# ============================================
RUN mkdir /var/run/sshd \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# ============================================
# SETUP USER ENVIRONMENT
# ============================================
USER dev
WORKDIR /home/dev

# Homebrew (Linuxbrew) - must be installed as non-root user
RUN NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
ENV PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"

# Oh My Zsh
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

# LazyVim
RUN git clone https://github.com/LazyVim/starter ~/.config/nvim \
    && rm -rf ~/.config/nvim/.git

# Tmux Plugin Manager + Resurrect
RUN git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm

# Create tmux config with resurrect
RUN echo "set -g @plugin 'tmux-plugins/tpm'\n\
set -g @plugin 'tmux-plugins/tmux-sensible'\n\
set -g @plugin 'tmux-plugins/tmux-resurrect'\n\
set -g @plugin 'tmux-plugins/tmux-continuum'\n\
set -g @continuum-restore 'on'\n\
set -g @resurrect-capture-pane-contents 'on'\n\
set -g default-terminal 'screen-256color'\n\
set -g mouse on\n\
run '~/.tmux/plugins/tpm/tpm'" > ~/.tmux.conf

# Setup PATH in zshrc
RUN echo '\n\
# PATH additions\n\
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"\n\
export PATH="/opt/cargo/bin:$PATH"\n\
export PATH="$HOME/.local/bin:$PATH"\n\
export DOTNET_ROOT=/usr/share/dotnet\n\
\n\
# Aliases\n\
alias vim="nvim"\n\
alias ll="ls -la"\n\
alias lg="lazygit"\n\
' >> ~/.zshrc

# Create workspace directory
RUN mkdir -p ~/workspace ~/scripts ~/.ssh
RUN chmod 700 ~/.ssh

# Create mind directory structure
RUN mkdir -p ~/workspace/mind/journal ~/workspace/mind/message_queue ~/workspace/mind/conversations

# Back to root for entrypoint
USER root

# ============================================
# INSTALL TELEGRAM BOT DEPENDENCIES (in venv)
# ============================================
COPY scripts/telegram/requirements.txt /tmp/telegram-requirements.txt
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r /tmp/telegram-requirements.txt \
    && rm /tmp/telegram-requirements.txt
ENV PATH="/opt/venv/bin:$PATH"

# ============================================
# COPY SCRIPTS AND TEMPLATES
# ============================================
COPY scripts/ /opt/scripts/
COPY mind/ /opt/mind-template/

# Copy Claude auth import if exists (for pre-authenticated containers)
COPY .claude-auth-import/ /opt/claude-auth-import/

RUN chmod -R 755 /opt/scripts \
    && chmod +x /opt/scripts/telegram/*.py \
    && chmod +x /opt/scripts/claude/*.sh \
    && ln -s /opt/scripts/telegram/send_message.py /usr/local/bin/send-telegram \
    && ln -s /opt/scripts/claude/session_manager.sh /usr/local/bin/claude-session

# ============================================
# ENTRYPOINT SCRIPT
# ============================================
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 22 80 443

ENTRYPOINT ["/entrypoint.sh"]
