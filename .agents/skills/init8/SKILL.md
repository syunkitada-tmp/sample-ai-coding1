---
description: "プロジェクト初期化 Phase 8: 完了済みタスクと仕様をアーカイブし、作業環境をクリーンアップします。"
---

# Phase 8: アーカイブ & クリーンアップ

## Role

あなたはプロジェクトの構成管理を担当するエンジニアです。

## Goal

現在の完了済みタスクや仕様ファイルを `spec/archives/` にアーカイブし、次のセッションに向けて作業環境をクリーンアップしてください。

## 前提条件

- Phase 7（全体レビュー & ドキュメント整備）が完了していること
- `spec/TODO.md` の全タスクが完了していること

## Process

### Step 1: アーカイブディレクトリの作成

`spec/archives/[YYYYMMDD_N]` ディレクトリを作成してください。

- `YYYYMMDD` は実行日（例: `20260330`）
- `_N` は同日の連番（`_1` から開始、同日に既存アーカイブがあれば次の番号）

### Step 2: ファイルのコピー

以下のファイルをアーカイブディレクトリにコピーしてください（元ファイルはこの時点では削除しない）：

```
spec/archives/[YYYYMMDD_N]/
  features/          ← features/ ディレクトリ全体のコピー
  spec/              ← spec/ 配下のファイル（archives/ ディレクトリを除く）
```

### Step 3: ARCHIVE_SUMMARY.md の作成

アーカイブディレクトリ内に `ARCHIVE_SUMMARY.md` を作成してください。

```markdown
# Archive Summary

- **Date**: YYYY-MM-DD
- **Archive ID**: YYYYMMDD_N
- **Completed Tasks**: [完了タスク数] / [全タスク数]

## 主な成果

- [Phase 6 で実装した主要機能の要約]
- [Phase 7 のレビュー結果の要約]

## 含まれるファイル

- [アーカイブに含まれるファイル一覧]
```

内容は `spec/TODO.md` と `spec/SESSION_CONTEXT.md` から自動生成してください。

### Step 4: KNOWLEDGE_BASE.md のリファクタリング

`spec/KNOWLEDGE_BASE.md` はアーカイブせず、次のセッションに引き継ぎます。
ただし、以下の観点でリファクタリングし、**開発者に変更内容を提示して承認を得てください**：

- 解決済みで再発の可能性が低い項目を削除
- 類似の項目を統合・集約
- 古くなった情報（バージョン固有の問題など）を削除
- プロジェクト全体に適用される重要なパターンは残す

### Step 5: TODO.md のクリーンアップ

完了タスク（`[x]`）を全て削除し、未着手・進行中のタスクのみ残してください。
全タスクが完了している場合は、空のテンプレートにリセットしてください：

```markdown
# Implementation Todo List

（タスクなし）
```

### Step 6: SESSION_CONTEXT.md のリセット

SESSION_CONTEXT.md を以下の最小テンプレートにリセットしてください：

```markdown
# Session Context (Last Updated: YYYY-MM-DD)

## 1. Current Status

- **Current Phase**: Phase 8 完了（次のイテレーション待ち）
- **Progress**: 0 / 0

## 2. Next Step

- 次に着手すべきこと: [未定]

## 3. Pending Issues / Notes

- [なし]
```

### Step 7: 最終確認

アーカイブとクリーンアップの結果を開発者に報告してください：

- アーカイブ先のパスとファイル数
- KNOWLEDGE_BASE.md のリファクタリング内容
- クリーンアップ後の TODO.md / SESSION_CONTEXT.md の状態

## 完了条件

- `spec/archives/[YYYYMMDD_N]` にファイルがアーカイブされていること
- `ARCHIVE_SUMMARY.md` がアーカイブ内に作成されていること
- `KNOWLEDGE_BASE.md` がリファクタリングされ、開発者の承認を得ていること
- `TODO.md` から完了タスクが削除されていること
- `SESSION_CONTEXT.md` が最小テンプレートにリセットされていること

## フェーズ完了後

このフェーズが完了したら、以下を提示してください：

> **Phase 8 完了！** アーカイブとクリーンアップが完了しました。
>
> プロジェクトの初期化サイクルは全て完了です。
> 次のイテレーションを開始する場合は、必要なフェーズから再開してください：
>
> - 新機能の追加: `@skill init1` から要件定義
> - 既存機能の改修: `@skill init5` からタスク計画
> - 即座に実装: `@skill init6` で TDD 開始
