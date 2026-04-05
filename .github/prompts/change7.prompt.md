---
description: "プロジェクト変更 Phase 7: 完了済みタスクと仕様をアーカイブし、作業環境をクリーンアップします。"
agent: "agent"
---

# Phase 7: アーカイブ & クリーンアップ

## Role

あなたはプロジェクトの構成管理を担当するエンジニアです。

## Goal

現在の完了済みタスクや仕様ファイルを `spec/archives/` にアーカイブし、次のセッションに向けて作業環境をクリーンアップしてください。

## 前提条件

- Phase 6（変更レビュー & ドキュメント更新）が完了していること
- `spec/TODO.md` の全タスクが完了していること

## Process

### Step 1: アーカイブディレクトリの作成

`spec/archives/[YYYYMMDD_N]` ディレクトリを作成してください。

- `YYYYMMDD` は実行日（例: `20260330`）
- `_N` は同日の連番（`_1` から開始、同日に既存アーカイブがあれば次の番号）

### Step 2: ファイルのコピーと移動

以下のファイルをアーカイブディレクトリにコピーしてください（元ファイルは削除しない）：

```
spec/archives/[YYYYMMDD_N]/
  spec/              ← spec/ 配下のファイル（以下を除く）
    - ARCH_DESIGN.md
    - KNOWLEDGE_BASE.md
    - REQUIREMENTS.md
```

以下のファイルはアーカイブディレクトリに**移動**してください（元ファイルを削除）：

```
spec/archives/[YYYYMMDD_N]/
  spec/
    PROPOSAL.md
    SESSION_CONTEXT.md
    TODO.md
```

### Step 3: ARCHIVE_SUMMARY.md の作成

アーカイブディレクトリ内に `ARCHIVE_SUMMARY.md` を作成してください。

```markdown
# Archive Summary

- **Date**: YYYY-MM-DD
- **Archive ID**: YYYYMMDD_N
- **Change Type**: [Bug Fix / New Feature / Refactoring]
- **Proposal**: [PROPOSAL.md の Summary を転記]
- **Completed Tasks**: [完了タスク数] / [全タスク数]

## 主な成果

- [実装した変更の要約]
- [レビュー結果の要約]

## 含まれるファイル

- [アーカイブに含まれるファイル一覧]
```

内容は `spec/TODO.md` から自動生成し、参考情報として PROPOSAL.md と SESSION_CONTEXT.md（両方ともアーカイブに移動済み）の内容も活用してください。

### Step 5: KNOWLEDGE_BASE.md のリファクタリング（続き）

`spec/KNOWLEDGE_BASE.md` はアーカイブせず、次のセッションに引き継ぎます。
ただし、以下の観点でリファクタリングし、**開発者に変更内容を提示して承認を得てください**：

- 解決済みで再発の可能性が低い項目を削除
- 類似の項目を統合・集約
- 古くなった情報を削除
- プロジェクト全体に適用される重要なパターンは残す

### Step 6: 最終確認

アーカイブとクリーンアップの結果を開発者に報告してください：

- アーカイブ先のパスとファイル数
- KNOWLEDGE_BASE.md のリファクタリング内容

## 完了条件

- `spec/archives/[YYYYMMDD_N]` にファイルがアーカイブされていること
- `ARCHIVE_SUMMARY.md` がアーカイブ内に作成されていること
- `KNOWLEDGE_BASE.md` がリファクタリングされ、開発者の承認を得ていること
- `spec/PROPOSAL.md`、`SESSION_CONTEXT.md`、`TODO.md` がアーカイブに移動されていること

## フェーズ完了後

このフェーズが完了したら、以下を提示してください：

> **Phase 7 完了！** アーカイブとクリーンアップが完了しました。
>
> 変更サイクルは全て完了です。
> 次の変更を行う場合は `/change1` から開始してください。
