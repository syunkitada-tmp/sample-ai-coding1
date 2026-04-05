# Change Proposal

## 1. Overview

- **Change Type**: Refactoring
- **Summary**: `executor.py` におけるレガシーな `BasePlugin` インターフェースのサポートを廃止し、実行モデルをシェルコマンド（`CommandRegistry`）へ一本化します。
- **Motivation**: システムのアーキテクチャを簡素化し、すべてのコマンド実行を `subprocess` によるシェル実行に統一することで、保守性と拡張性を向上させるためです。

## 2. Change Description

### 現在の動作

- `WorkerExecutor` は `PluginLoader` から取得したプラグインが `CommandRegistry` か `BasePlugin` かを判定し、実行パスを分岐しています。
- `BasePlugin`（Python クラスベース）は非推奨（Deprecated）としてマークされていますが、依然として `executor.py` や `PluginLoader` でサポートされています。
- `!help` コマンドなどが `src/plugins/help.py` で `BasePlugin` として実装されています。

### 変更後の期待動作

- `WorkerExecutor` はすべてのコマンドをシェル実行（`CommandRegistry`）として扱います。
- `BasePlugin` および関連する読み込みロジックはシステムから完全に削除されます。
- `!help` コマンドは、PATH 上にある `chatops-help` 実行ファイルを通じて提供されます。

## 3. Impact Analysis

### 影響を受けるファイル

- `src/domain/interfaces/plugin.py` — `BasePlugin` の削除
- `src/infrastructure/plugin_loader.py` — Python クラス読み込み機能（`load_from_dir` 等）の削除
- `src/worker/executor.py` — `_execute_job` からプラグイン形式の分岐を削除、シェル実行へ一本化
- `src/worker/main.py` — 手動での `HelpPlugin` 登録を削除
- `src/plugins/help.py` — ファイル削除
- `tests/unit/infrastructure/test_plugin_loader.py` — `BasePlugin` 前提のテストケース削除
- `tests/unit/worker/test_executor.py` — 実行モックを `CommandRegistry` 前提に修正

### 影響を受ける既存機能

- `features/domain/plugin_extension.feature(.ja)` — 既存のプラグイン拡張仕様がシェルベースに限定される影響を確認
- `features/cmds/help_command.feature(.ja)` — ヘルプコマンドが正常に動作することを確認

### リスク

- **!help コマンド**: `chatops-help` が適切に PATH に配置されていない場合、利用不可となります。
- **レガシー移行**: 万が一、`BasePlugin` を使用している未移行のプラグインがある場合、それらは即座に動作しなくなります。

## 4. Scope

### In Scope

- `executor.py` を含む関連ファイルからのレガシーコード完全一掃
- `CommandRegistry` への実行モデル統一
- テストコードの追随

### Out of Scope

- 新規コマンドの追加
- シェル実行以外の実行方式の検討
- Docker イメージ側の PATH 設定（既存設定を前提とする）
