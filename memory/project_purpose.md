---
name: project_purpose
description: PueueCallbackBot の目的と仕様概要
type: project
---

pueue（バックグラウンド実行パッケージ）に登録したタスクの完了コールバックとして、Slack Webhook へ通知を送るスクリプトを作るリポジトリ。

**Why:** pueue のタスク完了をSlackでリアルタイムに受け取りたい。

**How to apply:** コールバックスクリプトとして呼び出される想定。Slack Webhook URL はユーザーから後で提供される。pueue がコールバックにどの情報（引数・環境変数）を渡すかは実装前に確認が必要。
