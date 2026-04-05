# Change Proposal

## 1. Overview

- **Change Type**: Refactoring
- **Summary**: `features` ディレクトリの構造をプロジェクトの実際の構造 (`src`, `cmds`, `tools`) に合わせて整理・階層化します。
- **Motivation**: features フォルダ内の構成をプロジェクトのディレクトリ構造と一致させることで、各機能仕様がどのソースコードのコンポーネントに対応するかを明確にするためです。

## 2. Change Description

### 現在の動作

現在、`features/` 直下には `api/`, `domain/`, `worker/`, `infrastructure/`, `plugins/`, `tools/` がフラットに配置されています。このうち一部は `src/` 配下に対応し、`plugins` は実際のコードでは `cmds/` として存在しており、構成の乖離が生じています。

### 変更後の期待動作

プロジェクトの実際のディレクトリ構成に合わせるため、以下のように階層化およびリネームを行います。

- `features/api`, `features/domain`, `features/worker`, `features/infrastructure` を `features/src/` 配下に移動する
- ドキュメントの `features/plugins` をソースコードの命名に合わせて `features/cmds` にリネームする
- `features/tools` は同じ階層のまま維持する

## 3. Impact Analysis

### 影響を受けるファイル

以下のディレクトリツリーが変更されます。

- `features/api/` -> `features/src/api/`
- `features/domain/` -> `features/src/domain/`
- `features/worker/` -> `features/src/worker/`
- `features/infrastructure/` -> `features/src/infrastructure/`
- `features/plugins/` -> `features/cmds/`
- `spec/ARCH_DESIGN.md` -> 記載されている `features/` 配下のディレクトリ構造図を更新

### 影響を受ける既存機能

- `features/` ディレクトリ以下の `.feature` ファイルパス（パスのみで中身は変わりません）

### リスク

- 稼働中のテストコードやCI/CDは現状 `features/` ファイルの特定パスに依存していないため、実体に対する稼働へのリスクは極めて小規模（実質なし）。
- 他のMarkdownドキュメントから該当ファイルへのリンクが切れる可能性があります（ただし、現状でそのようなリンクは見当たりません）。

## 4. Scope

### In Scope

- `features/` ディレクトリ内のサブディレクトリの再配置・リネーム
- `spec/ARCH_DESIGN.md` のファイルツリー構造表記の更新

### Out of Scope

- 実アプリケーションコード（`src/`, `cmds/`, `tools/`, `tests/`）の変更
- `.feature` ファイルの機能シナリオ内容の修正（配置変更のみ）
