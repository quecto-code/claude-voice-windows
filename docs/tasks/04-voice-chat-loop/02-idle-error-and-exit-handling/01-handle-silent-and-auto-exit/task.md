---
type: task
title: silent 時の継続通知と自動終了を実装する
label: must-have
depends_on: []
---

## 背景

親 Story `04-voice-chat-loop/02-idle-error-and-exit-handling` の一部として、status=silent のときの継続通知（1 回目）と自動終了（2 回目）の挙動を `/voice-chat` の指示に書く（requirements Edge Case 1/2）。

親 Story: 04-voice-chat-loop/02-idle-error-and-exit-handling

## 受入条件

- [x] `.claude/commands/voice-chat.md` に「status=silent が 1 回目 → 継続中を `voice_speak` → 再 listen」の手順が記載されている（Edge Case 1）→ 「1 回目の silent」節で `voice_speak` で継続通知 + 再 `voice_listen` を明記
- [x] 「継続通知後さらに silent → 終了を `voice_speak` しループ離脱」の手順が記載されている（Edge Case 2）→ 「2 回連続の silent」節で「無音が続いたため音声モードを終了します」+ ループ離脱を明記
- [x] silent の連続回数の数え方（2 回連続で終了、status=ok でカウントリセット）が明記されている → `silent_count` 変数 / `status=="ok"` で `silent_count=0` リセット / `status=="silent"` で `silent_count += 1` / 2 回連続で終了 / `silent → ok → silent` は連続ではない、を本文に明示。`unintelligible` は別経路で silent カウンタを増やさないことも明記

## 仕様詳細

### 変更ファイル

- `.claude/commands/voice-chat.md`（既存の「失敗 status での継続」に補注を入れた上で、新節「silent 時の挙動 (Edge Case 1 / 2)」を追加。silent カウンタの管理 / 1 回目 / 2 回連続 / まとめ の 4 ブロック構成）
- `tests/test_voice_chat_command.py`（既存 15 件に新規 6 件追加 = 計 21 件）
- `docs/tasks/.../task.md`（受入条件チェック）
- `docs/tasks/STATUS.md`（15/17）

実装ポイント:
- `silent_count` は Claude のプロンプト文脈で管理（サーバはステートレス、設計判断 1）
- `status=="ok"` でリセット、`status=="silent"` でインクリメント、2 回連続で終了
- 「`silent → ok → silent` は連続ではない」のエッジケースも明示
- `unintelligible` は別経路扱いで silent カウンタを増やさない (次タスク 02-handle-unintelligible-and-end-command で扱う) ことも本文中で明確化
- pytest 全 115 件 pass + 1 件 skip

### 関数 / API シグネチャ

該当なし（プロンプト記述）

### バリデーション・エラー処理

該当なし

### エッジケース

- 1 回 silent → 発話あり（ok）で復帰した場合は silent カウントをリセットする

## 依存関係

- 前提: なし
- ブロックする: なし

理由: 同 Story 内で独立した分岐記述。

## スコープ外

- unintelligible・終了コマンド（次タスク）

## 補足

- requirements Edge Case 1/2 に対応
- 関連設計: [design.md#相互作用状態エラー方針](../../../../design/design.md#相互作用状態エラー方針)（status=silent の分岐）
