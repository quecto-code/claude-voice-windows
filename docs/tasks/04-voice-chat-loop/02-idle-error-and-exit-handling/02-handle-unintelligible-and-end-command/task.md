---
type: task
title: 聞き取り失敗と終了コマンドを処理する
label: must-have
depends_on:
  - 04-voice-chat-loop/02-idle-error-and-exit-handling/01-handle-silent-and-auto-exit
---

## 背景

親 Story `04-voice-chat-loop/02-idle-error-and-exit-handling` の一部として、status=unintelligible の再発話促しと、終了コマンドのループ離脱を `/voice-chat` の指示に書く（requirements Requirement 6/7）。

親 Story: 04-voice-chat-loop/02-idle-error-and-exit-handling

## 受入条件

- [x] `.claude/commands/voice-chat.md` に「status=unintelligible → 『聞き取れませんでした、もう一度お願いします』を `voice_speak` → 再 listen」の手順がある（Requirement 6）
- [x] 「transcript が終了コマンド（例: 音声モードを終了 / もう終わり）に意味的に該当 → 別れの一言を `voice_speak` しループ離脱」の手順がある（Requirement 7）
- [x] 終了コマンドの判別を Claude の**意味解釈**に委ねる旨が明記されている（サーバ側で特別検出しない）

## 仕様詳細

### 変更ファイル

- `.claude/commands/voice-chat.md` — 「unintelligible 時の挙動 (Requirement 6)」節を追加（再発話促し → 再 listen、silent カウンタと独立、終了判定しない）。終了コマンド節に「サーバは終了を特別検出しない」を追記。ターンループ図・silent 節のプレースホルダ参照を実セクションへ更新
- `tests/test_voice_chat_command.py` — 04/02/02 用の grep テストを追加（unintelligible 節・再発話促し・別経路・ループ継続・終了コマンドの別れ＆離脱・意味解釈・取り違え注意）

### 関数 / API シグネチャ

該当なし（プロンプト記述）

### バリデーション・エラー処理

該当なし

### エッジケース

- 「終わり」を含む通常指示（例「この作業を終わりにして」）と終了コマンドの取り違えに注意する旨を明記

## 依存関係

- 前提: 04-voice-chat-loop/02-idle-error-and-exit-handling/01-handle-silent-and-auto-exit
- ブロックする: なし

理由: 同じコマンド本文の分岐記述なので silent 分岐の後に追記する。

## スコープ外

- 破壊的操作の確認（別 Story）

## 補足

- requirements Requirement 6/7 に対応
- 関連設計:
  - [design.md#相互作用状態エラー方針](../../../../design/design.md#相互作用状態エラー方針)（status=unintelligible の分岐）
  - [design.md#トレーサビリティ](../../../../design/design.md#トレーサビリティ)（FR-6 / FR-7 → プロンプト側）
