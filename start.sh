#!/bin/bash
# start.sh - pueue コールバックから呼び出されるラッパースクリプト
#
# pueue の callback 設定例 (~/.config/pueue/pueue.yml):
#   callback: "/path/to/PueueCallbackBot/start.sh {{ id }} {{ result }}"
#   callback_log_lines: 10

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# .env が存在すれば読み込む
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

TASK_ID="$1"
TASK_RESULT="$2"

python3 "$SCRIPT_DIR/watchdog_pueue.py" --id "$TASK_ID" --result "$TASK_RESULT"
