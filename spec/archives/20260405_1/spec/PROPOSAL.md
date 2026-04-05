# Change Proposal

## 1. Overview

- **Change Type**: Refactoring
- **Summary**: `command_parser.py` における位置引数（`args`）の表現方式を、リスト型から文字列型に統一する
- **Motivation**: ChatOps において、テキスト全体をそのまま引数として扱いたい場面が存在するため。文字列化により、空白を含む文章を単一の引数として渡すことが可能になる

## 2. Change Description

### 現在の動作

現在、コマンド `!alert --host web01 foo bar` は以下のようにパースされます：

```python
ParsedCommand(
    name="alert",
    kwargs={"host": "web01"},
    args=["foo", "bar"]  # リスト型
)
```

位置引数（`args`）はリスト型であるため、スペースで区切られた複数個の個別トークンとして扱われます。

### 変更後の期待動作

同じコマンド入力に対して、`args` を文字列として扱うようにします：

```python
ParsedCommand(
    name="alert",
    kwargs={"host": "web01"},
    args="foo bar"  # 文字列型
)
```

これにより、位置引数全体を単一の文字列として扱うことができ、空白や改行を含むテキストをそのまま引数として渡すことが可能になります。

**注記**: `kwargs`（オプション引数）は辞書型のまま変更しません。

## 3. Impact Analysis

### 影響を受けるファイル

#### コア実装

- `src/domain/services/command_parser.py`
  - `ParsedCommand.args` の型定義を `list[str]` → `str` に変更
  - 関連する戻り値を調整

- `src/domain/services/message_service.py`
  - `job.args` に JSON 保存する際、`parsed.args` が文字列になることに対応
  - JSON 構造 `{"kwargs": {...}, "args": "..."}` として保存

- `src/worker/executor.py` (Line 86)
  - JSON 復元時に `parsed.get("args", "")` から文字列を取り出す（デフォルト値は空文字列）
  - プラグイン呼び出し時に `args=...` として文字列を渡す

#### インターフェース・プラグイン

- `src/domain/interfaces/plugin.py`
  - `BasePlugin.execute()` のシグネチャの `args` パラメータ型を `list[str]` → `str` に更新

- `src/plugins/alert.py`
  - `execute()` メソッドの `args: list[str]` → `args: str` に変更
  - `args` の処理ロジック更新：`' '.join(args)` → 既に文字列なので直接使用

- `src/plugins/help.py`
  - `execute()` メソッドの `args: list[str]` → `args: str` に変更
  - このプラグインは `args` を使用していないため、修正は最小限

#### テスト

- `tests/unit/domain/services/test_command_parser.py`
  - 全テストケースの `AssertedCommand.args` の期待値を更新
  - 例: `assert result.args == ["app01"]` → `assert result.args == "app01"`
  - 例: `assert result.args == []` → `assert result.args == ""`

- `tests/unit/domain/services/test_message_service.py`
  - JSON 検証時に `parsed["args"]` が文字列であることを確認するようにテストを更新

- `tests/unit/plugins/test_alert.py`（存在する場合）
  - `args` パラメータが文字列型であることを確認

### 影響を受ける既存機能

- `features/domain/persist_and_enqueue.feature`
  - 仕様上では `args "--host web01"` というテキスト表現のため、実装が変わっても仕様の意図は変わらない
  - ただし、BDD ステップ実装で JSON 検証を行う場合は `args` が文字列型になることを確認する必要あり

- `features/plugins/dummy_alert_command.feature`
  - ダミーアラートコマンドの挙動に変わりなし（`args` が文字列化されるだけ）

### リスク

- **既存機能のデグレ**: **低い**。`args` を文字列化することで、機能が失われるわけではなく、むしろ柔軟性が向上する
- **プラグイン互換性**: **中程度**。既存プラグインインターフェース（`BasePlugin`）のシグネチャが変わるため、外部プラグインの互換性は失われる。ただし、現在ビルトインプラグイン（`alert`, `help`）のみであり、同時に更新するため問題なし
- **テスト更新**: **必須**。テストケースを更新しないと テスト失敗が多く発生するが、更新ロジックは単純で機械的
- **JSON 互換性**: **低い**。DB に保存されたジョブレコードの JSON は新形式になるため、既存レコードは該当リビジョン以降の処理で扱う必要あり

## 4. Scope

### In Scope

- `args: list[str]` → `args: str` への型変更
- コア実装（command_parser, message_service, executor）の修正
- プラグインインターフェース（`BasePlugin.execute()`）の `args` パラメータ型変更
- ビルトインプラグイン（`alert`, `help`）の更新
- ユニットテストの更新

### Out of Scope

- プラグイン開発者向けドキュメント・ガイド更新（Phase 2以降で実施）
- 既存 DB ジョブレコードのマイグレーション（新形式のみ対応で問題ないと判断）
- BDD シナリオの大幅な修正（実装修正で十分）
