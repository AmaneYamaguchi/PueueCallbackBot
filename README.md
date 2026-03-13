# PueueCallbackBot

[pueue](https://github.com/Nukesor/pueue) のタスク完了コールバックを受け取り、Slack へ通知を送るスクリプト。

## 概要

pueue に登録したタスクが完了すると、pueue デーモンがコールバックコマンドを実行する。
本リポジトリの `start.sh` をそのコールバックとして設定することで、タスク完了時に `pueue log <id>` の結果が Slack へ通知される。

## pueue コールバック仕様

pueue の設定ファイル（`~/.config/pueue/pueue.yml`）に以下のプレースホルダーが使用できる。

| プレースホルダー | 内容 |
|---|---|
| `{{ id }}` | タスク ID |
| `{{ command }}` | 実行したコマンド |
| `{{ path }}` | 作業ディレクトリ |
| `{{ result }}` | 完了ステータス（`Success`, `Failed` など） |
| `{{ exit_code }}` | プロセスの終了コード |
| `{{ output }}` | 標準出力・標準エラーの末尾 N 行 |
| `{{ start }}` | タスク開始時刻 |
| `{{ end }}` | タスク終了時刻 |

`callback_log_lines` で `{{ output }}` に含める末尾行数を設定できる（デフォルト: 10）。

## セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/AmaneYamaguchi/PueueCallbackBot.git
cd PueueCallbackBot
```

### 2. 環境変数を設定

`.env.example` をコピーして `.env` を作成し、Slack Webhook URL を記入する。

```bash
cp .env.example .env
```

`.env` を編集:

```
SLACK_WEBHOOK_URL=https://hooks.slack.com/triggers/YOUR_WORKSPACE/YOUR_TRIGGER_ID/YOUR_TOKEN
```

> `.env` は `.gitignore` に含まれているためリポジトリにコミットされない。

### 3. pueue の callback を設定

`~/.config/pueue/pueue.yml` を開き、`daemon:` セクションに以下を追記する。

```bash
# Linux
nano ~/.config/pueue/pueue.yml
```

```yaml
daemon:
  callback: "/path/to/PueueCallbackBot/start.sh {{ id }} {{ result }}"
  callback_log_lines: 10
```

`/path/to/PueueCallbackBot` はリポジトリの絶対パスに置き換える（`pwd` で確認）。

> **注意:** `callback:` と `callback_log_lines:` は `daemon:` の直下に記述する。トップレベルに書いても反映されない。

### 4. pueue デーモンを再起動

設定を反映するために再起動が必要。

```bash
pueue shutdown
pueued --daemonize
```

### 5. 動作確認

```bash
pueue add -- ls -la
```

タスクが完了すると Slack に通知が届く。

## 使い方

### watchdog の停止

実行中の watchdog プロセスをすべて停止する:

```bash
./stop.sh
```
