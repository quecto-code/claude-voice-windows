---
type: epic
title: 音声入力
label: must-have
depends_on:
  - 00-environment-setup
  - 01-mcp-server-foundation
---

## 背景・目的

ユーザの発話を文字起こしして Claude への指示に変換する機能。録音中は vosk でストリーミング認識（確定ワード「以上」のスポッティング）、発話確定後に faster-whisper で高品質な最終テキストを得る二段構成（[ADR-0003](../../adr/0003-dual-engine-streaming-listen.md)）。

実装は `src/claude_voice/listen/` 配下に閉じる（[design.md#構成](../../design/design.md#構成) の独立 2 パイプライン方針）。並行性は **sox 子プロセス + 単一読取スレッド + vosk + SIGTERM** で実装する（[design.md 設計判断 2](../../design/design.md#主要な設計判断とその理由)）。

## ゴール・成功基準

- `voice_listen()` が、録音 → 確定 → 文字起こしを行い `ListenResult` を返す。
- 発話確定から処理開始（transcript 取得）までの待ち時間が P95 < 3 秒（GPU 利用）。

## 想定ユーザー

開発者（作者自身）。キーボードに向かえない場面で口頭で指示を出す。

## 主要なユースケース

- ユースケース 1: 喋って数秒黙ると、その発話が指示として確定する（沈黙確定、FR-8）
- ユースケース 2: 「以上」と言うと即座に確定する（確定ワード、FR-9）
- ユースケース 3: 発話なしで待ち時間が長いと `status="silent"` を返す（Edge1/2 の起点）

## スコープ

### 含むもの (in scope)

- `sox` による pulse マイク録音と sox 自身による silence 自動停止
- vosk ストリーミングによる確定ワード検出と sox の SIGTERM 停止
- faster-whisper による最終文字起こし
- `voice_listen` MCP ツール（status: ok / silent / unintelligible）

### 含まないもの (out of scope)

- status を見た後の分岐（継続通知・再 listen・終了判断）は Epic 04
- 終了コマンドの意味解釈（Epic 04、Claude 側）
- 録音の暫定表示（あれば便利だが本 Epic では対象外）

## 配下 Story（計画）

- `01-record-and-finalize` 発話を録音し沈黙/確定ワードで確定する
- `02-transcribe-and-expose-tool` 確定音声を文字起こしし voice_listen を公開する

## 依存関係

- 前提: `01-mcp-server-foundation`
- 関連: `04-voice-chat-loop`（`voice_listen` を利用）

## リスク・未決事項

- 無音しきい値（初期 1.2 秒）・onset timeout（初期 30 秒）は使いながら調整（`config.py`）
- vosk 日本語モデルのサイズと確定ワード検出精度は実測で調整

## 補足

- [ADR-0003](../../adr/0003-dual-engine-streaming-listen.md)（二段構成の根拠）
- 関連設計: [design.md#構成](../../design/design.md#構成) / [design.md#データモデル](../../design/design.md#データモデル) / [design.md#インターフェース](../../design/design.md#インターフェース) / [design.md#相互作用状態エラー方針](../../design/design.md#相互作用状態エラー方針)
