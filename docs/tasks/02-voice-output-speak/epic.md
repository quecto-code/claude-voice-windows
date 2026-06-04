---
type: epic
title: 音声出力
label: must-have
depends_on:
  - 00-environment-setup
  - 01-mcp-server-foundation
---

## 背景・目的

Claude が「ユーザに伝えるべき」と判断した内容を日本語音声で読み上げる機能。listen に先行して開発する（speak は listen に依存しないため、最短で「Claude をしゃべらせる」を達成できる）。TTS は VOICEVOX（WSL2 Linux 版エンジン、ローカル HTTP）、再生は `sox` の pulse 経路。

実装は `src/claude_voice/speak/` 配下に閉じる（`design.md#構成` の独立 2 パイプライン方針）。

## ゴール・成功基準

- `voice_speak(text)` ツールに渡したテキストが VOICEVOX で合成され、WSLg PulseAudio 経由でスピーカーから再生される。
- Claude の応答生成完了から読み上げ開始までの遅延 < 2 秒（GPU 利用）。
- 連続呼び出し時に再生が重ならない（直列化）。

## 想定ユーザー

開発者（作者自身）。別作業中に Claude の報告・宣言・許可要求を耳で受け取る。

## 主要なユースケース

- ユースケース 1: Claude が処理結果の要約を音声で報告する（事後報告）
- ユースケース 2: Claude がこれから行う処理を音声で宣言する（事前宣言）
- ユースケース 3: 破壊的操作の許可を音声で求める（許可要求、Epic 04 から呼ばれる）

## スコープ

### 含むもの (in scope)

- VOICEVOX エンジンへの合成リクエストと WAV 取得（`speak/synthesizer.py`）
- `sox` による pulse sink 再生（`speak/player.py`）
- `speak.speak(text)` パイプラインと `voice_speak` MCP ツール公開

### 含まないもの (out of scope)

- 「何を読み上げるか」の判断（Claude 側／Epic 04 のループ指示が担う）
- 読み上げ中の割り込み（モデル B、対象外）
- 3 役割の判別（プロンプト側、`design.md` 設計判断 5）

## 配下 Story（計画）

- `01-synthesize-and-play` VOICEVOX 合成 + 再生 + voice_speak ツール公開

## 依存関係

- 前提: `01-mcp-server-foundation`
- 関連: `04-voice-chat-loop`（`voice_speak` を利用）

## リスク・未決事項

- VOICEVOX エンジンの常駐起動方法（手動 / スクリプト）は実装時に決める
- 話者（speaker id）の選定は使いながら調整（`config.SPEAKER_ID` で差し替え可）

## 補足

- 音声経路は WSLg PulseAudio + `sox`（[design.md#全体像](../../design/design.md#全体像) で検証済み）
- 関連設計: [design.md#構成](../../design/design.md#構成) / [design.md#インターフェース](../../design/design.md#インターフェース) / [design.md#相互作用状態エラー方針](../../design/design.md#相互作用状態エラー方針)
