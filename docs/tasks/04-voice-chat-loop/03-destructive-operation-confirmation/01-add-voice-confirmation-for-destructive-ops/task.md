---
type: task
title: 破壊的操作の音声確認を組み込む
label: must-have
depends_on: []
---

## 背景

親 Story `04-voice-chat-loop/03-destructive-operation-confirmation` の一部として、`/voice-chat` の指示に破壊的操作の音声確認フローを追記する（[ADR-0002](../../../../adr/0002-skip-permissions-with-voice-confirmation.md)、[design.md 設計判断 6](../../../../design/design.md#主要な設計判断とその理由)）。

親 Story: 04-voice-chat-loop/03-destructive-operation-confirmation

## 受入条件

- [x] `.claude/commands/voice-chat.md` に「破壊的・不可逆操作の直前に、許可要求を `voice_speak` し `voice_listen` で返事を待つ（ブロッキング）」手順が明記されている
- [x] 「肯定（はい等）でのみ実行、否定・不明瞭なら実行しない」が明記されている
- [x] 破壊的操作の例示（ファイル削除・上書き・`git push --force`・`git reset --hard` 等）が列挙されている
- [x] 線引きは使いながら調整する前提（固定仕様でない）が明記されている

## 仕様詳細

### 変更ファイル

- `.claude/commands/voice-chat.md` — 「破壊的操作の音声確認 (許可要求 / A-2)」節を追加（許可要求 voice_speak → voice_listen ブロッキング待ち、肯定でのみ実行・否定/unintelligible/曖昧は実行しない、破壊的操作の例示、線引きは使いながら調整、連続操作の確認単位）。3 役割表の「Story 03 で定義」を実セクション参照へ更新
- `tests/test_voice_chat_command.py` — 04/03/01 用の grep テストを追加（セクション存在・ブロッキング・肯定でのみ実行・否定/unintelligible/曖昧は不実行・例示・調整前提・確認単位）

### 関数 / API シグネチャ

該当なし（プロンプト記述）

### バリデーション・エラー処理

- 返事が unintelligible のときは再確認する

### エッジケース

- 連続する破壊的操作（複数ファイル削除など）をまとめて 1 回確認するか個別かを記述する

## 依存関係

- 前提: なし
- ブロックする: なし

理由: 同 Story 内で独立したコマンド本文の追記。

## スコープ外

- ハーネスのパーミッション機構利用（バイパス前提）
- サーバ側コード追加

## 補足

- [ADR-0002](../../../../adr/0002-skip-permissions-with-voice-confirmation.md) / requirement A-2
- 関連設計: [design.md 設計判断 6](../../../../design/design.md#主要な設計判断とその理由)
