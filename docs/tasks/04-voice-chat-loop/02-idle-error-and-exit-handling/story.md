---
type: story
title: 無音・聞き取り失敗・終了コマンドを処理する
label: must-have
depends_on:
  - 04-voice-chat-loop/01-voice-chat-command-and-loop
---

## 背景・目的

ループの分岐を整える。`voice_listen` の status（silent / unintelligible）と終了コマンドに応じて、継続通知・自動終了・再発話の促し・ループ離脱を行う（requirements の Edge Case 1/2・Requirement 6/7）。

## ユーザーストーリー

**As a** 別作業中に音声モードを開いている開発者
**I want to** 無音が続いたら通知や自動終了をしてほしいし、聞き取り失敗時はやり直しを促してほしい
**So that** 放置や誤認識でループが無駄に回り続けない

## 受入条件

- [ ] status=silent が **1 回目**のとき、`/voice-chat` 本文に従って音声モード継続中である旨を `voice_speak` で通知し、再び `voice_listen` する（Edge Case 1）
- [ ] 継続通知後さらに status=silent のとき、終了の旨を `voice_speak` で告げてループを抜ける（Edge Case 2）
- [ ] status=unintelligible のとき、「聞き取れませんでした、もう一度お願いします」を `voice_speak` し再 listen する（Requirement 6）
- [ ] transcript が終了コマンド（例「音声モードを終了」「もう終わり」）に意味的に該当するとき、別れの一言を `voice_speak` してループを抜ける（Requirement 7）
- [ ] silent 連続回数は **Claude が文脈で数える**（サーバはステートレス、[design.md 設計判断 1]）

## 仕様詳細

### UI / 画面

なし

### API / Server Action

- `voice_listen` の status を参照する分岐ロジック（コマンド本文の指示として）

### データモデル

なし（Claude のプロンプト文脈で管理）

### バリデーション

なし

### エラーハンドリング

- 連続失敗してもループ自体は維持する（[Reliability NFR]）

### エッジケース

- silent → 発話あり（ok）で復帰した場合は silent カウントをリセットする旨を書く
- 終了コマンドと通常指示の判別は Claude の意味解釈に委ねる

## 依存関係

- 前提（着手前に完了が必要）: `04-voice-chat-loop/01-voice-chat-command-and-loop`
- ブロックする: なし

理由: ループの核ができてから分岐を足す。

## スコープ外

- 破壊的操作の確認（別 Story）

## 補足

- Edge Case 1/2・Requirement 6/7 に対応
- 関連設計:
  - [design.md#相互作用状態エラー方針](../../../design/design.md#相互作用状態エラー方針)（status=silent / unintelligible の分岐）
  - [design.md トレース表（FR-6 / FR-7 / Edge1 / Edge2 → プロンプト側）](../../../design/design.md#トレーサビリティ)
