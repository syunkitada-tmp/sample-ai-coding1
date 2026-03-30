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
