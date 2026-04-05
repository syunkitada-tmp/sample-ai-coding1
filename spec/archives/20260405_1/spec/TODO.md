# Implementation Todo List

## Phase 4: command_parser.py args 文字列化 — タスク計画

### 優先度順タスク

#### 1. テスト実行確認（最優先）✅ **COMPLETED**

- **内容**: すべてのユニットテストが正常に通ることを確認
- **結果**: ✅ **88/88 PASS**（ユニット: 82, 統合: 6）
- **実行日**: 2026-04-01
- **対象テスト**:
  - ✅ `tests/unit/domain/services/test_command_parser.py` (15 tests) — args 文字列化対応確認
  - ✅ `tests/unit/domain/services/test_message_service.py` (7 tests) — JSON 検証対応確認
  - ✅ `tests/unit/plugins/test_alert.py` (5 tests) — プラグイン実行確認
  - ✅ `tests/unit/plugins/test_help.py` (4 tests) — プラグイン実行確認
  - ✅ `tests/unit/domain/services/test_job_service.py` (9 tests) — リトライ動作確認
  - ✅ `tests/integration/test_receive_message.py` (6 tests) — 統合テスト確認
  - ✅ その他関連ユニットテスト (38 tests)
- **成功条件**: すべてのテストが PASS (Exit Code: 0) ✅
- **オーナー**: Copilot
- **ブロック**: なし（Phase 3 での修正が完全に反映されていることが前提）

#### 2. 統合テスト確認（完了）✅

- **内容**: 統合テストが存在する場合、動作を確認
- **結果**: ✅ `tests/integration/test_receive_message.py` が 6/6 PASS
- **実行日**: 2026-04-05
- **成功条件**: 統合テストが PASS または存在しないことを確認
- **オーナー**: Copilot
- **ブロック**: なし

#### 3. コードレビュー（完了）✅

- **内容**: 修正内容の最終確認と意図確認
- **結果**: ✅ 全テスト 88/88 PASS
- **実行日**: 2026-04-05
- **確認項目**:
  - `args: list[str]` → `args: str` への型変更が全体で一貫しているか
  - JSON 周辺の デフォルト値（`"[]"` → `""` など）が正しいか
  - プラグイン実装の args 処理が正期待通りか
  - テスト内容が実装の意図を正しく反映しているか
- **成功条件**: 修正内容に対する最終承認を得る
- **オーナー**: Copilot
- **ブロック**: なし

---

## 完了した変更（Phase 1〜3）

✅ **仕様更新**:

- `spec/PROPOSAL.md` — 変更提案を文書化
- `spec/ARCH_DESIGN.md` — プラグインインターフェース例を更新

✅ **実装修正**:

- `src/domain/services/command_parser.py` — args を `list[str]` → `str` に変更
- `src/worker/executor.py` — JSON デフォルト値を更新
- `src/domain/interfaces/plugin.py` — BasePlugin.execute() シグネチャを更新
- `src/plugins/alert.py` — execute() 署名と処理ロジックを更新
- `src/plugins/help.py` — execute() 署名を更新

✅ **テスト修正**:

- `tests/unit/domain/services/test_command_parser.py` — args 期待値を文字列化
- `tests/unit/domain/services/test_message_service.py` — JSON 検証を更新
- `tests/unit/plugins/test_alert.py` — メソッド呼び出しと JSON を更新
- `tests/unit/plugins/test_help.py` — メソッド呼び出しを更新
