# Project Knowledge Base

## 1. Local Development & Testing Tips

- **パッケージ管理**: uv を使用する。`requirements.txt` は不要。依存関係は `pyproject.toml` の `[project].dependencies` と `[dependency-groups].dev` で管理

  ```bash
  # 初回セットアップ
  uv sync --dev
  # テスト実行
  uv run pytest tests/
  # パッケージ追加
  uv add <package>
  uv add --dev <package>
  # Alembic 実行
  uv run alembic upgrade head
  ```

- **SQLite でのユニットテスト**: `tests/conftest.py` の `db_session` フィクスチャが SQLite インメモリ DB を提供する。MySQL が起動していなくてもモデルのユニットテストは実行可能

- **Alembic の `env.py`**: `config.py` の `settings.database_url` を `config.set_main_option()` で注入している。`alembic revision --autogenerate` を実行する前に `DATABASE_URL` 環境変数または `.env` が正しく設定されていること

## 2. Common Errors & Fixes

- **Error**: `ModuleNotFoundError: No module named 'src'`
  **Fix**: `pyproject.toml` に `pythonpath = ["."]` を設定済み。`uv run pytest` をプロジェクトルートから実行すること

- **Error**: `DeprecationWarning: datetime.datetime.utcnow() is deprecated`
  **Fix**: `datetime.now(UTC).replace(tzinfo=None)` を返す `_utcnow()` ヘルパー関数を使い、`mapped_column(default=_utcnow)` で参照する（callable を渡すことで呼び出しごとに評価される）

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

- **`Job.args` の格納形式**: kwargs と位置引数を `json.dumps({"kwargs": parsed.kwargs, "args": parsed.args})` として Text カラムに保存。Worker 側は `json.loads(job.args)` で復元する
