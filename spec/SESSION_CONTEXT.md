# Session Context (Last Updated: 2026-03-30)

## 1. Current Status

- **Current Phase**: Phase 6 全タスク完了（MVP + Integration テスト + .env.example）
- **Progress**: 全 P1–P7 完了（Docker Compose 本番整備のみ任意残存）
- **テスト**: 78 passed / 0 failed（unit 72 + integration 6）

## 2. Technical Context

- **アーキテクチャ**: 確定済み (`spec/ARCH_DESIGN.md`)
- **BDD 仕様**: 確定済み (`features/**/*.feature`)
- **確定済み仕様（Phase 2 QA）**:
  - 1メッセージに複数コマンドが含まれる場合 → エラーとして Slack に通知
  - 未知コマンドの場合 → 受信 API 時点でエラーを Slack に即通知
  - メッセージ受信 API の認証 → なし（内部ネットワーク前提）
  - リトライ間隔 → `retry_after` カラムで遅延制御（失敗から一定時間後）
  - `!help` 返信フォーマット → プレーンテキスト（`!コマンド名: 説明` 改行区切り）
  - `!alert` の `--host` オプション → 必須（なければリトライなしで `failed`）

## 3. Technology Stack

| 項目                 | 採用                                        |
| -------------------- | ------------------------------------------- |
| 言語                 | Python 3.12                                 |
| HTTP API             | FastAPI                                     |
| ORM / Migration      | SQLAlchemy 2.x + Alembic                    |
| DB                   | MySQL 8.0                                   |
| Worker               | `concurrent.futures.ThreadPoolExecutor`     |
| 設定管理             | pydantic-settings (`BaseSettings`) / `.env` |
| テスト（必須）       | pytest                                      |
| テスト（オプション） | pytest + httpx（Integration）               |
| コンテナ             | Docker Compose                              |

## 4. Directory Layout

```
src/
  api/         → FastAPI エンドポイント
  worker/      → ポーリングループ・ThreadPoolExecutor
  domain/      → ORM モデル・サービス・プラグイン ABC
  plugins/     → !alert / !help（ファイル追加のみで拡張可）
  infrastructure/ → DB 接続・プラグインローダー・Slack クライアント
features/
  api/         → receive_message
  domain/      → persist_and_enqueue / retry / plugin_extension
  worker/      → async_worker
  plugins/     → help_command / dummy_alert_command
tests/
  unit/        → src/ 構成に対応
  integration/ → オプション
```

## 5. Next Step

- 全タスク完了。残った任意作業:
  - Docker Compose 本番向け整備（マルチステージビルド等）
  - Alembic 初回マイグレーション（MySQL 起動後: `uv run alembic upgrade head`）

## 6. Pending Issues / Notes

- [ ] Alembic の `env.py` で `config.py` の `database_url` を参照する方法を確認する
- [ ] `SELECT FOR UPDATE SKIP LOCKED` が使用する MySQL バージョン（8.0+）を Docker イメージで固定すること
- [ ] `plugin_dir` の値はコンテナ環境では絶対パスが安全か確認する
- [ ] Integration テスト（P7）は MVP 完成後に優先度を再評価する
