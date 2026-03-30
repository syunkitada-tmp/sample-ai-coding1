# Change Proposal

## 1. Overview

- **Change Type**: New Feature
- **Summary**: 構造化ログ基盤を導入し、ログにファイル名・行番号と trace_id を付与することでトレーサビリティを向上させる。
- **Motivation**: 現状のログは `%(asctime)s %(levelname)s %(name)s: %(message)s` のみで、ログ出力箇所の特定やリクエスト〜ジョブ実行のフロー追跡が困難。障害調査・性能分析の工数削減のため、構造化ログ基盤が必要。

## 2. Change Description

### 現在の動作

- ログフォーマットにファイル名・行番号が含まれない
- trace_id の概念が存在せず、API 受信からワーカー実行までの処理を横断的に追跡できない
- `logging.basicConfig()` が `worker/main.py` 内のみに記述されており、API プロセスではロギング初期化がない
- `Job` モデルに trace_id カラムがない

### 変更後の期待動作

- すべてのログに `[filename.py:lineno]` と `[trace_id=<uuid>]` が含まれる
  ```
  2026-03-30T10:00:00Z INFO [executor.py:42] [trace_id=a1b2c3d4] src.worker.executor: Job 7 started
  ```
- API がメッセージを受信した時点で UUID を生成し、`contextvars.ContextVar` でプロセス内に伝播
- ジョブ登録時に `Job.trace_id` カラムへ保存し、ワーカーがジョブ取得時に `ContextVar` に復元
- これにより API プロセス ↔ ワーカープロセス を跨いだ同一フローのログを trace_id で串刺し検索できる

## 3. Impact Analysis

### 影響を受けるファイル

| ファイル                                             | 変更内容                                                                                                                                        |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/config/` ディレクトリ新設                       | `src/config.py` → `src/config/settings.py` へ移動。`src/config/__init__.py` で `settings` をエクスポート                                        |
| `src/lib/logging.py`                                 | **新規** — `configure_logging()` / `set_trace_id()` / `get_trace_id()` を集約。`logging.Filter` でファイル名・行番号・trace_id をレコードに注入 |
| `src/domain/models/job.py`                           | `trace_id: Mapped[str \| None]` カラム追加                                                                                                      |
| `migrations/versions/xxxx_add_trace_id_to_jobs.py`   | **新規** — `jobs.trace_id` カラムの Alembic マイグレーション                                                                                    |
| `src/api/main.py`                                    | FastAPI ミドルウェアを追加し、リクエスト受信時に trace_id を生成して `ContextVar` にセット。`configure_logging()` を呼び出す                    |
| `src/domain/services/message_service.py`             | ジョブ登録時に `get_trace_id()` の値を `Job.trace_id` に格納                                                                                    |
| `src/worker/executor.py`                             | ジョブ取得後に `set_trace_id(job.trace_id)` を呼び出してコンテキストを復元                                                                      |
| `src/worker/main.py`                                 | `logging.basicConfig()` を削除し `configure_logging()` に置き換え                                                                               |
| `tests/unit/domain/services/test_message_service.py` | trace_id がジョブに格納されることを確認するテスト追加                                                                                           |
| `tests/unit/worker/test_executor.py`                 | trace_id コンテキスト復元のテスト追加                                                                                                           |

### 影響を受ける既存機能

| feature ファイル                              | 影響                                                                     |
| --------------------------------------------- | ------------------------------------------------------------------------ |
| `features/domain/persist_and_enqueue.feature` | Job 登録シナリオに trace_id の保存が加わるが、既存の振る舞いは変わらない |
| `features/worker/async_worker.feature`        | ジョブ実行フローに trace_id 復元が加わるが、既存の振る舞いは変わらない   |
| その他 feature                                | 直接影響なし                                                             |

### リスク

- **DB マイグレーション**: `trace_id` カラムを `NULLABLE` で追加するため既存レコードへの影響は最小限。ただしマイグレーション未適用の環境でサービスを起動すると ORM 側でカラム不整合が発生する
- **ContextVar とスレッド**: `concurrent.futures.ThreadPoolExecutor` のワーカースレッドは親スレッドの `ContextVar` を**コピーしない**（Python 3.7+ の仕様）。trace_id の復元は `_execute_job` 冒頭で明示的に `set_trace_id()` を呼ぶことで対処する
- **デグレリスク**: ロギング設定の変更により、既存テストやツールがログ出力を文字列比較している場合にフォーマット変更で壊れる可能性がある（現時点では該当テストなし）

## 4. Scope

### In Scope

- `src/config/` ディレクトリの新設（`src/config.py` を `src/config/settings.py` へ移動）
- `src/lib/logging.py` の新規作成（フォーマット・Filter・trace_id 管理）
- `Job.trace_id` カラムの追加と Alembic マイグレーション
- API ミドルウェアでの trace_id 生成
- ワーカーでの trace_id コンテキスト復元
- API・ワーカー両プロセスのロギング初期化統一
- 上記に対応するユニットテスト追加

### Out of Scope

- JSON 形式への変更
- 外部ログ収集基盤（Datadog・Loki 等）との連携設定
- HTTP リクエストヘッダー（`X-Request-ID` 等）による外部 trace_id の受け入れ
- 既存プラグイン（`alert.py`・`help.py`）へのログ追加
