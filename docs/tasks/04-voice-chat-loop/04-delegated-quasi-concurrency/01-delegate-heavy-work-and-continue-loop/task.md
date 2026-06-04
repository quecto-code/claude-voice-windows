---
type: task
title: 重い作業の委譲と会話継続を組み込む
label: must-have
depends_on: []
---

## 背景

親 Story `04-voice-chat-loop/04-delegated-quasi-concurrency` の核。`/voice-chat` のターンループに「重い作業はバックグラウンド・サブエージェントに委譲して即 `voice_listen` に戻り会話を続ける」振る舞いを追記する（requirement 10、[ADR-0004](../../../../adr/0004-delegated-quasi-concurrency.md)、[design.md オーケストレーション節](../../../../design/design.md#相互作用状態エラー方針)）。

親 Story: 04-voice-chat-loop/04-delegated-quasi-concurrency

## 受入条件

- [x] `.claude/commands/voice-chat.md` に、`status="ok"` のとき作業を「軽い作業＝その場で実行」「重い作業＝バックグラウンド・サブエージェントに委譲」に振り分ける手順が明記されている
- [x] 委譲したら作業完了を待たず即 `voice_listen` に戻り会話を継続する（requirement 10）と明記されている
- [x] 同時に走るバックグラウンドジョブは 1 個までと明記されている
- [x] 走行中に新たな重い作業を指示されたら、暗黙に並列起動せず「完了を待つ／今のを止めて差し替える」を確認する手順がある
- [x] バックグラウンドジョブは `voice_speak` / `voice_listen` を呼ばず、結果・進捗をテキストで親に返す（単一スピーカー）と明記されている
- [x] 「重い／軽い」の線引きは固定仕様でなく使いながら調整する前提が明記されている

## 仕様詳細

### 変更ファイル

- `.claude/commands/voice-chat.md` — ターンループ節の `status="ok"` 分岐に「委譲型準並行」の手順を追加（軽い/重いの振り分け、重い作業はバックグラウンド・サブエージェントへ委譲、同時 1 ジョブ、走行中の新・重い作業は確認、単一スピーカー、線引きは調整前提）。「設計メモ」に進行中ジョブのハンドルもプロンプト側状態である旨を追記
- `tests/test_voice_chat_command.py` — 04/04/01 用の grep テストを追加（委譲手順・即 listen 復帰・同時 1 ジョブ・走行中の確認・単一スピーカー・線引き調整前提の各文言の存在）

### 関数 / API シグネチャ

該当なし（プロンプト記述。サーバ API は不変＝既存 `voice_listen` / `voice_speak` のみ。[design.md 設計判断 7](../../../../design/design.md#主要な設計判断とその理由)）

### バリデーション・エラー処理

- 走行中ジョブがあるのに新・重い作業が来たら確認（並列起動しない）

### エッジケース

- 軽い作業と重い作業の境界が曖昧なときは「重い寄り」に倒して委譲してよい（待ち時間を優先）

## 依存関係

- 前提: なし（親 Story の依存で既存ループ核の完成は担保済み）
- ブロックする: 04-voice-chat-loop/04-delegated-quasi-concurrency/02-narrate-progress-and-suppress-auto-exit, 04-voice-chat-loop/04-delegated-quasi-concurrency/03-handback-destructive-ops-to-foreground

理由: 委譲の核ができてから、進捗ナレーションと破壊的操作の差し戻しを足す。

## スコープ外

- 進捗ナレーション・silent 自動終了の抑止（02 で実装）
- 破壊的操作の差し戻し（03 で実装）
- サーバ側コード追加・複数ジョブ並行

## 補足

- [ADR-0004](../../../../adr/0004-delegated-quasi-concurrency.md) / requirement 10
- 関連設計: [design.md#相互作用状態エラー方針（オーケストレーション: 委譲型準並行）](../../../../design/design.md#相互作用状態エラー方針) / [design.md 設計判断 1・7](../../../../design/design.md#主要な設計判断とその理由)
- 変更履歴: docs/changes/CHANGELOG.md CH-002
