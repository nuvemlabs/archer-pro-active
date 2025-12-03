#!/bin/bash
#
# Import Claude Authentication from Host
#
# This script copies Claude authentication from the host machine
# to be used during container initialization.
#
# Run this BEFORE building the Docker image:
#   ./scripts/import-claude-auth.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
IMPORT_DIR="$PROJECT_ROOT/.claude-auth-import"

# Possible locations for Claude auth on the host
CLAUDE_LOCATIONS=(
    "$HOME/.claude"
    "/home/$(whoami)/.claude"
)

echo "=========================================="
echo "Claude Authentication Import"
echo "=========================================="
echo ""

# Find Claude authentication on host
FOUND_AUTH=""
for LOCATION in "${CLAUDE_LOCATIONS[@]}"; do
    # Check for Claude Code authentication file (.credentials.json)
    if [ -f "$LOCATION/.credentials.json" ]; then
        FOUND_AUTH="$LOCATION"
        break
    fi
done

if [ -z "$FOUND_AUTH" ]; then
    echo "❌ No Claude directory found on host"
    echo ""
    echo "Checked locations:"
    for LOCATION in "${CLAUDE_LOCATIONS[@]}"; do
        echo "  - $LOCATION"
    done
    echo ""
    echo "You'll need to authenticate Claude after container starts:"
    echo "  docker exec -it -u dev claude-dev-env claude"
    echo ""
    exit 0
fi

echo "✅ Found Claude directory at: $FOUND_AUTH"
echo ""
echo "Files found:"
ls -la "$FOUND_AUTH" | head -10
echo ""

# Create import directory
echo "Creating import directory: $IMPORT_DIR"
mkdir -p "$IMPORT_DIR"

# Copy essential files for authentication and configuration
echo "Copying authentication and configuration files..."

# Critical authentication file
if [ -f "$FOUND_AUTH/.credentials.json" ]; then
    cp "$FOUND_AUTH/.credentials.json" "$IMPORT_DIR/"
    echo "  ✓ .credentials.json (authentication)"
fi

# Settings and configuration
for file in settings.json settings.local.json; do
    if [ -f "$FOUND_AUTH/$file" ]; then
        cp "$FOUND_AUTH/$file" "$IMPORT_DIR/"
        echo "  ✓ $file"
    fi
done

# User customization files
for file in CLAUDE.md AGENT_HANDOVER_PROMPT.md ITERATIVE_WORKFLOW.md; do
    if [ -f "$FOUND_AUTH/$file" ]; then
        cp "$FOUND_AUTH/$file" "$IMPORT_DIR/"
        echo "  ✓ $file"
    fi
done

# User plugins and skills (if they exist)
for dir in plugins skills; do
    if [ -d "$FOUND_AUTH/$dir" ]; then
        cp -r "$FOUND_AUTH/$dir" "$IMPORT_DIR/"
        echo "  ✓ $dir/ directory"
    fi
done

echo ""
echo "Skipping container-specific files:"
echo "  - history.jsonl (can be large)"
echo "  - projects/, session-env/, debug/, file-history/"
echo "  - todos/, plans/, shell-snapshots/"
echo ""

# Fix permissions - make everything readable
echo "Fixing permissions..."
find "$IMPORT_DIR" -type f -exec chmod 644 {} \; 2>/dev/null || true
find "$IMPORT_DIR" -type d -exec chmod 755 {} \; 2>/dev/null || true
chmod 600 "$IMPORT_DIR/.credentials.json" 2>/dev/null || true
echo "  ✓ Permissions fixed"

echo ""
echo "✅ Claude authentication copied successfully"
echo ""
echo "Files copied:"
ls -la "$IMPORT_DIR"
echo ""
echo "Next steps:"
echo "  1. Build the Docker image: docker compose build"
echo "  2. Start the container: docker compose up -d"
echo "  3. Claude will be pre-authenticated!"
echo ""
echo "Note: This imported auth will be used to initialize the"
echo "      'archer-claude-auth' volume on first container start."
echo ""
