#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

LOG="$DIR/balance_bot.log"

# Kill any existing instance
pkill -f "python3.*balance_bot.py" 2>/dev/null || true
sleep 1

# Kill existing tail process (if any from run.sh)
pkill -f "tail.*balance_bot.log" 2>/dev/null || true

# Clear old state so it sends a fresh pinned message
rm -f "$DIR/tg_msg_id.txt"

# Start with -u for unbuffered output
nohup python3 -u balance_bot.py > "$LOG" 2>&1 &

BGPID=$!
echo "Balance bot started, PID: $BGPID"
echo "Log: $LOG"

# Tail the log so you can see startup output
tail -f "$LOG"
