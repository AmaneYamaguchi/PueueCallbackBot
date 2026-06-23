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
import socket
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from urllib.error import URLError


def get_webhook_url() -> str:
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        print("Error: SLACK_WEBHOOK_URL is not set", file=sys.stderr)
        sys.exit(1)
    return url


def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return socket.gethostbyname(socket.gethostname())


def get_pueue_log_json(task_id: str) -> dict | None:
    """pueue log --json でタスク詳細を取得する。失敗時は None を返す。"""
    if not task_id.strip():
        return None
    try:
        result = subprocess.run(
            ["pueue", "log", "--json", task_id],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return json.loads(result.stdout).get(task_id)
    except Exception:
        return None


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


def parse_duration(start_str: str | None, end_str: str | None) -> float | None:
    """ISO 8601 の start/end 文字列から実行時間（秒）を計算する。"""
    if not start_str or not end_str:
        return None
    try:
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)
        return round((end - start).total_seconds(), 3)
    except Exception:
        return None


def get_pueue_counts() -> dict:
    """pueue status --json でキュー全体の件数を集計する。失敗時は空dictを返す。"""
    try:
        result = subprocess.run(
            ["pueue", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        tasks = json.loads(result.stdout).get("tasks", {}).values()
    except Exception:
        return {}

    queued = running = success = failed = 0
    for task in tasks:
        status = task.get("status")
        if isinstance(status, dict):
            if "Queued" in status:
                queued += 1
            elif "Running" in status:
                running += 1
            elif "Done" in status:
                done_result = status["Done"].get("result")
                if done_result == "Success":
                    success += 1
                else:
                    failed += 1

    return {
        "queued": queued,
        "running": running,
        "success": success,
        "failed": failed,
        "total": queued + running + success + failed,
    }


def build_payload(task_id: str, result: str) -> dict:
    log_json = get_pueue_log_json(task_id)
    log_text = get_pueue_log(task_id)

    task = log_json.get("task", {}) if log_json else {}

    # start/end/result は task.status.Done の中にある
    status = task.get("status", {})
    done = status.get("Done", {}) if isinstance(status, dict) else {}
    start_str = done.get("start") if isinstance(done, dict) else None
    end_str = done.get("end") if isinstance(done, dict) else None

    # exit_code: Done.result が "Success" なら 0、{"Failed": <code>} なら終了コード
    exit_code: int | None = None
    if isinstance(done, dict):
        done_result = done.get("result")
        if done_result == "Success":
            exit_code = 0
        elif isinstance(done_result, dict):
            failed = done_result.get("Failed")
            if isinstance(failed, int):
                exit_code = failed

    counts = get_pueue_counts()
    payload = {
        "queue_queued": counts.get("queued"),
        "queue_running": counts.get("running"),
        "queue_success": counts.get("success"),
        "queue_failed": counts.get("failed"),
        "queue_total": counts.get("total"),
        "task_id": task_id,
        "result": result,
        "command": task.get("command"),
        "working_dir": task.get("path"),
        "exit_code": exit_code,
        "duration_seconds": parse_duration(start_str, end_str),
        "user": os.environ.get("USER") or os.environ.get("LOGNAME"),
        "hostname": socket.gethostname(),
        "ip": get_local_ip(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "log": log_text,
    }
    return payload


def send_notification(webhook_url: str, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
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
    payload = build_payload(args.id, args.result)
    try:
        send_notification(webhook_url, payload)
    except URLError as e:
        print(f"Error: failed to send Slack notification: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
