#!/bin/bash
# Session setup script for solana-coin-flip
# Runs automatically at the start of each Claude Code cloud session

set -e

echo "==> Setting up solana-coin-flip development environment..."

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "==> Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install Python dependencies
echo "==> Installing Python dependencies..."
cd "$(dirname "$0")/.."
uv sync

echo "==> Setup complete. Run: uv run coinflip"
