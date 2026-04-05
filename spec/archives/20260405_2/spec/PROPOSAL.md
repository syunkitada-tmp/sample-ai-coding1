# Change Proposal

## 1. Overview

- **Change Type**: New Feature
- **Summary**: プラグインの仕組みをshellコマンドベースに変更し、chatops-プレフィックスのコマンドとして提供可能にする。これにより、既存のコマンドラインツールを簡単に統合し、Slackから柔軟に実行できるようにする。
- **Motivation**: 現在のPythonクラスベースのプラグインでは、外部ツールの統合が難しく、拡張性が限定的。shellコマンドベースにすることで、任意の言語やツールをプラグインとして利用可能にし、ユースケース（例: chatops-alert, chatops-silence, chatops-chat, chatops-doc）を容易に実現するため。

## 2. Change Description

### 現在の動作

- プラグインはPythonクラスとして実装され、`BasePlugin`を継承した`execute`メソッドでロジックを実行。
- プラグインは`src/plugins/`ディレクトリにPythonファイルを追加するだけで拡張可能。
- 実行結果は直接Slackに返信される。

### 変更後の期待動作

- プラグインは`chatops-xxx`形式のshellコマンドとして実装（例: `chatops-alert`, `chatops-silence`）。
- ワーカーがジョブ実行時にshellコマンドを呼び出し、標準出力をチェック。
- 出力がJSON形式の場合、構造解析してレスポンスに反映（例: エラーコードや詳細メッセージの抽出）。
- 出力がJSONでない場合、そのままをSlackメッセージとして利用。
- コマンドはPATH経由で実行可能とし、引数を渡す。

## 3. Impact Analysis

### 影響を受けるファイル

- `src/domain/interfaces/plugin.py` — プラグインインターフェースをshellコマンド向けに変更（コマンド名定義をshell実行にシフト）
- `src/infrastructure/plugin_loader.py` — プラグインのロードを PATH スキャン方式に変更（実行環境の PATH から `chatops-*` プレフィックスの実行可能ファイルを検出・登録）
- `src/worker/executor.py` — ジョブ実行ロジックを変更（`subprocess` でshellコマンドを実行し、標準出力を解析）
- `cmds/alert/main.py` および他のコマンドファイル — 既存のPythonクラス実装をPythonスクリプト実装に転換。`pyproject.toml` で entry_points に登録
- `src/config/settings.py` — shellコマンドのPath やタイムアウト設定を追加
- `tests/unit/cmds/test_alert.py` など — テストをshellコマンド実行のモックに更新
- `tests/unit/domain/services/test_command_parser.py` — chatops-プレフィックスの解析を追加
- `pyproject.toml` — `[project.scripts]` entry_points として `chatops-*` コマンズを定義（例: `chatops-alert = 'cmds.alert.main:main'`）

### 影響を受ける既存機能

- `features/plugins/dummy_alert_command.feature` — ダミーコマンド（!alert）の動作をshellコマンド（chatops-alert）ベースに変更。引数渡しと出力解析を反映。
- `features/plugins/help_command.feature` — !helpコマンドの出力にchatops-プレフィックスのコマンド一覧を追加（自動検出）。
- `features/domain/plugin_extension.feature` — プラグイン拡張の仕組みを「ファイル追加のみ」から「shellコマンド追加のみ」に変更。Pythonコード不要。
- `features/domain/persist_and_enqueue.feature` — コマンド検出・ジョブ登録でchatops-プレフィックスを認識するよう更新。
- `features/worker/async_worker.feature` — ワーカー実行でshellコマンドのタイムアウト・エラー処理を追加。

### リスク

- **セキュリティリスク**: shellコマンド実行により、コマンドインジェクションの可能性（引数サニタイズが必要）。PATH経由の実行で悪意あるコマンドの混入リスク。
- **パフォーマンスリスク**: shell実行のオーバーヘッド（プロセス起動コスト）。大量のコマンド実行でワーカーの負荷が増大。
- **互換性リスク**: 既存のPythonプラグインとの互換性なし（移行スクリプトやラッパー実装が必要）。既存ユーザーのプラグインが使えなくなる。
- **エラーハンドリングリスク**: shellコマンドの失敗（exit code != 0）時のリトライ・通知が複雑化。JSONパースエラー時のフォールバック処理。
- **デグレリスク**: 出力フォーマット（JSON/non-JSON）の判定ミスでレスポンスがおかしくなる。既存の!alertなどの動作が変わる。

## 4. Scope

### In Scope

- プラグイン機構の変更（shellコマンドベースへの移行）。
- shellコマンド実行の実装（subprocess利用、標準出力解析）。
- 出力フォーマットの判定とレスポンス反映（JSON解析 / テキストそのまま）。
- 既存プラグインの移行（例: alert.pyをchatops-alertスクリプトに変換）。
- 設定の追加（コマンドパス、タイムアウトなど）。
- テストの更新（shell実行モック）。

### Out of Scope

- セキュリティ強化（コマンドインジェクション対策の詳細実装は別タスク）。
- パフォーマンス最適化（shell実行のキャッシュや並列化）。
- 互換性維持のためのラッパー実装（既存Pythonプラグインのshellラッパー）。
- 新しいプラグインの実装（chatops-silenceなど）。
- 外部ツールの統合検証（例: chatops-docの実装確認）。</content>
  <parameter name="filePath">/home/owner/tmp/sample-ai-coding1/spec/PROPOSAL.md
