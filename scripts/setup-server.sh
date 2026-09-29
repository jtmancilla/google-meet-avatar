#!/usr/bin/env bash
# setup-server.sh — Provision a fresh Ubuntu 24.04 instance for the avatar worker.
#
# Run this ONCE on the server after SSH-ing in:
#   curl -sSL https://raw.githubusercontent.com/jtmancilla/google-meet-avatar/main/scripts/setup-server.sh | bash
#
# Or copy it and run locally:
#   scp scripts/setup-server.sh user@server:~ && ssh user@server 'bash setup-server.sh'

set -euo pipefail

echo "=== 1/4  Installing system packages ==="
sudo apt-get update -qq
sudo apt-get install -y -qq git podman podman-compose
sudo systemctl enable --now podman-restart || true

echo "=== 2/4  Cloning the repository ==="
if [ -d "$HOME/google-meet-avatar" ]; then
    echo "  → repo already exists, pulling latest..."
    git -C "$HOME/google-meet-avatar" pull --ff-only
else
    git clone https://github.com/jtmancilla/google-meet-avatar.git "$HOME/google-meet-avatar"
fi

cd "$HOME/google-meet-avatar"

echo "=== 3/4  Checking .env ==="
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "  [INFO] Created .env from template. Edit it with your API keys:"
    echo "     nano $HOME/google-meet-avatar/.env"
    echo ""
    echo "  Required variables:"
    echo "    LEMONSLICE_API_KEY"
    echo "    LIVEKIT_URL"
    echo "    LIVEKIT_API_KEY"
    echo "    LIVEKIT_API_SECRET"
    echo ""
    echo "  After editing, re-run this script or run:"
    echo "    podman compose up -d --build"
    exit 0
fi

echo "=== 4/4  Building and starting the worker ==="
podman compose up -d --build

echo ""
echo "[OK] Worker is running! Useful commands:"
echo "  podman compose logs -f        # follow logs"
echo "  podman compose restart        # restart after .env changes"
echo "  podman compose down           # stop"
echo "  podman compose up -d --build  # rebuild after code changes"
