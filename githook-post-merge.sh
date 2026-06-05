#!/usr/bin/env bash
# Git post-merge hook — automatically restarts the systemd service
# after `git pull` merges new commits.
#
# Install on the server:
#   ln -sf ../../githook-post-merge.sh .git/hooks/post-merge
#   chmod +x .git/hooks/post-merge

set -e

SERVICE_NAME="deepseek-balance-bot"

if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo "[Bot Update] Automatically restarting ${SERVICE_NAME}..."

    if [ "$(id -u)" -eq 0 ]; then
        systemctl restart "$SERVICE_NAME"
    else
        sudo systemctl restart "$SERVICE_NAME"
    fi

    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "[Bot Update] ✅ Service restarted successfully."
    else
        echo "[Bot Update] ⚠️ Automatic restart failed due to permissions."
        echo "   Please restart manually: sudo systemctl restart ${SERVICE_NAME}"
    fi
else
    echo "[Bot Update] 💡 Service is not running."
    echo "   To start the bot: sudo systemctl start ${SERVICE_NAME}"
fi

# Never block git pull — always exit cleanly
exit 0
