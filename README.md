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

## Slack 通知の JSON フィールド一覧

タスク完了時に Slack Webhook へ POST される JSON のフィールド一覧。

| フィールド | 型 | 内容 | 取得元 |
|---|---|---|---|
| `task_id` | string | pueue のタスク ID | `--id` 引数 |
| `result` | string | 完了ステータス（`Success`, `Failed` など） | `--result` 引数 |
| `command` | string \| null | 実行されたコマンド | `pueue log --json` |
| `working_dir` | string \| null | タスク実行時の作業ディレクトリ | `pueue log --json` |
| `exit_code` | integer \| null | プロセスの終了コード（Success=0） | `pueue log --json` |
| `duration_seconds` | float \| null | 実行時間（秒） | `pueue log --json` の start/end から計算 |
| `user` | string \| null | コールバックを実行したユーザ名 | `$USER` 環境変数 |
| `hostname` | string | マシンのホスト名 | `socket.gethostname()` |
| `ip` | string | マシンのローカル IP アドレス | `socket` モジュール（外向き NIC で特定） |
| `timestamp` | string | 通知送信時刻（ISO 8601 UTC） | `datetime.now(UTC)` |
| `log` | string | `pueue log <id>` のテキスト出力 | `pueue log` コマンド |

> `command` / `working_dir` / `exit_code` / `duration_seconds` は `pueue log --json` の取得に失敗した場合 `null` になる。

### 通知 JSON の例

```json
{
  "task_id": "42",
  "result": "Success",
  "command": "python train.py",
  "working_dir": "/home/user/project",
  "exit_code": 0,
  "duration_seconds": 123.456,
  "user": "username",
  "hostname": "my-machine",
  "ip": "192.168.1.10",
  "timestamp": "2026-03-14T12:00:00+00:00",
  "log": "Task 42 [ ...]"
}
```

### フィールドを手動で追加する方法

`watchdog_pueue.py` の `build_payload()` 関数内の `payload` dict にキーを追加するだけで通知 JSON にフィールドを増やせる。

**例1: 環境変数から追加する**

```python
payload = {
    ...
    "my_env_var": os.environ.get("MY_ENV_VAR"),  # 追加
}
```

**例2: シェルコマンドの実行結果を追加する**

```python
def get_gpu_info() -> str | None:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() or None
    except Exception:
        return None

# build_payload() 内
payload = {
    ...
    "gpu": get_gpu_info(),  # 追加
}
```

**例3: `pueue log --json` の追加フィールドを使う**

`pueue log --json` で取得できる `task` dict には `label`（タスクのラベル）や `created_at`（キューへの追加時刻）なども含まれる。

```python
payload = {
    ...
    "label": task.get("label"),       # タスクに付けたラベル
    "created_at": task.get("created_at"),  # キューへの追加時刻
}
```

変数を追加したら `send_notification()` は変更不要。`payload` dict の内容がそのまま JSON として Slack へ送られる。

## 使い方

### watchdog の停止

実行中の watchdog プロセスをすべて停止する:

```bash
./stop.sh
```
