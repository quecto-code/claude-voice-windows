---
type: task
title: ターンループと 3 役割の指示を定義する
label: must-have
depends_on:
  - 04-voice-chat-loop/01-voice-chat-command-and-loop/01-create-voice-chat-command
---

## 背景

親 Story `04-voice-chat-loop/01-voice-chat-command-and-loop` の一部として、`/voice-chat` の本文にターンループと voice_speak の 3 役割の運用を記述する（[ADR-0001](../../../../adr/0001-mcp-tool-driven-turn-based.md)、[design.md 設計判断 1・5](../../../../design/design.md#主要な設計判断とその理由)）。

親 Story: 04-voice-chat-loop/01-voice-chat-command-and-loop

## 受入条件

- [x] `.claude/commands/voice-chat.md` の本文に「`voice_listen` → status=ok なら 事前宣言(`voice_speak`) → 作業 → 事後報告(`voice_speak`) → 再び `voice_listen`」のループ手順が明記されている → 「ターンループ」節に listen → 事前宣言 → 作業 → 事後報告 → 再 listen の流れ + voice_listen が同節内に 2 回以上出現することを grep 検証
- [x] 「宣言・報告はノンブロッキング、ブロッキングで返事を待つのは許可要求のみ」が明記されている → 3 役割表 + 「ブロッキングで返事を待つのは『許可要求』のみ」を正規表現で検証
- [x] 「画面＝全文、音声＝要約のみ」（`voice_speak` には Claude が選んだ要点だけ渡す）が明記されている → 「画面 = 全文、音声 = 要約のみ」節を grep 検証
- [x] 「終了コマンド（例: 音声モードを終了 / もう終わり）を意味的に検知したらループを抜ける」が明記されている → 「終了コマンド」節 + 「意味的に」「意味解釈」「音声モードを終了 / もう終わり」を grep 検証
- [x] ループが 1 往復で止まらないよう「作業後は必ず再 listen する」指示が含まれる → 「作業後は必ず再 listen する」明示 + ループ図の `[7] そうでなければ [1] に戻る ← ★必ず再 listen する` で確認
- [x] 「listen/speak が失敗 status でも再 listen で継続する」旨が含まれる（[Reliability NFR]） → 「失敗 status での継続 (Reliability)」節で silent / unintelligible / `ok=false` でループを止めない方針を明記

## 仕様詳細

### 変更ファイル

- `.claude/commands/voice-chat.md`（追記・「起動手順 / ターンループ / voice_speak の 3 役割 / 画面=全文・音声=要約 / 終了コマンド / 失敗 status での継続 / 設計メモ」の 7 節構成に拡張）
- `tests/test_voice_chat_command.py`（既存 7 件に新規 8 件追加 = 計 15 件）
- `docs/tasks/.../task.md`（受入条件チェック）
- `docs/tasks/STATUS.md`（14/17、01-voice-chat-command-and-loop 2/2 ✓）

実装ポイント:
- ターンループ図を ASCII で示し、`[7] そうでなければ [1] に戻る ← ★必ず再 listen する` で 1 往復停止を防ぐ
- 3 役割を表形式 (事前宣言・事後報告・許可要求 / ブロッキング属性) + 注記で網羅
- 「ブロッキングで返事を待つのは『許可要求』のみ」を 1 文で明示
- 終了コマンドは「Claude の意味解釈に委ねる (固定文字列マッチではない)」を明文化、誤検出例 (作業を終わりにして) も記述
- 「画面 = 全文、音声 = 要約のみ」節で `voice_speak` には要点だけ抜粋する方針を明記
- silent / unintelligible / `ok=false` のいずれでもループを止めない (Reliability NFR)
- 詳細な silent カウントや破壊的操作判定は Story 02 / 03 で扱う旨を本文中に明記してスコープを切る
- pytest 全体 109 件 pass + 1 件 skip

### 関数 / API シグネチャ

該当なし（プロンプト記述）

### バリデーション・エラー処理

- listen/speak が失敗 status でも再 listen で継続する旨を書く

### エッジケース

- Claude が宣言を省略しがちな場合に備え、「毎ターン宣言する」旨を明示
- 終了コマンドと通常指示の判別は意味解釈に委ねる

## 依存関係

- 前提: 04-voice-chat-loop/01-voice-chat-command-and-loop/01-create-voice-chat-command
- ブロックする: なし

理由: コマンドの器が先に必要。

## スコープ外

- silent/unintelligible 分岐（別 Story）、破壊的操作の確認（別 Story）

## 補足

- [ADR-0001](../../../../adr/0001-mcp-tool-driven-turn-based.md)
- 関連設計:
  - [design.md#相互作用状態エラー方針](../../../../design/design.md#相互作用状態エラー方針)
  - [design.md 設計判断 1（ステートレス）/ 5（3 役割をサーバに置かない）](../../../../design/design.md#主要な設計判断とその理由)
