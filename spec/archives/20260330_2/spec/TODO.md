# Implementation Todo List

## 構造化ログ & trace_id 導入

### 基盤整備（最優先）

- [x] **T1** `src/config/` ディレクトリ化
  - `src/config.py` → `src/config/settings.py` へ移動
  - `src/config/__init__.py` で `settings` を再エクスポート（既存 import 変更不要）

- [x] **T2** `src/config/logging.py` 新規作成
  - `ContextVar[str]` で trace_id を管理（`set_trace_id` / `get_trace_id`）
  - `logging.Filter` サブクラスでファイル名・行番号・trace_id をレコードに注入
  - `configure_logging()` 関数でフォーマット・Filter を一括設定
  - ログフォーマット例: `%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] [trace_id=%(trace_id)s] %(name)s: %(message)s`

- [x] **T3** `src/domain/models/job.py` に `trace_id` カラム追加
  - `trace_id: Mapped[str | None] = mapped_column(String(36), nullable=True)`

- [x] **T4** Alembic マイグレーション作成・適用
  - `uv run alembic revision --autogenerate -m "add_trace_id_to_jobs"`
  - NULLABLE カラムとして追加

### infrastructure 接続（高優先）

- [x] **T5** `src/worker/main.py`
  - `logging.basicConfig(...)` を削除し `configure_logging()` 呼び出しに差し替え

- [x] **T6** `src/api/main.py`
  - `configure_logging()` 呼び出しを追加
  - `@app.middleware("http")` で UUID を生成し `set_trace_id()` → レスポンス後にリセット

- [x] **T7** `src/domain/services/message_service.py`
  - ジョブ登録時に `get_trace_id()` の値を `Job.trace_id` に格納

- [x] **T8** `src/worker/executor.py`
  - `_execute_job` 冒頭で `set_trace_id(job.trace_id or "-")` を呼び出し

### テスト（中優先）

- [x] **T9** `tests/unit/config/test_logging.py` 新規作成
  - `configure_logging()` でフォーマット・Filter が登録されること
  - `set_trace_id` / `get_trace_id` の読み書き
  - コンテキスト未設定時に `"-"` が返ること
  - Filter 適用後のログレコードに `filename`・`lineno`・`trace_id` が入ること

- [x] **T10** `tests/unit/domain/services/test_message_service.py` にテスト追加
  - コマンドジョブ登録時に `job.trace_id` が `get_trace_id()` の値と一致すること

- [x] **T11** `tests/unit/worker/test_executor.py` にテスト追加
  - `_execute_job` 実行後に `get_trace_id()` がジョブの `trace_id` と一致すること
