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

- **Error**: `HelpPlugin.__init__() missing 1 required positional argument: 'plugin_loader'`（plugin_loader の自動スキャン時）
  **Fix**: `register_from_module` でのインスタンス化時に `TypeError` が出た場合はスキップし、手動登録に委ねる。`api/dependencies.py` と `worker/main.py` の両方で `load_from_dir` 後に `plugin_loader._registry["help"] = HelpPlugin(plugin_loader=plugin_loader)` を追記すること

## 3. Implementation Patterns

- **ORM モデルの `default`**: `datetime.now(UTC)` は `default=_utcnow`（callable）として渡す。`default=datetime.now(UTC)` だとモジュール読み込み時の値が固定されてしまうため注意

- **設定の DI**: `src/infrastructure/db.py` のエンジンは `@lru_cache` で遅延初期化。テスト時は `conftest.py` が独自セッションを提供するため DB 接続は発生しない

- **ABC サブクラスのテスト用モック**: `BasePlugin` の ABC サブクラスをテストヘルパーで生成する場合、`execute` をラムダで後付け代入しても `__abstractmethods__` が残るためインスタンス化できない。必ずクラス本体で `def execute(...)` を実装すること

  ```python
  # NG: ラムダ後付け代入はインスタンス化時に TypeError
  DummyPlugin.execute = lambda self, args, ctx: "ok"

  # OK: クラス本体で実装
  class DummyPlugin(BasePlugin):
      def execute(self, args, thread_context):
          return "ok"
  ```

- **トランザクションのロールバック**: `session.commit()` が例外を投げたとき、`session.add()` 済みオブジェクトはセッションのアイデンティティマップ上に残る。後続の `session.query(...).count()` が autoflush で DB に書き込んでしまうため、commit 失敗時には必ず `session.rollback()` を呼ぶこと

  ```python
  try:
      self._db.commit()
  except Exception:
      self._db.rollback()
      raise
  ```

- **respx による httpx モック**: `uv add --dev respx` で導入。`respx_mock` フィクスチャを pytest 引数に追加するだけで使用可能（pytest プラグインとして自動登録）

- **FastAPI テスト用 DI オーバーライド**: `app.dependency_overrides[get_xxx] = lambda: mock` でサービスをモックに差し替えられる。`create_app()` ファクトリ関数を用意して TestClient に渡すとテストごとに独立したアプリインスタンスを取得できる

- **`SELECT FOR UPDATE SKIP LOCKED` の SQLite 互換**: SQLite は SKIP LOCKED を非対応のため例外を投げる。`try/except` で SKIP LOCKED なし版にフォールバックする実装にすることでユニットテストが MySQL なしで通る

- **`Job.args` の Worker 側復元**: `json.loads(job.args)` で `{"kwargs": {...}, "args": "..."}` を取り出し、`plugin.execute(kwargs=..., args=..., thread_context=...)` に渡す

- **`NoRetryError` パターン**: プラグインがリトライ不要の失敗を表現したい場合は `NoRetryError` を raise する。`executor._execute_job()` がこれを捕捉し `job_service.mark_failed_no_retry()` を呼ぶ。`mark_failed()` は呼ばれず retry_count も変化しない

- **コンストラクタ引数が必要なプラグインの登録**: `plugin_loader.load_from_dir()` は引数なしでインスタンス化できるプラグインのみ自動登録する。`HelpPlugin` のように DI が必要なプラグインは `load_from_dir` 後に手動で `_registry` に登録すること（`api/dependencies.py` と `worker/main.py` の両方で行う）

- **構造化ログ / trace_id 管理**: `src/lib/logging.py` に集約。`configure_logging()` を API・Worker 両プロセスの起動時に呼ぶ。`set_trace_id()` / `get_trace_id()` で ContextVar を操作する。`ThreadPoolExecutor` スレッドでは ContextVar が引き継がれないため、`_execute_job` 冒頭で `set_trace_id(job.trace_id or "-")` を明示的に呼ぶこと

- **`configure_logging()` の箆等性**: 重複呼び出し時に `TraceFilter` を持つ既存ハンドラを除去してから再追加するため、何度呼んでも重複ハンドラが増えない

- **`_execute_job` の trace_id リセット**: `try/finally: set_trace_id(None)` でジョブ完了後に必ずリセットすること。リセットなしだと同スレッドで次のジョブが古い trace_id を引き継く

## 4. Phase 5 Lessons: Interface & Implementation Type Changes

- **インターフェース型変更の全体波及**: `BasePlugin.execute()` のシグネチャ（特に `args` パラメータ型）を変更する場合、以下が全てを更新する必要がある：
  1. インターフェース定義（`src/domain/interfaces/plugin.py`）
  2. 全プラグイン実装（`src/plugins/*.py`）
  3. プラグイン呼び出し側（`src/worker/executor.py` など）
  4. テストの期待値とモック（`tests/unit/plugins/*.py`）
  5. JSON シリアライズ/デシリアライズの対応（`src/domain/services/message_service.py`、`src/worker/executor.py`）

  型変更時は単なる find-replace ではなく、**意味的な変換** （例: `list[str]` から `str` への結合）が伴う場合は特に注意が必要

- **JSON フォーマット互換性**: JSON に保存されるデータ型を変更する場合（例: `"args": []` → `"args": ""`）：
  - デフォルト値の設定を JSON 復元時に明示する（`parsed.get("args", "")` など）
  - 既存レコードとの互換性に注意（新フォーマットのみ対応でよいか確認）
- **テストの機械的修正範囲**: `args: list[str]` → `args: str` への修正は機械的に行える：
  - リスト期待値 `["token1", "token2"]` → 文字列 `"token1 token2"`
  - 空リスト `[]` → 空文字列 `""`
  - ただし、**処理ロジックの変更** （例: `' '.join(args)` → `args` 直接使用）は手動での理解が必要

- **テスト実行の重要性**: 型変更後は **必ず全テストを実行** して動作確認を行うこと。
  - Phase 5 では 88/88 テスト PASS で、修正の完全性を確認できた
  - 手動レビューだけでは見落としやすいため、テスト実行が最終的な保険になる
