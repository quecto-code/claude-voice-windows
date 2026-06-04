---
type: story
title: 確定音声を文字起こしし voice_listen を公開する
label: must-have
depends_on:
  - 03-voice-input-listen/01-record-and-finalize
---

## 背景・目的

`recorder.record` が返した確定 PCM を faster-whisper で日本語に文字起こしし、`voice_listen` MCP ツールとして status 付きで Claude に公開する。これで「話せば指示テキストになる」が完成する。

## ユーザーストーリー

**As a** 口頭で指示を出す開発者
**I want to** 確定した発話が正確なテキストになって Claude に渡ってほしい
**So that** 音声指示が意図どおり実行される

## 受入条件

- [ ] `src/claude_voice/listen/transcriber.py` に `transcribe(pcm: bytes) -> str | None` が実装され、`config.WHISPER_MODEL_SIZE`（既定 `"small"`）/ CUDA で 16kHz/mono/s16le の生 PCM を日本語文字起こしする
- [ ] `src/claude_voice/listen/__init__.py` から `listen() -> ListenResult` が公開され、`recorder.record(...)` → 結果に応じて `transcribe(pcm)` → `ListenResult` の組み立てを行う
- [ ] `reason=FinalizeReason.timeout` → `ListenResult(transcript="", status="silent")`
- [ ] `transcribe(pcm)` が None / 空 / 極端に短い → `ListenResult(transcript="", status="unintelligible")`
- [ ] 正常時 → `ListenResult(transcript=<text>, status="ok")`。末尾に `config.FINALIZE_WORD`（「以上」）が含まれていれば除去する
- [ ] MCP ツール `voice_listen() -> ListenResult` が `server.py` に登録され、`listen.listen()` を呼ぶ薄いラッパとして動く
- [ ] 文字起こし失敗・モデルロード失敗を捕捉し、例外を投げず `unintelligible` 等にマップする（[Reliability NFR]）

## 仕様詳細

### UI / 画面

なし

### API / Server Action

- MCP ツール: `voice_listen() -> ListenResult`
- 公開関数: `claude_voice.listen.listen() -> ListenResult`
- 内部: `transcriber.transcribe(pcm) -> str | None`

### データモデル

`ListenResult` を使う（`types.py`）。不変条件:
- `status="ok" ⇒ transcript` は非空
- `status!="ok" ⇒ transcript == ""`

### バリデーション

- 空 PCM / 極短 PCM は unintelligible 判定

### エラーハンドリング

- faster-whisper のモデルロード失敗・推論失敗を捕捉し、status で表現

### エッジケース

- 確定ワード「以上」が transcript の末尾に残る場合は除去する（中ほどに混ざるケースは触らない）
- 雑音のみの入力は unintelligible

## 依存関係

- 前提（着手前に完了が必要）: `03-voice-input-listen/01-record-and-finalize`
- ブロックする: `04-voice-chat-loop/01-voice-chat-command-and-loop`

理由: 確定 PCM があって初めて文字起こしできる。ループは voice_listen を前提にする。

## スコープ外

- status を見た後の分岐（Epic 04 のループ指示）
- 暫定表示 UI（本 Story では対象外）

## 補足

- モデルは不足時 `medium` に上げる余地あり。GPU: RTX 3050 8GB
- [ADR-0003](../../../adr/0003-dual-engine-streaming-listen.md)
- 関連設計:
  - [design.md#構成](../../../design/design.md#構成)（listen/ サブパッケージ責務）
  - [design.md#データモデル](../../../design/design.md#データモデル)（ListenResult・status マッピング）
  - [design.md#インターフェース](../../../design/design.md#インターフェース)（voice_listen ツール / listen 公開 API / transcribe 内部 IF）
  - [design.md#相互作用状態エラー方針](../../../design/design.md#相互作用状態エラー方針)（listen フロー全体・失敗パス）
