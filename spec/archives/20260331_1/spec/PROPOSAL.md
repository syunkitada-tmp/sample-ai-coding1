# Change Proposal

## 1. Overview

- **Change Type**: New Feature
- **Summary**: Slack プロキシのデバッグ用サーバーを追加する。受信した投稿リクエストを標準出力に印字するだけのシンプルなスタブサービス。
- **Motivation**: ローカル開発・動作確認時に実際の Slack プロキシなしでコマンド実行結果を目視確認できるようにするため。

## 2. Change Description

### 現在の動作

- `api` / `worker` サービスの `SLACK_PROXY_URL` は `.env` で設定された外部 Slack プロキシを向いている。
- ローカル環境では実 Slack プロキシが存在しないため、コマンド実行結果の確認ができない（HTTP エラーが発生する）。

### 変更後の期待動作

- `docker-compose up` 起動時に `slack_proxy_debug` サービスも起動する。
- `api` / `worker` の `SLACK_PROXY_URL` は常に `slack_proxy_debug` へ向く。
- `slack_proxy_debug` サービスは `POST /post` で受け取った JSON ペイロードを標準出力に印字し、`{"ok": true}` を返す。
- `docker-compose logs slack_proxy_debug` でコマンド実行結果を確認できる。

## 3. Impact Analysis

### 影響を受けるファイル

- `tools/slack_proxy_debug.py` — **新規作成**: デバッグサーバー本体（標準ライブラリのみ、FastAPI 不使用）
- `Dockerfile.slack_proxy_debug` — **新規作成**: デバッグサーバー用 Dockerfile
- `docker-compose.yml` — **変更**: `slack_proxy_debug` サービス追加、`api` / `worker` に `SLACK_PROXY_URL` 上書き追記

### 影響を受ける既存機能

- `features/` 内の既存シナリオへの影響なし（既存ロジック変更なし）

### リスク

- `docker-compose.yml` で `SLACK_PROXY_URL` を常に `slack_proxy_debug` に向けるため、実 Slack プロキシへの接続はコンテナ環境では不可。本番向けには別 compose ファイルまたは環境変数の手動上書きが必要。

## 4. Scope

### In Scope

- `tools/slack_proxy_debug.py`: `POST /post` を受け付け、ペイロードを標準出力へ JSON 整形して印字し `{"ok": true}` を返す HTTP サーバー
- `Dockerfile.slack_proxy_debug`: `python:3.12-slim` ベース、`tools/slack_proxy_debug.py` だけをコピーして起動するシンプルな Dockerfile
- `docker-compose.yml`: `slack_proxy_debug` サービス追加（ポート `8081:8081`、`chatops_net` 参加）、`api` / `worker` に `SLACK_PROXY_URL: http://slack_proxy_debug:8081/post` を追記

### Out of Scope

- 実 Slack プロキシへの接続切り替え機構（プロファイル・`docker-compose.override.yml` など）
- デバッグサーバーのテストコード追加
- 既存のユニット / インテグレーションテストの変更
