# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

pueue のタスク完了コールバックを受け取り、Slack Webhook へ通知するスクリプト群。
pueue デーモンが `start.sh {{ id }} {{ result }}` を呼び出し、`watchdog_pueue.py` が `pueue log <id>` を実行して結果を Slack に送信する。

## Architecture

- `start.sh` — pueue の callback として登録するエントリポイント。`.env` を読み込んで `watchdog_pueue.py` を呼び出す
- `watchdog_pueue.py` — `pueue log <id>` を実行し `{"log": "..."}` 形式で Slack Webhook に POST する
- `stop.sh` — 実行中の `watchdog_pueue.py` プロセスを `pkill` で停止する

## Environment Variables

`SLACK_WEBHOOK_URL` が必須。`.env` ファイルに記載する（`.gitignore` 済み）。

## No External Dependencies

標準ライブラリのみ使用（`argparse`, `json`, `os`, `subprocess`, `urllib`）。パッケージインストール不要。
