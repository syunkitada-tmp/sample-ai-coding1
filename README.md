# ChatOps Framework

Slack チャンネルへの投稿をトリガーに、プラグイン形式で拡張可能なコマンドを非同期で実行し、結果を Slack スレッドへ返す自前 ChatOps 基盤です。SaaS に依存せず、DB をキュー兼ステート管理として一元利用します。

## 機能

- **メッセージ受信 API** — Slack Hook からメッセージ（チャンネル ID・スレッド情報・投稿者・本文）を受け取る HTTP エンドポイント
- **コマンド検出 & ジョブ登録** — `!コマンド名 [--option value] [args]` 形式を解析し、メッセージ永続化と同一トランザクションで DB にジョブを登録
- **非同期ワーカー** — 独立プロセスが DB をポーリングし、`ThreadPoolExecutor` で複数コマンドを並行実行
- **自動リトライ** — 失敗したジョブを設定回数まで自動再試行。上限到達時に Slack スレッドへ最終失敗通知を投稿
- **プラグイン拡張** — `src/plugins/` にファイルを追加するだけで新コマンドとして認識・実行
- **ビルトインコマンド** — `!help`（コマンド一覧返信）を標準搭載
- **サンプルプラグイン** — `!alert --host <host>` を同梱（プラグイン実装のリファレンス）
- **Slack プロキシ デバッグサーバー** — `docker-compose up` 時に自動起動するスタブサーバー。受信ペイロードを標準出力に印字し `{"ok": true}` を返す。`docker-compose logs slack_proxy_debug` でコマンド実行結果を目視確認できる

## 必要条件

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)（パッケージ管理）
- Docker & Docker Compose（MySQL 8.0 を含む本番起動時）

## セットアップ

### 1. 環境変数の設定

```bash
cp .env.example .env
# .env を編集して DATABASE_URL / SLACK_PROXY_URL 等を設定
```

### 2. 依存パッケージのインストール

```bash
uv sync --dev
```

### 3. Docker Compose で起動（推奨）

```bash
docker compose up --build
```

`migrate` サービスが自動的に `alembic upgrade head` を実行してから `api` / `worker` が起動します。

### 4. ローカル起動（MySQL 別途用意）

```bash
# DB マイグレーション
uv run alembic upgrade head

# API サーバー起動
uv run uvicorn src.api.main:app --reload

# ワーカー起動（別ターミナル）
uv run python -m src.worker.main
```

## 使い方

Slack チャンネルで以下の形式でメッセージを送信してください:

```
!コマンド名 [--オプション 値] [引数 ...]
```

### コマンド例

```
!help
!alert --host web01
!alert --host db01 mysql redis
```

メッセージ受信 API に直接リクエストする場合:

```bash
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "C12345",
    "user": "U98765",
    "text": "!alert --host web01",
    "timestamp": "1711234567.000001"
  }'
```

## テスト

```bash
# 全テスト実行
uv run pytest

# 詳細出力
uv run pytest -v
```

88 テスト（ユニット 82 + インテグレーション 6）が含まれます。

## プロジェクト構成

```
src/
├── api/            # FastAPI — POST /messages エンドポイント
├── worker/         # ポーリングループ & ThreadPoolExecutor
├── domain/         # ビジネスロジック（ORM モデル・サービス・プラグイン ABC）
├── plugins/        # プラグインディレクトリ（ファイル追加で拡張）
├── infrastructure/ # DB 接続・Slack クライアント・プラグインローダー
├── config/         # pydantic-settings による設定管理
└── lib/            # 全レイヤー共通ユーティリティ（構造化ログ・ trace_id 管理）

migrations/         # Alembic マイグレーションファイル
features/           # BDD 仕様（.feature ファイル）
tools/
└── slack_proxy_debug.py  # Slack プロキシ デバッグサーバー（開発用スタブ）
tests/
├── unit/           # pytest ユニットテスト
└── integration/    # pytest + httpx インテグレーションテスト
```

## ログ・トレーサビリティ

全ログに出力元ファイル名・行番号と `trace_id` が含まれます。

```
2026-03-30 10:00:00 INFO [executor.py:82] [trace_id=a1b2c3d4-...] src.worker.executor: ...
```

`trace_id` は API リクエスト受信時に自動生成され、`jobs` テーブルの `trace_id` カラム経由でワーカープロセスに引き継がれます。同一 `trace_id` でフィルタリングすることで、メッセージ受信からコマンド実行までのフローを串刺し検索できます。

## 開発ガイド

### プラグインの追加方法

`src/plugins/` に以下のインターフェースを実装したファイルを追加するだけで、次回ワーカー起動時に自動認識されます。

```python
from src.domain.interfaces.plugin import BasePlugin

class MyPlugin(BasePlugin):
    command_name = "mycommand"
    description = "コマンドの説明"

    def execute(
        self,
        kwargs: dict[str, str | bool],
        args: list[str],
        thread_context: dict,
    ) -> str:
        # 実行ロジックを実装して結果文字列を返す
        # リトライ不要の失敗は NoRetryError を raise する
        return "実行結果"
```

実装例は [src/plugins/alert.py](src/plugins/alert.py) を参照してください。

### 設定値

`.env` または環境変数で以下を設定できます:

| 変数名                       | デフォルト                                             | 説明                             |
| ---------------------------- | ------------------------------------------------------ | -------------------------------- |
| `DATABASE_URL`               | `mysql+pymysql://root:password@localhost:3306/chatops` | DB 接続 URL                      |
| `SLACK_PROXY_URL`            | `http://localhost:8081/post`                           | Slack 投稿プロキシ API の URL    |
| `WORKER_POLLING_INTERVAL`    | `5`                                                    | ワーカーのポーリング間隔（秒）   |
| `WORKER_MAX_CONCURRENCY`     | `4`                                                    | 最大同時実行スレッド数           |
| `WORKER_MAX_RETRY_COUNT`     | `3`                                                    | コマンド失敗時の最大リトライ回数 |
| `WORKER_RETRY_DELAY_SECONDS` | `60`                                                   | リトライまでの待機時間（秒）     |
| `PLUGIN_DIR`                 | `src/plugins`                                          | プラグインディレクトリのパス     |
