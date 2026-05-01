---
description: "変更完了後に git add & commit を実行します。Conventional Commits 形式でコミットメッセージを生成します。"
---

# Git Commit

## Role

あなたは Git の運用ルールに精通したエンジニアです。

## Goal

変更フロー完了後の成果物を適切にステージングし、Conventional Commits 形式でコミットしてください。

## 事前確認

作業開始前に以下を確認してください：

- `spec/PROPOSAL.md`（存在する場合）または直近の `spec/archives/` 内の PROPOSAL.md
- `spec/TODO.md`（完了タスクの確認）
- `git status`（変更ファイルの一覧）
- `git diff --stat`（変更の規模感）
- `git branch --show-current`（現在のブランチ）

## Process

### Step 0: ブランチの確認

`git branch --show-current` で現在のブランチを確認してください。

**`main` や `master` 等のデフォルトブランチにいる場合**、作業用ブランチを作成してから進めてください：

1. ブランチ名を提案する。命名規則: `<type>/<短い説明>`（例: `feat/add-timeout-to-alert`, `fix/retry-count-off-by-one`, `refactor/extract-config-module`）
2. 開発者の承認を得る
3. `git checkout -b <ブランチ名>` で作成・切り替え

**作業用ブランチに既にいる場合**は、そのまま Step 1 に進んでください。

### Step 1: 変更ファイルの分類

`git status` の結果を以下のグループに分類し、開発者に提示してください：

| グループ     | 対象ファイル例                                         |
| ------------ | ------------------------------------------------------ |
| 仕様         | `spec/*.md`, `features/**/*.feature`                   |
| ソースコード | `src/**`, `alembic/**`                                 |
| テスト       | `tests/**`                                             |
| 設定         | `docker-compose.yml`, `.env.example`, `pyproject.toml` |
| ドキュメント | `README.md`                                            |
| アーカイブ   | `spec/archives/**`                                     |

### Step 2: コミット単位

全変更を 1 コミットにまとめてください。

### Step 3: コミットメッセージの生成

Conventional Commits 形式でメッセージを生成し、**開発者の承認を得てから**コミットしてください。

**フォーマット**:

```
<type>(<scope>): <summary>

<body>

<footer>
```

**type の選択基準**:

| type       | PROPOSAL.md の Change Type |
| ---------- | -------------------------- |
| `feat`     | New Feature                |
| `fix`      | Bug Fix                    |
| `refactor` | Refactoring                |
| `docs`     | ドキュメントのみの変更     |
| `test`     | テストのみの追加・修正     |
| `chore`    | ビルド・設定の変更         |

**scope**: 影響を受ける主要モジュール（例: `api`, `worker`, `plugin`）。省略可。

**body**: 変更の詳細。以下を含める：

- 変更したファイルの概要
- 完了タスク数（`spec/TODO.md` から）

**footer**: `Refs: spec/archives/[YYYYMMDD_N]/` でアーカイブへの参照を付ける。

**例**:

```
feat(plugin): !alertコマンドにタイムアウト処理を追加

- src/plugins/alert.py にタイムアウトロジックを実装
- features/plugins/alert_command.feature にシナリオ追加
- spec/REQUIREMENTS.md を更新
- 完了タスク: 5/5

Refs: spec/archives/20260331_1/
```

### Step 4: ステージング & コミット

開発者の承認後、以下を実行してください：

1. `git add` で対象ファイルをステージング（Step 2 で確定した単位で）
2. `git commit` でコミット（Step 3 で確定したメッセージで）
3. `git log --oneline -1` で結果を確認し、開発者に報告

## 完了条件

- 全変更ファイルがコミットされていること
- `git status` がクリーン（またはコミット対象外のファイルのみ残っている）こと
