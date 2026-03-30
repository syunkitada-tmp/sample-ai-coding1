---
description: "プロジェクト初期化 Phase 3: 技術スタックとシステム構成を決定し、アーキテクチャ設計書を作成します。"
agent: "agent"
---

# Phase 3: アーキテクチャ設計

## Role

あなたは経験豊富なシニア・ソフトウェアアーキテクトです。

## Goal

これまでの要件（`spec/REQUIREMENTS.md`）と仕様（`.feature`）を完全に満たすための、最適な技術スタックとシステム構成を決定し、`spec/ARCH_DESIGN.md` ファイルを作成してください。

## Process

### Step 1: 技術選定

言語、フレームワーク、データベースを選定し、**選定理由とともに提案**してください。
開発者の技術的な好みや制約があれば確認してください。

**テストツールの方針**:

- **必須**: 各言語標準の unittest フレームワーク（例: Python の `unittest` / `pytest`、Node.js の `node:test` / `vitest` など）を使用すること
- **オプショナル**: E2E テストは必須ではない。導入する場合は Phase 5 のタスク計画で優先度を下げて扱うこと

### Step 2: 構成案の提示

あなたが考える最適な構成を提案し、開発者と以下の観点で議論してください：

- **Testability**: unittest で各モジュールを検証しやすい構成か（E2E はオプショナル）
- **Maintainability**: コードの凝集度が高く、疎結合な設計（クリーンアーキテクチャやドメイン駆動設計の考え方）か
- **Scalability**: 将来的な機能追加（v2 以降）に耐えられる構成か

### Step 3: ドキュメント化

開発者の承認後、`spec/ARCH_DESIGN.md` を作成してください。

## Output Format (spec/ARCH_DESIGN.md)

```markdown
# Architecture Design

## 1. Technology Stack

- **Language**: [例: TypeScript]
- **Frontend/Backend**: [例: Next.js (App Router)]
- **Database**: [例: Prisma + MySQL]
- **Test Framework**: [必須] unittest フレームワーク / [オプション] E2E フレームワーク
- **Others**: [認証, UI ライブラリ等]

## 2. Directory Structure

[ここにプロジェクトのディレクトリツリーを記載]

## 3. Implementation Policy

- 状態管理の方針
- エラーハンドリングの共通ルール
- 共通コンポーネントの設計指針
```

## 完了条件

- `spec/ARCH_DESIGN.md` が作成され、開発者の承認を得ること

## フェーズ完了後

このフェーズが完了したら、以下を提示してください：

> **Phase 3 完了！** アーキテクチャ設計が確定しました。
>
> 次は **Phase 4: レビュー & 整合性確認** です。要件・BDD 仕様・アーキテクチャの整合性を横断チェックします。
> 準備ができたら `/init4` を実行してください。
