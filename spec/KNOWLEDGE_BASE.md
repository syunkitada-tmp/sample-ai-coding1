# Project Knowledge Base

## 1. Local Development & Testing Tips

- **パッケージ管理**: uv を使用する。`requirements.txt` は不要。依存関係は `pyproject.toml` の `[project].dependencies` と `[dependency-groups].dev` で管理

  ```bash
  # 初回セットアップ
  uv sync --dev
  # テスト実行
  uv run pytest tests/
  # パッケージ追加（本番依存 / dev 依存）
  uv add <package>
  uv add --dev <package>
  # Alembic マイグレーション（DATABASE_URL または .env が設定されていること）
  uv run alembic revision --autogenerate -m "description"
  uv run alembic upgrade head
  ```

  > **注意**: `httpx` など本番コードで使うパッケージは `[project].dependencies` に入れること。`[dependency-groups].dev` に入れると Docker イメージ（`uv sync --no-dev`）で使えなくなる。

- **SQLite でのテスト（ユニット & インテグレーション）**:
  - ユニットテスト: `tests/conftest.py` の `db_session` フィクスチャが SQLite インメモリ DB を提供。MySQL 不要
  - インテグレーションテスト: `sqlite:///:memory:` は接続ごとに独立した DB になり `no such table` が発生する。`StaticPool` + `check_same_thread: False` で全接続が同一 DB を共有できる

  ```python
  from sqlalchemy.pool import StaticPool
  engine = create_engine(
      "sqlite:///:memory:",
      connect_args={"check_same_thread": False},
      poolclass=StaticPool,
  )
  ```

## 2. Common Errors & Fixes

- **Error**: `ModuleNotFoundError: No module named 'src'`
  **Fix**: `pyproject.toml` に `pythonpath = ["."]` を設定済み。`uv run pytest` をプロジェクトルートから実行すること

- **Error**: Docker コンテナから MySQL に接続できない (`Can't connect to MySQL server on 'localhost'`)
  **Fix**: コンテナ間通信はサービス名（`db`）をホスト名として使う。`docker-compose.yml` の各サービスに `environment.DATABASE_URL: mysql+pymysql://root:password@db:3306/chatops` を追記して `.env` の `localhost` 設定を上書きすること

## 3. Implementation Standards

### シェルコマンドプラグインの実行仕様
シェルコマンド（`chatops-*`）の実行と結果判定は以下のルールに従う。

1. **引数の復元**: `Job.args` (JSON) から `kwargs` と `args` を取り出し、シェルコマンドのオプション（`--key value`）と位置引数に再構築して `subprocess.run` に渡す。
2. **エラー判定 (`NoRetryError`)**: ユーザー起票のエラー（リトライ不要）は、標準出力の JSON 内に `error` キーを含め、exit code >= 1 とすることで表現する。`WorkerExecutor` はこの出力を検知して `mark_failed_no_retry()` を呼ぶ。
3. **出力パース**:
   - JSON 出力内の `result` または `message` キーを優先的に Slack 返信に利用する。
   - JSON 以外、または該当キーがない場合は、標準出力の全テキストをそのまま返信する。
   - 実行タイムアウト、または実行ファイル未踏の場合は `WorkerExecutor` 側で例外を捕捉し、適切に失敗処理を行う。

### 構造化ログとトレーサビリティ
全コンポーネントで一貫したログ出力と `trace_id` の追跡を行う。

1. **初期化**: API・Worker ともに、プロセス起動時に `configure_logging()` を一度だけ呼び出し、ログハンドラをセットアップする。
2. **`trace_id` の伝搬**: `set_trace_id()` / `get_trace_id()` (ContextVar) を使用する。
   - **重要**: `ThreadPoolExecutor` の別スレッドでは ContextVar が自動で引き継がれない。そのため、`WorkerExecutor._execute_job` の冒頭で `set_trace_id(job.trace_id or "-")` を明示的に呼ぶ必要がある。
3. **リセットの徹底**: `_execute_job` では `try/finally` ブロックを用いて、完了時に必ず `set_trace_id(None)` を呼び出し、スレッドのコンテキストをクリーンに保つ。

### DB トランザクション
MySQL および SQLite (SKIP LOCKED 非対応) の両方で動作を保証する。

1. **ロールバック**: `session.commit()` 失敗時は必ず `session.rollback()` を呼ぶ（アイデンティティマップ上の不整合を防ぐため）。
2. **SKIP LOCKED 互換**: SQLite は `SKIP LOCKED` をサポートしないため、例外捕捉時にフォールバック実装を用いることでユニットテストを MySQL なしで継続可能にする。
