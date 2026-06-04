---
type: story
title: voice-chat 起動とターンループ・3 役割を成立させる
label: must-have
depends_on:
  - 02-voice-output-speak/01-synthesize-and-play
  - 03-voice-input-listen/02-transcribe-and-expose-tool
---

## 背景・目的

`/voice-chat` で音声モードに入り、Claude が listen → 宣言 → 作業 → 報告 → listen のターンを回す核を作る。会話状態はすべて Claude（プロンプト）側で管理する（[design.md 設計判断 1](../../../design/design.md#主要な設計判断とその理由)）。ループ維持はコマンドの指示プロンプトと listen 戻り値の補強で担保する（[ADR-0001](../../../adr/0001-mcp-tool-driven-turn-based.md)）。

## ユーザーストーリー

**As a** ハンズフリーで Claude を使う開発者
**I want to** /voice-chat で音声だけの対話ループに入りたい
**So that** キーボードに触れず指示と応答を往復できる

## 受入条件

- [ ] プロジェクトに `.claude/commands/voice-chat.md`（スラッシュコマンド定義）が存在する
- [ ] コマンド本文に「最初に `voice_listen` を呼ぶ前に、listen 状態に入った旨を `voice_speak` で告げる」手順がある
- [ ] status=ok のとき、transcript を指示として作業し、着手前に**事前宣言**（「〜をする」）を `voice_speak` で読み上げ、完了後に**事後報告**（「〜をした」）を `voice_speak` で読み上げる手順がある
- [ ] 1 ターン完了後、自動的に再び `voice_listen` を呼ぶ（終了コマンドまで継続する）旨が明記されている
- [ ] **宣言・報告はノンブロッキング、ブロッキングで返事を待つのは許可要求のみ**（次 Story の対象）であることが明記されている
- [ ] **画面＝全文、音声＝Claude が選んだ要約のみ**（`voice_speak` に渡すのは要点だけ）が明記されている

## 仕様詳細

### UI / 画面

- 画面には Claude の通常出力（全文）が出る。`voice_speak` には要約のみ渡す

### API / Server Action

- `voice_listen` / `voice_speak`（Epic 02/03）を利用

### データモデル

なし（会話状態は Claude のプロンプト文脈で管理）

### バリデーション

なし

### エラーハンドリング

- listen/speak が失敗 status を返しても、指示に従い再 listen して継続する

### エッジケース

- Claude が 1 往復でループを抜けないよう、コマンド本文に「作業後は必ず再 listen する」「listen 戻り値にも継続指示が含まれている前提で従う」と書く

## 依存関係

- 前提（着手前に完了が必要）: `02-voice-output-speak/01-synthesize-and-play`, `03-voice-input-listen/02-transcribe-and-expose-tool`
- ブロックする: `04-voice-chat-loop/02-idle-error-and-exit-handling`, `04-voice-chat-loop/03-destructive-operation-confirmation`

理由: speak と listen の両ツールが揃わないとループが回らない。分岐・確認はこの核の上に乗る。

## スコープ外

- silent/unintelligible/終了の分岐（次 Story）
- 破壊的操作の確認（別 Story）

## 補足

- [ADR-0001](../../../adr/0001-mcp-tool-driven-turn-based.md)
- 関連設計:
  - [design.md#全体像](../../../design/design.md#全体像)
  - [design.md 設計判断 1（ステートレス）/ 5（3 役割をサーバに置かない）](../../../design/design.md#主要な設計判断とその理由)
