# Session Context: Shell Command Plugin System Implementation

**Date**: 2026-04-05  
**Phase**: Phase 4 (Task Planning) - Transitioning to Phase 5 (TDD Implementation)  
**Conversation**: Selection and planning of implementation tasks based on PROPOSAL.md change analysis

---

## 1. Problem Statement

The ChatOps Framework currently uses a **Python class-based plugin system** (`src/plugins/` with ABC interface). This lacks:

- Clear plugin isolation (all plugins loaded at startup)
- Standard execution semantics (Python environment coupling)
- Easy plugin versioning/updates (in-process reloads problematic)
- Flexibility for non-Python plugin languages

**Solution**: Transition to **PATH-based shell commands** (chatops-\*) built as Python packages in `cmds/` directory with entry_points in pyproject.toml.

---

## 2. Architectural Decisions (Finalized)

### **Directory Structure**

```
cmds/
├── __init__.py
├── lib/
│   ├── __init__.py
│   └── utils.py           # Shared: arg parsing, JSON output, etc.
├── alert/
│   ├── __init__.py
│   └── main.py            # Entry: main()
└── help/
    ├── __init__.py
    └── main.py            # Entry: main()
```

### **Command Format**

- **Command Name**: `chatops-{name}` (e.g., `chatops-alert`)
- **Installation**: Via `pip install -e .` → entry_points create executable scripts
- **Invocation**: `subprocess.run(['chatops-alert', '--host', 'web01'])`
- **Output**:
  - JSON: `{"result": "..."}` or `{"error": "..."}`
  - Plain text: Fallback if not JSON
- **Exit Code**: 0 = success, 1 = failure

### **Key Configuration**

- `plugin_command_timeout: int = 30` — Seconds before subprocess timeout (recoverable)
- `plugin_command_path: Optional[str] = None` — Optional PATH override
- Removed: `plugin_dir` setting (no longer needed with PATH discovery)

### **Execution Model**

```
Message → API /messages endpoint
  ↓
  Message saved to DB
  ↓
  Job created (status: "pending")
  ↓
  Worker picks up job
  ↓
  Executor calls: subprocess.run(['chatops-COMMAND', args...])
  ↓
  Parse stdout (JSON or plain text)
  ↓
  Slack response via proxy
```

---

## 3. Task Prioritization Strategy

**User Preference**: Phase A → Phase B → Phase C (iterate sequentially)

### **Phase A: Command Implementation** (10.5h estimated)

- Create Python packages in `cmds/alert/`, `cmds/help/`
- Implement entry_points in pyproject.toml
- Unit tests for each command
- **Rationale**: Commands are self-contained; early verification of subprocess model viability

### **Phase B: Infrastructure Refactoring** (10.5h estimated)

- Update plugin_loader.py with PATH scanning
- Update executor.py with subprocess execution + output parsing
- Update settings.py with new config keys
- **Rationale**: Depends on Phase A; modifies core execution engine

### **Phase C: Integration & Cleanup** (9.5h estimated)

- Delete old Python class tests
- Update BDD features
- End-to-end integration tests
- **Rationale**: Final validation; depends on A + B working

**Total Effort**: ~30.5 hours

---

## 4. Test Strategy

### **Test Handling for Legacy Code**

**Decision**: Delete Python class-based plugin tests after Phase A+B verification, not during.

- **Phase A**: Write new unit tests for `cmds/lib/utils`, `cmds/alert`, `cmds/help`
- **Phase B**: Write new unit tests for updated `plugin_loader.py`, `executor.py`
- **After Phase B Verification**: Delete old tests in `tests/unit/plugins/`

**Rationale**: Reduces context switching, clearer success criteria before removal.

### **Test Format**

- **Unit Tests**: `tests/unit/{cmds,infrastructure,worker}/`
- **Integration Tests**: `tests/integration/test_command_flow.py`, `test_plugin_loading.py`
- **BDD Features**: `features/domain/`, `features/plugins/`, `features/worker/`

---

## 5. Completed Work (Phases 1–3)

### **Phase 2: Specification Updates** ✅

- Updated `spec/ARCH_DESIGN.md` with complete cmds/ directory structure + plugin guidelines
- Updated `spec/REQUIREMENTS.md` with Python package + entry_points approach
- Updated `spec/PROPOSAL.md` Impact Analysis section
- Updated 7 BDD feature files for subprocess model

### **Phase 3: Consistency Review** ✅

- Validated all specs mention `cmds/` structure (not `src/plugins/`)
- Validated REQUIREMENTS matches ARCH_DESIGN
- Validated PROPOSAL matches implementation targets
- Validated BDD features align with architecture

### **Current Code Status**

- `src/plugins/` exists (contains old Python class plugins: alert.py, help.py)
- `cmds/` does NOT exist (will be created in Phase 5)
- `src/domain/interfaces/plugin.py` exists (ABC, will be deprecated)
- `pyproject.toml` exists (requires entry_points section)

---

## 6. Critical Files Affected (from PROPOSAL.md)

### **Positive (New/Modified)**

- `cmds/alert/main.py` — Dummy alert command ✨ NEW
- `cmds/help/main.py` — Help command scanning PATH ✨ NEW
- `cmds/lib/utils.py` — Shared utilities ✨ NEW
- `pyproject.toml` — Add [project.scripts] entry_points
- `src/infrastructure/plugin_loader.py` — Replace directory scan with PATH scan
- `src/worker/executor.py` — Replace plugin.execute() with subprocess.run()
- `src/config/settings.py` — Add plugin_command_timeout, plugin_command_path
- New unit tests in `tests/unit/{cmds,infrastructure,worker}/`

### **Negative (Removed/Deprecated)**

- `src/plugins/alert.py` — Removed (replaced by cmds/alert/)
- `src/plugins/help.py` — Removed (replaced by cmds/help/)
- `src/domain/interfaces/plugin.py` — Deprecated (ABC no longer used)
- Old tests in `tests/unit/plugins/` — Removed (after Phase B passes)

### **Unchanged**

- API endpoint `POST /messages` — Behavior unchanged
- Message model, Job model, database schema — Unchanged
- Slack integration — Unchanged

---

## 7. Key Assumptions & Constraints

- **Backward Compatibility**: Existing Python plugins cannot coexist; full cutover required
- **Platform Support**: Assumes Unix-like environment (Linux, macOS); PATH semantics apply
- **Python Entry Points**: Uses standard setuptools mechanism (entry_points in pyproject.toml)
- **Error Handling**: Subprocess errors treated as temporary (retry logic) vs permanent (user error in JSON)
- **No Rollback Plan**: Change is one-way; old Python class system will be removed

---

## 8. Known Risks & Mitigation

| Risk                                              | Impact                                        | Mitigation                                                           |
| ------------------------------------------------- | --------------------------------------------- | -------------------------------------------------------------------- |
| Subprocess timeout handling on slow systems       | Job retries may not complete in time          | Make `plugin_command_timeout` configurable; default 30s (reasonable) |
| JSON parsing errors (malformed output)            | Fallback to plain text; unclear user feedback | Standardize output format; document in plugin dev guide              |
| PATH doesn't include chatops-\* commands          | Plugin discovery fails silently               | Log missing commands at startup; fail fast with clear error          |
| Existing installations rely on old Python plugins | Breaking change for users                     | Bump version, document migration path in README                      |

---

## 9. Next Steps (Phase 5 Execution)

**Pending Approval**: This TODO.md and SESSION_CONTEXT.md files

**Once Approved**:

1. Begin Phase A implementation (tasks A.1 → A.8)
2. Use TDD: Write test first, implement, verify
3. After Phase A: Proceed to Phase B
4. After Phase B: Proceed to Phase C cleanup
5. Final verification: All tests pass, all features work

**Phase 5 Progress**:
- ✅ Phase A completed (A.1 - A.8)
- ✅ Phase B completed (B.1 - B.6)
  - Added new settings in `config/settings.py` for subprocess execution timeout and path
  - Refactored `executor.py` to execute commands via `subprocess.run`
  - Added extensive unit tests for shell command execution in executor
- ✅ Phase C completed (C.1 - C.6)
  - Removed legacy python plugins tests
  - Verified BDD spec documentation matches new architecture
  - Added full end-to-end integration tests for command flow and plugin load
  - Updated README.md documentation for the new API plugin format
  - All unit/integration tests running smoothly (104 items)

- ✅ `A.1` completed: `cmds/` package skeleton created
- ✅ `A.2` completed: `cmds/lib/utils.py` implemented with unit tests
- ✅ `A.3` completed: `cmds/alert/main.py` implemented with unit tests
- ✅ `A.4` completed: `cmds/help/main.py` implemented with unit tests
- ✅ `A.5` completed: `pyproject.toml` entry_points added and verified via editable install
- ✅ `A.6` completed: `tests/unit/cmds/lib/test_utils.py` added and verified
- ✅ `A.7` completed: `tests/unit/cmds/test_alert.py` exists and alert command behavior is validated
- ✅ `A.8` completed: `tests/unit/cmds/test_help.py` exists and help command behavior is validated
- ✅ `B.1` completed: `CommandRegistry` added and `BasePlugin` deprecated for backward compatibility
- ✅ `B.2` completed: `PluginLoader` now discovers chatops-\* commands from PATH

**Success Criteria**:

- ✅ Both `chatops-alert` and `chatops-help` executable via PATH
- ✅ All Phase A, B, C tests pass
- ✅ BDD features pass
- ✅ No regressions in existing API/Worker functionality
- ✅ Old Python plugin code fully removed

---

## 10. References

- **PROPOSAL**: `spec/PROPOSAL.md` — Change justification, impact analysis
- **REQUIREMENTS**: `spec/REQUIREMENTS.md` — Functional requirements for new plugin system
- **ARCHITECTURE**: `spec/ARCH_DESIGN.md` — Complete architecture, design guidelines
- **FEATURES**: `features/domain/*.feature`, `features/plugins/*.feature`, `features/worker/*.feature`
- **TASKS**: `spec/TODO.md` — Detailed task breakdown (this session)

---

**Status**: 🟢 **Phase 5 Implementation Complete** — Ready for Phase 6 (Review & Documentation)

Next action: Await `/change6` to handle documentation review.
