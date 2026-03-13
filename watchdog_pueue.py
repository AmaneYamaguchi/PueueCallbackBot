#!/usr/bin/env python3
"""
watchdog_pueue.py - pueue タスク完了時に Slack へ通知するスクリプト

環境変数:
  SLACK_WEBHOOK_URL: 通知先の Slack Webhook URL（必須）

start.sh 経由で pueue コールバックとして呼び出されることを想定。
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from urllib.error import URLError


def get_webhook_url() -> str:
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        print("Error: SLACK_WEBHOOK_URL is not set", file=sys.stderr)
        sys.exit(1)
    return url


def get_pueue_log(task_id: str) -> str:
    if not task_id.strip():
        return "(task ID is empty: cannot retrieve pueue log)"
    try:
        result = subprocess.run(
            ["pueue", "log", task_id],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout or result.stderr
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return f"(failed to retrieve pueue log: {e})"


def send_notification(webhook_url: str, log: str) -> None:
    payload = json.dumps({"log": log}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        status = resp.getcode()
    if status != 200:
        print(f"Warning: Slack returned HTTP {status}", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send pueue task completion notification to Slack"
    )
    parser.add_argument("--id", required=True, help="Task ID")
    parser.add_argument("--result", required=True, help="Task result (e.g. Success, Failed)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    webhook_url = get_webhook_url()
    log = get_pueue_log(args.id)
    try:
        send_notification(webhook_url, log)
    except URLError as e:
        print(f"Error: failed to send Slack notification: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
