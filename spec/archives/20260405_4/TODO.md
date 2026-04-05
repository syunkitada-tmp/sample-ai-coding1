# Implementation Tasks

## Phase 1: Core Interface Cleanup
- [x] **[Foundation] `src/domain/interfaces/plugin.py`**: Remove `BasePlugin` abstract base class.
- [x] **[Foundation] `src/infrastructure/plugin_loader.py`**: Cleanup imports and simplify `_registry` type hints.

## Phase 2: Infrastructure Refactoring
- [x] **[Loader] `src/infrastructure/plugin_loader.py`**: Remove legacy loading logic.
- [x] **[Loader] `src/infrastructure/plugin_loader.py`**: Refactor `reload` and `list_commands`.

## Phase 3: Worker Implementation
- [x] **[Executor] `src/worker/executor.py`**: Simplify `_execute_job` to call `_execute_shell` directly for all commands.
- [x] **[Worker] `src/worker/main.py`**: Remove `HelpPlugin` import and manual injection into the registry.
- [x] **[Cleanup] Delete `src/plugins/help.py`**.

## Phase 4: Quality & Tests
- [x] **[TDD] Update `tests/unit/infrastructure/test_plugin_loader.py`**: Remove tests for legacy loading and BasePlugin features.
- [x] **[TDD] Update `tests/unit/worker/test_executor.py`**: Update `_make_plugin_loader` and all test cases to use `CommandRegistry`.
- [x] **[Final Check]**: Run all tests and ensure 100% pass rate for current features.

## Phase 5: Final Cleanup
- [x] **[API] `src/api/dependencies.py`**: Remove legacy `HelpPlugin` reference and injection.
- [x] **[Tests] `tests/integration/test_receive_message.py`**: Update to use `CommandRegistry` mocks.
- [x] **[Cleanup] Delete `tests/unit/plugins/`**.
- [x] **[Cleanup] Delete `src/plugins/`**.

## Phase 6: Review & Documentation
- [x] **[Doc] Update `README.md`**: Remove legacy plugin references and structure.
- [x] **[Review] Quality Review**: Check for dead code and naming consistency.
- [x] **[Final Check]**: Run all tests one last time.
