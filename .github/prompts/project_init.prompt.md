---
description: "プロジェクト初期化の全体ガイド。7 フェーズの概要と進め方を説明します。"
agent: "agent"
argument-hint: "プロジェクトのアイデアや概要を入力してください"
---

# プロジェクト初期化ガイド

プロジェクトのアイデアから実装開始までを **7 つのフェーズ** で段階的に進めます。
各フェーズは個別のプロンプトとして用意されており、開発者と相談しながら 1 フェーズずつ確定していきます。

## フェーズ一覧

| #   | フェーズ                    | プロンプト             | 成果物                                    |
| --- | --------------------------- | ---------------------- | ----------------------------------------- |
| 1   | 要件定義                    | `/project_init_phase1` | `spec/REQUIREMENTS.md`                    |
| 2   | BDD 仕様作成                | `/project_init_phase2` | `features/**/*.feature`, `*.feature.ja`   |
| 3   | アーキテクチャ設計          | `/project_init_phase3` | `spec/ARCH_DESIGN.md`                     |
| 4   | レビュー & 整合性確認       | `/project_init_phase4` | 各成果物の更新                            |
| 5   | タスク計画                  | `/project_init_phase5` | `spec/TODO.md`, `spec/SESSION_CONTEXT.md` |
| 6   | 実装開始 (TDD)              | `/project_init_phase6` | コード + `spec/KNOWLEDGE_BASE.md`         |
| 7   | 全体レビュー & ドキュメント | `/project_init_phase7` | `README.md`                               |

## 進め方

1. **Phase 1 から順番に** 実行してください
2. 各フェーズのプロンプト内で、開発者と対話しながら内容を確定します
3. フェーズ完了時に次のフェーズが提案されるので、準備ができたら進んでください
4. 前のフェーズに戻って修正することも可能です

## まずは Phase 1 から始めましょう

`/project_init_phase1` を実行し、プロジェクトのアイデアを入力してください。
