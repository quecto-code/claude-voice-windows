---
type: task
title: 進捗ナレーションと自動終了抑止を実装する
label: must-have
depends_on:
  - 04-voice-chat-loop/04-delegated-quasi-concurrency/01-delegate-heavy-work-and-continue-loop
---

## 背景

親 Story `04-voice-chat-loop/04-delegated-quasi-concurrency` の一部。委譲したバックグラウンドジョブの走行中、ユーザの沈黙時に進捗を音声で知らせ（requirement 11）、その間は silent 自動終了（Edge Case 2）を抑止する。既存の silent / onset timeout タイマを進捗報告に転用する（[ADR-0004](../../../../adr/0004-delegated-quasi-concurrency.md)、[design.md オーケストレーション節](../../../../design/design.md#相互作用状態エラー方針)）。

親 Story: 04-voice-chat-loop/04-delegated-quasi-concurrency

## 受入条件

- [x] `.claude/commands/voice-chat.md` に、バックグラウンドジョブ走行中に `voice_listen` が `status="silent"` を返したら、継続通知ではなく**進捗報告**（「まだ〜の作業中です」等）を `voice_speak` する手順がある（requirement 11）
- [x] バックグラウンドジョブ走行中は silent 自動終了（Edge Case 2）を抑止する（silent カウントで終了させない）手順が明記されている
- [x] ジョブが無いときは従来どおり 2 連続 silent で自動終了する（既存挙動を保つ）と整合している
- [x] バックグラウンドジョブ完了の結果は、次のターンの切れ目で事後報告として `voice_speak` すると明記されている
- [x] 「読み上げの 3 役割」表が **4 役割**（事前宣言・進捗報告・事後報告・許可要求）に更新されている

## 仕様詳細

### 変更ファイル

- `.claude/commands/voice-chat.md` —
  - 「voice_speak の 3 役割」節を **4 役割**に更新（進捗報告を追加。ノンブロッキング）
  - 「silent 時の挙動」節に「ジョブ走行中は継続通知の代わりに進捗報告を出し、自動終了を抑止する」分岐を追加
  - ジョブ完了をターンの切れ目で事後報告する手順を追加
- `tests/test_voice_chat_command.py` — 04/04/02 用の grep テストを追加（4 役割への更新・進捗報告・走行中の自動終了抑止・ジョブ無し時は従来終了・完了の事後報告の各文言）

### 関数 / API シグネチャ

該当なし（プロンプト記述。進捗の粒度は既存 `config.ONSET_TIMEOUT_SEC` に依存し、サーバ変更なし）

### バリデーション・エラー処理

- 進捗報告は失敗してもループを止めない（既存 Reliability 方針を踏襲）

### エッジケース

- 走行中の silent と、ジョブ無しの silent を取り違えない（走行中フラグで分岐）
- 進捗報告の粒度は数十秒で粗い。運用で調整する前提（[ADR-0004](../../../../adr/0004-delegated-quasi-concurrency.md)）

## 依存関係

- 前提: 04-voice-chat-loop/04-delegated-quasi-concurrency/01-delegate-heavy-work-and-continue-loop
- ブロックする: なし

理由: 委譲＝進行中ジョブの概念ができてから、その走行中の進捗・抑止を足す。

## スコープ外

- 委譲そのもの・会話継続（01 で実装）
- 破壊的操作の差し戻し（03 で実装）
- 進捗粒度を細かくするための仕組み追加（運用調整の範囲）

## 補足

- [ADR-0004](../../../../adr/0004-delegated-quasi-concurrency.md) / requirement 11 / Edge Case 2
- 関連設計: [design.md#相互作用状態エラー方針（オーケストレーション: 委譲型準並行）](../../../../design/design.md#相互作用状態エラー方針) / [design.md 設計判断 5（4 役割・単一スピーカー）](../../../../design/design.md#主要な設計判断とその理由)
- 変更履歴: docs/changes/CHANGELOG.md CH-002
