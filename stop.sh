#!/bin/bash
# stop.sh - 実行中の watchdog_pueue.py プロセスをすべて停止する

if pkill -f "watchdog_pueue.py"; then
    echo "Watchdog stopped."
else
    echo "No watchdog process found."
fi
