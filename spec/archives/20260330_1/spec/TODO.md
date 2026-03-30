# Implementation Todo List

## P1: 基盤構築（全タスクの前提）

- [x] Setup: プロジェクト初期化 (`pyproject.toml` / `requirements.txt`)
- [x] Setup: Docker Compose 構成 (API / Worker / MySQL)
- [x] Setup: pydantic-settings による `config.py` 実装 (`database_url`, `worker_polling_interval`, `worker_max_concurrency`, `worker_max_retry_count`, `slack_proxy_url`, `plugin_dir`)
- [x] Setup: Alembic 初期化 (`migrations/` ディレクトリ・`env.py`)
- [x] Setup: SQLAlchemy エンジン・セッションファクトリ (`src/infrastructure/db.py`)
- [x] Setup: ORM モデル実装
  - [x] `src/domain/models/message.py` (messages テーブル)
  - [x] `src/domain/models/job.py` (jobs テーブル: status / retry_count / retry_after / args / thread_context)
- [x] Setup: Alembic マイグレーション初回作成・適用（`migrations/versions/6e145104e22a_initial_schema.py`）
- [x] Setup: pytest 環境構築 (`tests/` ディレクトリ・`conftest.py`)

## P2: コアロジック（技術リスクの早期検証）

- [x] Feature: コマンドパーサー (`src/domain/services/command_parser.py`)
  - [x] Scenario: `!cmd --opt val arg` 形式を正しく解析できる
  - [x] Scenario: コマンドが含まれないテキストを判定できる
  - [x] Scenario: 複数コマンドが含まれるテキストを検出できる
- [x] Feature: BasePlugin ABC (`src/domain/interfaces/plugin.py`)
  - [x] `command_name` / `description` / `execute` の抽象インターフェース定義
- [x] Feature: プラグインローダー (`src/infrastructure/plugin_loader.py`)
  - [x] Scenario: Framework discovers a new plugin placed in the plugin directory
  - [x] Scenario: Plugin without a required interface field is rejected at load time
  - [x] Scenario: Removing a plugin file makes the command unavailable after reload
  - [x] Scenario Outline: Plugin interface must define all required fields

## P3: メッセージ受信 API + 永続化・ジョブ登録

- [x] Feature: Slack 投稿プロキシクライアント (`src/infrastructure/slack_client.py`)
- [x] Feature: メッセージサービス (`src/domain/services/message_service.py`)
  - [x] Scenario: Persist a plain message without a command
  - [x] Scenario: Persist a message and enqueue a job for a valid command
  - [x] Scenario: Reject a message containing multiple commands
  - [x] Scenario: Reject a message with an unknown command
  - [x] Scenario: Message save and job registration succeed or fail atomically
- [x] Feature: メッセージ受信 API (`src/api/routers/messages.py`)
  - [x] Scenario: Successfully receive a message with all required fields
  - [x] Scenario Outline: Reject a request with a missing required field
  - [x] Scenario: Reject a request with an empty body
- [x] Feature: FastAPI アプリ起動 (`src/api/main.py`, `src/api/dependencies.py`)

## P4: 非同期ワーカー

- [x] Feature: ジョブサービス (`src/domain/services/job_service.py`)
  - [x] Scenario: Worker picks up a pending job and executes it successfully
  - [x] Scenario: Worker does not pick up a job that is already processing
  - [x] Scenario: Worker respects the configured concurrency limit
- [x] Feature: ワーカー本体 (`src/worker/executor.py`, `src/worker/main.py`)
  - [x] Scenario: Worker executes multiple pending jobs concurrently
  - [x] Scenario: Worker polls again after the configured interval

## P5: リトライ機構

- [x] Feature: リトライ制御 (`src/domain/services/job_service.py` 拡張)
  - [x] Scenario: Failed job is scheduled for retry within the limit
  - [x] Scenario: Failed job is not picked up before retry_after
  - [x] Scenario: Failed job is picked up after retry_after has passed
  - [x] Scenario: Job exceeding the retry limit is marked as failed and notified
  - [x] Scenario Outline: Retry count boundary behaviour

## P6: プラグイン実装

- [x] Feature: `!help` プラグイン (`src/plugins/help.py`)
  - [x] Scenario: Help returns a list of all registered commands
  - [x] Scenario: Help reply format is "!command_name: description" per line
  - [x] Scenario: Help returns a message when no plugins are registered
- [x] Feature: `!alert` ダミープラグイン (`src/plugins/alert.py`)
  - [x] Scenario: Successfully execute !alert with required --host option
  - [x] Scenario: Execute !alert with --host option and positional arguments
  - [x] Scenario: Fail when --host option is missing

## P7: オプション（MVP 完成後）

- [x] Setup: Integration テスト環境構築 (`tests/integration/`)
  - [x] Scenario: API レベルの受信〜ジョブ登録 E2E 検証
- [x] Setup: Docker Compose 本番向け整備 (`Dockerfile.api` / `Dockerfile.worker`)
- [x] Setup: `.env.example` 作成
