---
type: task
title: voice-chat スラッシュコマンドを作る
label: must-have
depends_on: []
---

## 背景

親 Story `04-voice-chat-loop/01-voice-chat-command-and-loop` の一部として、音声モードを起動する `/voice-chat` コマンドの器（ファイル）を作る。

親 Story: 04-voice-chat-loop/01-voice-chat-command-and-loop

## 受入条件

- [x] `.claude/commands/voice-chat.md` が存在する → `Path("..").is_file()` で確認
- [x] コマンド本文に「音声モードに入る」旨と、最初に `voice_speak` で開始を告げてから `voice_listen` を呼ぶ手順の骨格が書かれている → 「音声モード」「voice_speak」「開始」「voice_listen」を grep + `voice_speak` の最初の出現位置が `voice_listen` より前であることを検証
- [x] Claude Code で `/voice-chat` が候補に表示され、実行できる → 直近のシステム情報内 skill 一覧に `voice-chat: ハンズフリーの音声対話モードに入る (claude-voice MCP)` が出現。frontmatter description が候補表示に使われていることを確認
- [ ] 実行すると `voice_listen` まで到達する（次タスクで詳細を詰める）→ **手動検証**: 実マイク + VOICEVOX が必要、かつ詳細ループは次タスク 02-define-turn-loop-and-speak-roles で書き込んでから本実行確認するのが筋。本タスクの骨格コマンドからは voice_speak 開始告知 → voice_listen 第 1 ターン到達まで読める

## 仕様詳細

### 変更ファイル

- `.claude/commands/voice-chat.md`（新規・スラッシュコマンドの器）
- `tests/test_voice_chat_command.py`（新規・ファイル存在 + 必須キーワード grep + voice_speak が voice_listen より前 + frontmatter description の検証 7 件）
- `docs/tasks/.../task.md`（受入条件チェック）
- `docs/tasks/STATUS.md`（13/17）

コマンド本文の骨格:
- frontmatter `description: ハンズフリーの音声対話モードに入る (claude-voice MCP)`
- 前提条件 (claude-voice MCP / VOICEVOX エンジン / マイク / vosk モデル)
- 起動手順の 3 段: voice_speak 開始告知 → voice_listen 第 1 ターン → status 分岐 (詳細は次タスク)
- 設計メモ (design 設計判断 1 / 5 と ADR-0001 への参照)
- pytest 7 件 + 全体 101 件 pass + 1 skip

### 関数 / API シグネチャ

該当なし（スラッシュコマンド定義 = プロンプト）

### バリデーション・エラー処理

該当なし

### エッジケース

- VOICEVOX エンジン未起動の場合の前提条件を本文に注記するか検討

## 依存関係

- 前提: なし
- ブロックする: 04-voice-chat-loop/01-voice-chat-command-and-loop/02-define-turn-loop-and-speak-roles

理由: 器を作ってからループ手順を書き込む。

## スコープ外

- ループ手順・3 役割の詳細記述（次タスク）

## 補足

- 起動は手動（ホットワードなし、[requirements Out of Scope]）
- 関連設計:
  - [design.md#全体像](../../../../design/design.md#全体像)
  - [design.md 設計判断 5（3 役割をサーバに置かない）](../../../../design/design.md#主要な設計判断とその理由)
