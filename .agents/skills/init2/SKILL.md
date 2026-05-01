---
description: "プロジェクト初期化 Phase 2: 要件定義書から BDD 仕様 (.feature) を作成します。"
---

# Phase 2: BDD 仕様作成

## Role

あなたは、BDD（振る舞い駆動開発）と Cucumber/Gherkin 構文のエキスパートです。

## Goal

`spec/REQUIREMENTS.md` の各機能を、Cucumber で実行可能な **`.feature` (英語)** と、その対訳である **`.feature.ja` (日本語翻訳版)** の 2 種類を作成してください。

## Process

### Step 1: 分析と質問

`spec/REQUIREMENTS.md` を読み取り、仕様が曖昧な箇所（バリデーション、エラー条件、遷移先など）があれば、私に質問して仕様を確定させてください。
一度に質問しすぎず、関連するものをまとめて 2〜3 個ずつ確認してください。

### Step 2: 機能ごとにファイル生成

確定した仕様を、機能単位で以下の 2 ファイルセットとして出力してください。
**1 機能ずつ提示し、開発者のレビュー・承認を得てから次の機能に進んでください。**

## Output Rules

1. **[機能名].feature (英語版)**:
   - 全て英語で記述。
   - Keywords: `Feature:`, `Scenario:`, `Given`, `When`, `Then`, `And`, `Scenario Outline:`, `Examples:`
   - そのままテスト実行に使用する「正」のファイルです。

2. **[機能名].feature.ja (日本語翻訳版)**:
   - **Gherkin キーワードのみ英語（そのままで）**、説明文（文章部分）を日本語に翻訳してください。
   - 内容は英語版と 1 対 1 で対応させてください。

## Output Format Example

`features/post_message.feature`

```gherkin
Feature: Post Message
  Scenario: Successfully post progress
    Given I am on the dashboard
    When I enter "Hello"
    Then It should be saved
```

`features/post_message.feature.ja`

```gherkin
Feature: メッセージ投稿機能
  Scenario: 進捗を正常に投稿できる
    Given ダッシュボード画面にいる
    When "こんにちは" と入力する
    Then 保存されること
```

## 完了条件

- 全 Must Have 機能の `.feature` / `.feature.ja` ファイルが作成され、開発者の承認を得ること

## フェーズ完了後

このフェーズが完了したら、以下を提示してください：

> **Phase 2 完了！** BDD 仕様が確定しました。
>
> 次は **Phase 3: アーキテクチャ設計** です。技術スタックとシステム構成を決定します。
> 準備ができたら `@skill init3` を実行してください。
