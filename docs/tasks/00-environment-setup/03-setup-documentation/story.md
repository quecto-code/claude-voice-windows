---
type: story
title: セットアップ手順を README にまとめる
label: must-have
depends_on:
  - 00-environment-setup/01-local-runtime
  - 00-environment-setup/02-external-services
---

## 背景・目的

新しい環境でクローンして claude-voice を起動するまでに必要な手順（venv 構築・VOICEVOX 起動・vosk モデル DL・MCP サーバ起動）を README に集約する。あわせて、`/task-executor` の push 動作に直結する **git remote の方針** をここで確定し記述する。

## ユーザーストーリー

**As a** 新規環境で claude-voice を立ち上げたい開発者
**I want to** README を読むだけでクローンから起動までの手順を再現したい
**So that** 環境構築の暗黙知に頼らず作業に入れる

## 受入条件

- [ ] プロジェクト直下に `README.md` が存在する
- [ ] README に次の節がすべて含まれる: `## 前提条件` / `## セットアップ` / `## 起動` / `## git remote 方針`
- [ ] `## セットアップ` に「uv で venv 作成」「VOICEVOX Linux 版エンジン DL & 起動」「vosk 日本語モデル DL & `models/` 配置」が手順として書かれている
- [ ] `## 起動` に `python -m claude_voice`（または `.venv/bin/python -m claude_voice`）が起動コマンドとして記載されている
- [ ] `## git remote 方針` に「remote を使う（リモート名と URL）」または「ローカル運用（remote なし）」のどちらかが明記されている
- [ ] README の手順を別環境で踏むと、最後に MCP ハンドシェイクまで到達できる（手動検証）

## 仕様詳細

### UI / 画面

なし（ドキュメント）

### API / Server Action

なし

### データモデル

なし

### バリデーション

- README の必須節が grep で機械検証できる

### エラーハンドリング

該当なし

### エッジケース

- 同名の `README.md` が既にある場合は差分追記でよい（上書きは禁止）

## 依存関係

- 前提（着手前に完了が必要）: `00-environment-setup/01-local-runtime`, `00-environment-setup/02-external-services`
- ブロックする: なし（実装 Epic は Epic 00 全体に依存）

理由: 書く内容（venv 構築・エンジン起動コマンド・モデル配置先）が前提 Story の結果から確定する。

## スコープ外

- 詳細チュートリアル（コマンド例や日本語解説の網羅）
- 外部リンク先の保証（リンク切れ対応）

## 補足

- git remote 方針は task-executor が push できるかに直結するため、本 Story で明示的に確定する
