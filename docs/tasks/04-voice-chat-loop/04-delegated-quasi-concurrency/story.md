---
type: story
title: 重い作業を委譲して会話を継続する
label: must-have
depends_on:
  - 04-voice-chat-loop/01-voice-chat-command-and-loop
  - 04-voice-chat-loop/02-idle-error-and-exit-handling
  - 04-voice-chat-loop/03-destructive-operation-confirmation
---

## 背景・目的

ターン制（[ADR-0001](../../../adr/0001-mcp-tool-driven-turn-based.md)）では、重い作業の最中ユーザが沈黙のまま待たされていた。これを **委譲型準並行**（[ADR-0004](../../../adr/0004-delegated-quasi-concurrency.md)）へ拡張する。フォアグラウンドの `/voice-chat` 会話ループが重い作業を 1 つのバックグラウンド・サブエージェントに委譲して即 `voice_listen` に戻り、会話を続ける。進行中は進捗を音声で知らせ、完了をターンの切れ目で報告する（requirement 10 / 11、[design.md オーケストレーション節](../../../design/design.md#相互作用状態エラー方針)）。

成果物は **`.claude/commands/voice-chat.md`** とその指示内容のみ。`src/claude_voice/` 側にはコードを追加しない（MCP サーバ API・構成・データモデルは不変。[design.md 設計判断 1 / 7](../../../design/design.md#主要な設計判断とその理由)）。

## ユーザーストーリー

**As a** 別作業をしながら音声で Claude を使う開発者
**I want to** 重い作業を待つ間も会話を続け、進捗を音声で受け取りたい
**So that** 沈黙のまま待たされず、ハンズフリーのテンポが途切れない

## 受入条件

- [ ] `.claude/commands/voice-chat.md` に、重い作業をバックグラウンド・サブエージェントに委譲して `voice_listen` に戻り会話を継続する手順がある（requirement 10）
- [ ] 同時に走るバックグラウンドジョブは 1 個までで、走行中に新たな重い作業を指示されたら確認する手順がある
- [ ] ジョブ走行中の沈黙時に進捗を音声で伝え（進捗報告）、その間は silent 自動終了を抑止する手順がある（requirement 11 / Edge Case 2）
- [ ] バックグラウンドジョブは破壊的操作を実行せず親に差し戻し、親が既存の A-2 ブロッキング確認を経て実行する手順がある
- [ ] `voice_speak` / `voice_listen` を呼ぶのはフォアグラウンドのみ（単一スピーカー）と明記されている
- [ ] 読み上げ役割が 4 つ（事前宣言・進捗報告・事後報告・許可要求）に更新されている

## 仕様詳細

### UI / 画面

なし（プロンプト記述）

### API / Server Action

- 既存の `voice_listen` / `voice_speak` のみ。新しいサーバ API は追加しない（[design.md 設計判断 7](../../../design/design.md#主要な設計判断とその理由)）
- バックグラウンド・サブエージェントは Claude Code のサブエージェント機構（`run_in_background`）で起動

### データモデル

なし（会話状態・進行中ジョブのハンドルはプロンプト文脈に住む。[design.md 設計判断 1](../../../design/design.md#主要な設計判断とその理由)）

### バリデーション

- 走行中ジョブがあるときの新・重い作業の指示は、暗黙に並列起動せず確認する

### エラーハンドリング

- 破壊的操作は委譲先で実行せず親に差し戻し、A-2 で確認（[ADR-0002](../../../adr/0002-skip-permissions-with-voice-confirmation.md)）

### エッジケース

- ジョブを待って黙っているユーザを自動終了で蹴り出さない（Edge Case 2 の抑止）
- 進捗の粒度は `config.ONSET_TIMEOUT_SEC`（既存）に従い数十秒。粗さは運用調整前提（[ADR-0004](../../../adr/0004-delegated-quasi-concurrency.md)）

## 依存関係

- 前提（着手前に完了が必要）: `04-voice-chat-loop/01-voice-chat-command-and-loop`, `04-voice-chat-loop/02-idle-error-and-exit-handling`, `04-voice-chat-loop/03-destructive-operation-confirmation`
- ブロックする: なし

理由: 既存のループ核・silent 処理・破壊的操作確認を拡張する振る舞いのため、それらの完成後に積む。

## スコープ外

- 処理中の真の割り込み（barge-in / モデル B の B-1・B-2）。走行中ジョブの即時 kill はしない
- 複数バックグラウンドジョブの同時並行（当面 1 ジョブ）
- listen / speak ツール自体の変更、サーバ側コード追加（設計判断 1 / 7）
- 1 往復ごとのレイテンシ（STT→Claude→TTS）の短縮（別トラック・本 Story の対象外）

## 補足

- [ADR-0004](../../../adr/0004-delegated-quasi-concurrency.md)（委譲型準並行。[ADR-0001](../../../adr/0001-mcp-tool-driven-turn-based.md) を supersede）/ [ADR-0002](../../../adr/0002-skip-permissions-with-voice-confirmation.md)
- 関連設計:
  - [design.md#相互作用状態エラー方針（オーケストレーション: 委譲型準並行）](../../../design/design.md#相互作用状態エラー方針)
  - [design.md 設計判断 1（ステートレス）/ 5（4 役割・単一スピーカー）/ 6（破壊的操作はフォアグラウンド限定）/ 7（委譲型準並行のオーケストレーション）](../../../design/design.md#主要な設計判断とその理由)
- 変更履歴: docs/changes/CHANGELOG.md CH-002
