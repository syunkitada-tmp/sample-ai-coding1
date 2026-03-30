# Architecture Design

## 1. Technology Stack

- **Language**: Python 3.12
- **HTTP API**: FastAPI
- **ORM**: SQLAlchemy 2.x
- **DB Migration**: Alembic
- **Database**: MySQL 8.0
- **Worker**: `concurrent.futures.ThreadPoolExecutor`（標準ライブラリ）
- **Config**: pydantic-settings (`BaseSettings`) — `.env` / 環境変数による設定管理
- **Test Framework**:
  - **[必須]** pytest（ユニットテスト）
  - **[オプション]** pytest + httpx（Integration テスト）
- **Others**: Docker Compose（API・Worker・MySQL の独立プロセス管理）

## 2. Directory Structure

```
chatops/
├── src/
│   ├── api/                          # FastAPI アプリケーション
│   │   ├── main.py                   # エントリポイント・ルーター登録
│   │   ├── routers/
│   │   │   └── messages.py           # POST /messages エンドポイント
│   │   ├── schemas/
│   │   │   └── message.py            # Pydantic バリデーションスキーマ
│   │   └── dependencies.py           # DB セッション DI
│   │
│   ├── worker/                       # 非同期ワーカープロセス
│   │   ├── main.py                   # ポーリングループ・ThreadPoolExecutor 管理
│   │   └── executor.py               # ジョブ取り出し・実行・ステータス更新
│   │
│   ├── domain/                       # ビジネスロジック（API / Worker 共用）
│   │   ├── models/
│   │   │   ├── message.py            # SQLAlchemy ORM モデル: messages テーブル
│   │   │   └── job.py                # SQLAlchemy ORM モデル: jobs テーブル
│   │   ├── services/
│   │   │   ├── message_service.py    # メッセージ保存 + コマンド検出 + ジョブ登録（同一トランザクション）
│   │   │   ├── job_service.py        # ジョブ取り出し・ステータス更新・リトライ制御
│   │   │   └── command_parser.py     # コマンド構文解析（!cmd --opt arg）
│   │   └── interfaces/
│   │       └── plugin.py             # プラグインインターフェース定義（ABC）
│   │
│   ├── plugins/                      # プラグインディレクトリ（ファイル追加のみで拡張可能）
│   │   ├── __init__.py
│   │   ├── alert.py                  # ダミーコマンド !alert（リファレンス実装）
│   │   └── help.py                   # ビルトイン !help コマンド
│   │
│   ├── config/                       # 設定管理
│   │   ├── __init__.py               # settings をエクスポート（from src.config import settings）
│   │   └── settings.py               # pydantic-settings BaseSettings（環境変数 / .env 管理）
│   ├── lib/                          # 全レイヤー共通の横断的ユーティリティ
│   │   └── logging.py                # ロギング設定・trace_id 管理（configure_logging / set_trace_id / get_trace_id）
│   └── infrastructure/
│       ├── db.py                     # SQLAlchemy エンジン・セッションファクトリ
│       ├── plugin_loader.py          # plugins/ を自動スキャン・登録
│       └── slack_client.py           # Slack 投稿プロキシ API 呼び出し
│
├── migrations/                       # Alembic マイグレーションファイル
│   ├── env.py
│   ├── versions/
│   └── alembic.ini
│
├── features/                         # BDD 仕様（src/ 構成に対応）
│   ├── api/
│   │   ├── receive_message.feature
│   │   └── receive_message.feature.ja
│   ├── domain/
│   │   ├── persist_and_enqueue.feature(.ja)
│   │   ├── retry.feature(.ja)
│   │   └── plugin_extension.feature(.ja)
│   ├── worker/
│   │   ├── async_worker.feature
│   │   └── async_worker.feature.ja
│   ├── plugins/
│   │   ├── help_command.feature(.ja)
│   │   └── dummy_alert_command.feature(.ja)
│   └── infrastructure/
│       └── structured_logging.feature(.ja)
│
├── tests/
│   ├── unit/                         # pytest ユニットテスト（必須）/ src/ 構成に対応
│   │   ├── api/
│   │   │   └── routers/
│   │   │       └── test_messages.py
│   │   ├── worker/
│   │   │   └── test_executor.py
│   │   ├── domain/
│   │   │   └── services/
│   │   │       ├── test_command_parser.py
│   │   │       ├── test_message_service.py
│   │   │       └── test_job_service.py
│   │   ├── plugins/
│   │   │   ├── test_alert.py
│   │   │   └── test_help.py
│   │   ├── infrastructure/
│   │   │   └── test_plugin_loader.py
│   │   └── lib/
│   │       └── test_logging.py       # configure_logging / set_trace_id / get_trace_id のテスト
│   └── integration/                  # pytest + httpx 統合テスト（オプション）
│       └── api/
│           └── test_messages_api.py
│
├── .env.example                      # 環境変数テンプレート
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.worker
└── pyproject.toml
```

## 3. Implementation Policy

### 設定管理

`src/config/settings.py` に `pydantic-settings` の `BaseSettings` を使用する。
全設定値は環境変数または `.env` ファイルから取得する。
`src/config/__init__.py` で `settings` を再エクスポートすることで、既存コードの `from src.config import settings` は変更不要。

```python
# src/config/settings.py（例）
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    worker_polling_interval: int = 5       # 秒
    worker_max_concurrency: int = 4
    worker_max_retry_count: int = 3
    slack_proxy_url: str
    plugin_dir: str = "src/plugins"

    class Config:
        env_file = ".env"

settings = Settings()
```

### レイヤー分離方針

| レイヤー              | 役割                                         | 依存方向                                        |
| --------------------- | -------------------------------------------- | ----------------------------------------------- |
| `src/api/`            | HTTP リクエスト受付・レスポンス              | → `src/domain/`                                 |
| `src/worker/`         | ポーリング・スレッド管理                     | → `src/domain/`                                 |
| `src/domain/`         | ビジネスロジック・ORM モデル                 | → `src/infrastructure/`（インターフェース経由） |
| `src/infrastructure/` | DB 接続・外部 API 呼び出し・プラグインロード | 外部依存のみ                                    |

- `src/domain/` 層は DB・HTTP に直接依存しない → `pytest` で容易に単体テストが書ける
- `src/infrastructure/` は DI（FastAPI `Depends` / 引数渡し）で差し替え可能

### ジョブキュー（DB キュー）方針

- `SELECT FOR UPDATE SKIP LOCKED` で同時取り出し時の競合を回避する
- ジョブ取り出し → ステータスを `processing` に更新 → 実行 の流れを1トランザクションで行う
- `retry_after` カラム（DATETIME）で遅延リトライを制御する（`retry_after <= NOW()` の条件でポーリング）

### エラーハンドリングの共通ルール

- **コマンド実行失敗**: `job_service` がキャッチし、`retry_count` を加算・`retry_after` を設定して `pending` に戻す
- **リトライ上限超過**: ステータスを `failed` に確定し、Slack スレッドへ最終失敗通知を投稿する
- **プラグインロード失敗**: 起動時にログ出力し、該当プラグインのみスキップして続行する
- **API バリデーションエラー**: FastAPI の Pydantic バリデーションにより自動で HTTP 400 を返す
- **コマンド検出エラー（複数コマンド / 未知コマンド）**: `message_service` 内で検出し、ジョブ登録は行わず API 層から `slack_client` を直接呼び出してエラー通知を Slack スレッドへ投稿する
- **プラグイン引数バリデーションエラー**: プラグインの `execute` が `ValueError` 等を送出した場合は一時障害とみなさず、`retry_count` を加算せずに即座にステータスを `failed` に確定し、Slack スレッドにエラー内容を通知する

### プラグイン設計指針

`src/domain/interfaces/plugin.py` に定義した ABC（抽象基底クラス）に従う。
必須フィールドは `command_name: str`、`description: str`、`execute(args, thread_context) -> str` の3つ。

```python
# src/domain/interfaces/plugin.py（例）
from abc import ABC, abstractmethod

class BasePlugin(ABC):
    command_name: str
    description: str

    @abstractmethod
    def execute(self, args: list[str], thread_context: dict) -> str:
        ...
```

`src/infrastructure/plugin_loader.py` が `src/plugins/` ディレクトリを `importlib` でスキャンし、
`BasePlugin` サブクラスを自動検出・登録する。ファイルを追加するだけで新コマンドとして認識される。
