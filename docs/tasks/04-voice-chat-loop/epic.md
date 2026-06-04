---
type: epic
title: 音声対話ループ
label: must-have
depends_on:
  - 00-environment-setup
  - 02-voice-output-speak
  - 03-voice-input-listen
---

## 背景・目的

listen と speak を束ね、`/voice-chat` でハンズフリーの対話を成立させる Epic。Claude 自身が `voice_listen` / `voice_speak` を呼んでループを回す。当初はターン制（[ADR-0001](../../adr/0001-mcp-tool-driven-turn-based.md)）だったが、重い作業中の待ち時間を解くため **委譲型準並行**（[ADR-0004](../../adr/0004-delegated-quasi-concurrency.md)、Story 04）に拡張する。安全性は `--dangerously-skip-permissions` 前提で、破壊的操作のみ音声確認で担保する（[ADR-0002](../../adr/0002-skip-permissions-with-voice-confirmation.md)）。

**重要**: この Epic の成果物は **Claude Code のスラッシュコマンド `.claude/commands/voice-chat.md`** とその指示内容であり、`src/claude_voice/` 側にはコードを追加しない（[design.md 設計判断 1・5・6](../../design/design.md#主要な設計判断とその理由)）。

## ゴール・成功基準

- `/voice-chat` を実行すると音声モードに入り、「listen → 宣言 → 作業 → 報告 → listen」のターンが終了コマンドまで継続する
- 単発の認識/合成失敗でループがクラッシュしない（[Reliability NFR]）
- 破壊的操作の前に音声で許可を求めるフローが動く

## 想定ユーザー

開発者（作者自身）。別作業をしながら音声だけで Claude Code を操作する。

## 主要なユースケース

- ユースケース 1: 口頭で指示 → Claude が宣言し作業し結果を報告 → 次の指示待ちに戻る
- ユースケース 2: 無音が続くと継続通知し、さらに続くと自動終了する
- ユースケース 3: 破壊的操作の前に音声で許可を求め、「はい」でのみ実行する

## スコープ

### 含むもの (in scope)

- `.claude/commands/voice-chat.md`（スラッシュコマンド本体）
- ループ指示プロンプト（listen → 宣言 → 作業 → 報告 → listen の手順）
- 3 役割（事前宣言・事後報告・許可要求）の運用ルール（Story 04 で進捗報告を加え 4 役割に拡張）
- silent / unintelligible / 終了コマンドの分岐
- 破壊的操作の音声確認
- 委譲型準並行への拡張（重い作業の委譲＋会話継続・進捗ナレーション・破壊的操作の差し戻し。ADR-0004 / Story 04）

### 含まないもの (out of scope)

- 処理中の真の割り込み = barge-in での即時中断（モデル B の B-1 / B-2）。委譲型準並行（ADR-0004）はこれとは別物で in scope
- listen/speak ツール自体の実装（Epic 02 / 03）
- ホットワード起動
- サーバ側コードの追加（`design.md` 設計判断 1 / 5 / 6 によりサーバには対応物を置かない）

## 配下 Story（計画）

- `01-voice-chat-command-and-loop` /voice-chat 起動とターンループ・3 役割
- `02-idle-error-and-exit-handling` silent / unintelligible / 終了コマンドの分岐
- `03-destructive-operation-confirmation` 破壊的操作の音声確認
- `04-delegated-quasi-concurrency` 重い作業の委譲・会話継続・進捗ナレーション・破壊的操作の差し戻し（委譲型準並行、[ADR-0004](../../adr/0004-delegated-quasi-concurrency.md)）

## 依存関係

- 前提: `02-voice-output-speak`, `03-voice-input-listen`
- 関連: なし

## リスク・未決事項

- ループ維持（Claude が listen→speak→listen を続けるか）はプロンプト設計に依存。listen 戻り値にも継続指示を添えて補強する
- 「破壊的操作」の線引きは使いながら調整

## 補足

- [ADR-0004](../../adr/0004-delegated-quasi-concurrency.md)（委譲型準並行。ADR-0001 を supersede）/ [ADR-0001](../../adr/0001-mcp-tool-driven-turn-based.md) / [ADR-0002](../../adr/0002-skip-permissions-with-voice-confirmation.md)
- 変更履歴: docs/changes/CHANGELOG.md CH-002
- 関連設計:
  - [design.md#全体像](../../design/design.md#全体像)
  - [design.md#相互作用状態エラー方針](../../design/design.md#相互作用状態エラー方針)
  - [design.md 設計判断 1（ステートレス）/ 5（3 役割をサーバに置かない）/ 6（パーミッションをサーバに置かない）](../../design/design.md#主要な設計判断とその理由)
