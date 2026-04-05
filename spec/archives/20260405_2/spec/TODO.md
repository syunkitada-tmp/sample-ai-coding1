# TODO: Shell Command Plugin Implementation

**Last Updated**: 2026-04-05  
**Change Proposal**: `spec/PROPOSAL.md`  
**Scope**: Plugin system refactoring from Python class-based to shell command (chatops-\*) format

---

## 📋 Task Phases

### **PHASE A: Plugin Command Implementation** ⭐ (Priority: Highest)

コマンドパッケージとしての alert, help を実装し、PATH から実行可能にする

#### A.1: Create Python Package Structure for cmds/

- **Status**: ✅ Completed
- **Task**: Create directories and **init**.py files
- **Details**:
  - Create `cmds/__init__.py`
  - Create `cmds/lib/__init__.py`
  - Create `cmds/alert/__init__.py`
  - Create `cmds/help/__init__.py`
- **Dependencies**: None
- **Estimated Effort**: 0.5h

#### A.2: Implement cmds/lib/utils.py

- **Status**: ✅ Completed
- **Task**: Create shared utilities for all commands
- **Details**:
  - `parse_args(argv: list[str]) -> dict` — コマンドライン引数をパース
  - `parse_kwargs(argv) -> tuple(kwargs, args)` — --opt value 形式のオプション抽出
  - `output_json(data: dict) -> str` — JSON出力フォーマッティング
  - `output_text(text: str) -> str` — テキスト出力
  - `exit_code()` — 適切な終了コード管理
- **Dependencies**: None
- **Estimated Effort**: 1.5h

#### A.3: Implement cmds/alert/main.py

- **Status**: ✅ Completed
- **Task**: Dummy alert command reference implementation
- **Details**:
  - `main()` エントリポイント関数
  - コマンドライン引数受け取り（`sys.argv[1:]`）
  - `--host` オプション必須チェック
  - JSON/text 出力
  - Exit code 0 (success) / 1 (error)
  - Example output:
    - JSON: `{"result": "Alert for web01"}`
    - Error JSON: `{"error": "--host is required"}`
- **Dependencies**: A.2
- **Estimated Effort**: 1.5h

#### A.4: Implement cmds/help/main.py

- **Status**: ✅ Completed
- **Task**: Help command showing registered chatops-\* commands
- **Details**:
  - PATH から `chatops-*` 実行可能ファイルをスキャン
  - コマンド名と説明の取得（metadata 戦略は TBD）
  - プレーンテキスト出力（！command_name: description）
  - 登録コマンドなしの場合のメッセージ
- **Dependencies**: A.2
- **Estimated Effort**: 2h

#### A.5: Update pyproject.toml with entry_points

- **Status**: ✅ Completed
- **Task**: Register commands as executable scripts via entry_points
- **Details**:
  - Add `[project.scripts]` section:
    ```toml
    chatops-alert = "cmds.alert.main:main"
    chatops-help = "cmds.help.main:main"
    ```
  - Verify `pip install -e .` installs scripts to PATH
- **Dependencies**: A.3, A.4
- **Estimated Effort**: 0.5h

#### A.6: Add unit tests for cmds.lib.utils

- **Status**: ✅ Completed
- **Task**: Unit tests for utility functions
- **Details**:
  - `tests/unit/cmds/lib/test_utils.py`
  - Test parse_args, parse_kwargs, output formatting
  - TDD approach
- **Dependencies**: A.2
- **Estimated Effort**: 2h

#### A.7: Add unit tests for cmds.alert

- **Status**: ✅ Completed
- **Task**: Unit tests for alert command
- **Details**:
  - `tests/unit/cmds/test_alert.py`
  - Mock subprocess execution (integration test is in Phase C)
  - Test --host option validation, JSON output
- **Dependencies**: A.3
- **Estimated Effort**: 1.5h

#### A.8: Add unit tests for cmds.help

- **Status**: ✅ Completed
- **Task**: Unit tests for help command
- **Details**:
  - `tests/unit/cmds/test_help.py`
  - Mock PATH scan, test output format
- **Dependencies**: A.4
- **Estimated Effort**: 1.5h

---

### **PHASE B: Core Infrastructure Updates** (Priority: High)

既存の plugin インターフェース・loader を shell コマンド方式に適応

#### B.1: Refactor src/domain/interfaces/plugin.py

- **Status**: ✅ Completed
- **Task**: Update plugin interface for shell command execution
- **Details**:
  - Keep Python class-based interface placeholder for backward compatibility
  - Define command registry schema:
    ```python
    @dataclass(frozen=True)
    class CommandRegistry:
        command_name: str  # "alert", "help" (without chatops- prefix)
        executable_path: str  # /usr/local/bin/chatops-alert
        description: str  # For help command
    ```
  - Add deprecation note for `BasePlugin`
- **Dependencies**: None
- **Estimated Effort**: 1h

#### B.2: Refactor src/infrastructure/plugin_loader.py

- **Status**: ✅ Completed
- **Task**: Implement PATH-based plugin discovery
- **Details**:
  - Replace directory scan with PATH scan
  - Use `shutil.which()` to find `chatops-*` commands
  - Build command registry (command_name → executable_path mapping)
  - Handle missing commands gracefully (log warning, skip)
  - Load at application startup (API & Worker)
- **Dependencies**: B.1
- **Estimated Effort**: 2.5h

#### B.3: Update src/config/settings.py

- **Status**: ✅ Completed
- **Task**: Add shell command execution settings
- **Details**:
  - `plugin_command_timeout: int = 30` — Subprocess timeout in seconds
  - `plugin_command_path: Optional[str] = None` — Optional PATH override
  - Settings passed to executor
- **Dependencies**: None
- **Estimated Effort**: 0.5h

#### B.4: Refactor src/worker/executor.py

- **Status**: ✅ Completed
- **Task**: Implement subprocess-based command execution
- **Details**:
  - Replace plugin.execute() with subprocess.run()
  - `subprocess.run(['chatops-alert', '--host', 'web01'], capture_output=True, timeout=settings.plugin_command_timeout)`
  - Parse stdout for JSON vs plain text
  - Handle exceptions:
    - TimeoutExpired → temporary error (retry)
    - FileNotFoundError → log & mark failed
    - CalledProcessError (exit code != 0) → check if temporary or permanent
  - JSON parsing:
    - If valid JSON with "error" key → user error (no retry)
    - If valid JSON with "result" or "message" → success
    - If not JSON → plain text output
  - Output to Slack via slack_client
- **Dependencies**: B.1, B.2, B.3
- **Estimated Effort**: 3h

#### B.5: Unit tests for src/infrastructure/plugin_loader.py

- **Status**: ✅ Completed
- **Task**: Test PATH-based plugin discovery
- **Details**:
  - `tests/unit/infrastructure/test_plugin_loader.py`
  - Mock `shutil.which()` to test discovery
  - Test missing command handling
  - Test registry building
- **Dependencies**: B.2
- **Estimated Effort**: 1.5h

#### B.6: Unit tests for src/worker/executor.py

- **Status**: ✅ Completed
- **Task**: Test subprocess execution and output parsing
- **Details**:
  - `tests/unit/worker/test_executor.py`
  - Mock subprocess.run for various scenarios:
    - Success (exit code 0, JSON output)
    - Success (exit code 0, plain text output)
    - Failure (exit code 1, JSON error)
    - Timeout
    - Command not found
  - Test Slack notification via mock
- **Dependencies**: B.4
- **Estimated Effort**: 2.5h

---

### **PHASE C: Integration & Cleanup** (Priority: Medium)

既存テストの削除、あるいは新テストへの置き換え。統合テスト実装

#### C.1: Delete Legacy Python Plugin Tests

- **Status**: ✅ Completed
- **Task**: Remove old tests for Python class-based plugins
- **Details**:
  - Delete `tests/unit/plugins/test_alert.py` (old Python class test)
  - Delete `tests/unit/plugins/test_help.py` (old Python class test)
  - These are replaced by `tests/unit/cmds/test_alert.py`, `tests/unit/cmds/test_help.py`
- **Dependencies**: A.7, A.8 (ensure new tests pass first)
- **Estimated Effort**: 0.5h

#### C.2: Update Existing BDD Feature Compatibility

- **Status**: ✅ Completed
- **Task**: Verify all .feature files work with new implementation
- **Details**:
  - Ensure Step definitions match new subprocess-based flow
  - Update any step definitions that referenced Python plugins
  - Test:
    - `features/domain/plugin_extension.feature` (PATH-based discovery)
    - `features/plugins/dummy_alert_command.feature` (subprocess execution)
    - `features/plugins/help_command.feature` (JSON/text output)
    - `features/domain/persist_and_enqueue.feature` (chatops-\* prefix detection)
    - `features/worker/async_worker.feature` (timeout, retry logic)
- **Dependencies**: B.1, B.2, B.4, A.3, A.4
- **Estimated Effort**: 2h

#### C.3: Integration Test: End-to-End Command Execution

- **Status**: ✅ Completed
- **Task**: Test full flow from message reception to Slack response
- **Details**:
  - `tests/integration/test_command_flow.py`
  - Test:
    1. POST /messages with "!alert --host web01"
    2. Message saved to DB
    3. Job created with status "pending"
    4. Worker picks up job
    5. Calls `chatops-alert --host web01`
    6. Parses output
    7. Sends response to Slack via proxy
  - Use Docker containers or local subprocess mocking
- **Dependencies**: B.4, C.2
- **Estimated Effort**: 3h

#### C.4: Integration Test: Plugin Load at Startup

- **Status**: ✅ Completed
- **Task**: Test plugin discovery on API/Worker startup
- **Details**:
  - `tests/integration/test_plugin_loading.py`
  - Verify `chatops-alert`, `chatops-help` are discovered
  - Verify missing commands are logged (not fatal)
  - Cold start scenario
- **Dependencies**: B.2
- **Estimated Effort**: 1.5h

#### C.5: Update README or CONTRIBUTING for New Plugin Format

- **Status**: ✅ Completed
- **Task**: Document how to add new plugins
- **Details**:
  - Plugin development guide: Python package in `cmds/` with `main.py`
  - Example: `cmds/mycommand/main.py` → entry_point "chatops-mycommand"
  - Expected output format (JSON vs plain text)
  - No breaking changes for users if plugins are external
- **Dependencies**: A.3, A.4
- **Estimated Effort**: 1h

#### C.6: Run Full Test Suite & Address Failures

- **Status**: ✅ Completed
- **Task**: Run pytest on entire codebase
- **Details**:
  - Fix any regressions or broken tests
  - Ensure all Phase A, B tests pass
  - Ensure backward compatibility where applicable
- **Dependencies**: All of Phase A, B, C.1–C.5
- **Estimated Effort**: 2–3h (depends on issues found)

---

## 📊 Task Summary by Phase

| Phase     | Tasks   | Total Effort | Owner | Start | End   |
| --------- | ------- | ------------ | ----- | ----- | ----- |
| **A**     | A.1–A.8 | ~10.5h       | [TBD] | [TBD] | [TBD] |
| **B**     | B.1–B.6 | ~10.5h       | [TBD] | [TBD] | [TBD] |
| **C**     | C.1–C.6 | ~9.5h        | [TBD] | [TBD] | [TBD] |
| **Total** | —       | **~30.5h**   | —     | —     | —     |

---

## 🔗 Dependencies Graph

```
Phase A:
  A.1 → (A.2, A.3, A.4)
  A.2 → A.3, A.4
  A.3 → A.5, A.7
  A.4 → A.5, A.8

Phase B:
  B.1 → B.2, B.4
  B.2 → B.5, B.4
  B.3 → B.4
  B.4 → B.6, C.2, C.3, C.4

Phase C:
  A.7 → C.1 (ensure new tests pass before delete)
  A.8 → C.1
  B.4 → C.2, C.3, C.4
  B.2 → C.4
  C.2 → C.3, C.4
  C.3 → C.6
  C.4 → C.6
  C.1 → C.6
  C.5 → C.6
```

---

## ✅ Completion Criteria

- [x] All Phase A tasks done
- [x] All Phase B tasks done (executor refactor is critical)
- [x] All Phase C tasks done
- [x] Full test suite passes
- [x] No regressions in existing functionality
- [x] `chatops-alert` and `chatops-help` executable from PATH
- [x] BDD feature tests pass
- [x] Developer sign-off on all changes
