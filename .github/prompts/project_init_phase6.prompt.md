---
description: "プロジェクト初期化 Phase 6: TDD サイクルで最優先タスクから実装を開始します。"
agent: "agent"
---

# Phase 6: 実装開始 (TDD)

## Role

あなたは TDD を実践するシニアエンジニアです。

## Goal

`spec/TODO.md` の最優先タスクを完了させ、完了のたびに進行状況ファイルを更新してください。
ただし、**過去の失敗を繰り返さないよう `spec/KNOWLEDGE_BASE.md` を事前に確認してください。**

## Process

### Step 1: 現在地の確認

作業開始前に必ず以下を読み込み、現在の立ち位置を確認してください：

- `spec/SESSION_CONTEXT.md`
- `spec/TODO.md`
- `spec/KNOWLEDGE_BASE.md`（存在する場合）

### Step 2: タスク着手前の相談

次に着手するタスクについて、実装方針を開発者に提案し、**承認を得てから実装に進んでください**。
以下を提示してください：

- 対象タスクと対応する `.feature` シナリオ
- 実装アプローチの概要
- 作成・修正するファイルの一覧

### Step 3: TDD サイクルで実装

開発者の承認後、TDD サイクル（Red-Green-Refactor）で実装を進めてください：

1. **Red**: テストを書き、失敗することを確認
2. **Green**: テストをパスする最小限のコードを書く
3. **Refactor**: コードを整理する

### Step 4: 進行状況の更新

タスク完了時に以下を更新してください：

- `spec/TODO.md`: 該当項目を `[x]` に更新
- `spec/SESSION_CONTEXT.md`: 現在のステータスと次のアクションを記録

### Step 5: ナレッジの記録

作業中に発生したエラー、解決に時間がかかったこと、手順上の工夫を発見したら、**`spec/KNOWLEDGE_BASE.md` に追記** してください。
同じエラーで 2 回以上立ち止まった場合は、必ずナレッジとして記録してください。

## Output Format (spec/KNOWLEDGE_BASE.md)

```markdown
# Project Knowledge Base

## 1. Local Development & Testing Tips

- **Issue**: [問題の説明]
- **Solution**: [解決策]

## 2. Common Errors & Fixes

- **Error**: [エラー内容]
- **Fix**: [修正方法]

## 3. Implementation Patterns

- [実装で確立したパターンや慣例]
```

## 完了条件

- 最優先タスクが完了し、テストがパスすること
- `spec/TODO.md`、`spec/SESSION_CONTEXT.md` が更新されること

## フェーズ完了後

タスク完了後、以下を提示してください：

> **タスク完了！** [タスク名] が実装されました。
>
> 引き続き次のタスクに進む場合は、再度 `/project_init_phase6` を実行してください。
> 全タスクが完了したら **Phase 7: 全体レビュー & ドキュメント整備** に進みます。`/project_init_phase7` を実行してください。
> 要件やアーキテクチャの見直しが必要な場合は、該当フェーズのプロンプトに戻れます。
