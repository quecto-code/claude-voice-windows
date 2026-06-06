---
type: story
title: VOICEVOX で合成し再生して voice_speak を公開する
url: 
label: must-have
depends_on:
  - 01-mcp-server-foundation/01-server-skeleton
---

## 背景・目的

テキストを音声化して再生する一連の流れを実装し、`voice_speak` ツールとして Claude から呼べるようにする。これで Claude がしゃべれるようになる。実装は `src/claude_voice/speak/` 配下に閉じ、listen 側には一切依存しない（`design.md#構成` 設計方針 2）。

## ユーザーストーリー

**As a** ハンズフリーで Claude を使う開発者
**I want to** Claude の応答を日本語音声で聞きたい
**So that** 画面を見られない場面でも処理内容や結果を把握できる

## 受入条件

- [ ] `src/claude_voice/speak/synthesizer.py` に `synthesize(text: str, speaker: int) -> bytes | None` が実装され、VOICEVOX の `/audio_query` → `/synthesis` を叩いて WAV bytes を返す
- [ ] `src/claude_voice/speak/player.py` に `play(wav: bytes) -> bool` が実装され、`sox` で Windows の `waveaudio` 既定デバイスに同期再生する
- [ ] `src/claude_voice/speak/__init__.py` から `speak(text: str) -> SpeakResult` が公開され、合成 + 再生を順に行う
- [ ] MCP ツール `voice_speak(text: str) -> SpeakResult` が `server.py` に登録され、`speak.speak(text)` を呼ぶ薄いラッパとして動く
- [ ] 日本語テキスト（例「ファイルを3件更新しました」）を渡すと、人間が聞き取れる日本語音声が再生される
- [ ] VOICEVOX エンジン未起動・合成失敗・再生失敗のいずれの場合も例外を投げず、`SpeakResult(ok=False, error=<理由>)` を返す（[Reliability NFR]）
- [ ] 空文字 `text` を渡すと再生せず `SpeakResult(ok=True, error=None)` を返す
- [ ] 連続呼び出しで再生が重ならない（`speak/__init__.py` 内の `Lock` で直列化）
- [ ] 合成完了から再生開始までの遅延が < 2 秒（GPU 利用時）

## 仕様詳細

### UI / 画面

なし

### API / Server Action

- MCP ツール: `voice_speak(text: str) -> SpeakResult`
- 公開関数: `claude_voice.speak.speak(text: str) -> SpeakResult`
- 内部: `synthesizer.synthesize(text, speaker) -> bytes | None`, `player.play(wav) -> bool`

### データモデル

`SpeakResult` を使う（`types.py`）。不変条件:
- `ok=True ⇒ error is None`
- `ok=False ⇒ error` は非空文字列

### バリデーション

- 空文字 `text` は即 `ok=True` で返す（合成・再生をスキップ）

### エラーハンドリング

- VOICEVOX 接続不可・HTTP 非 200・WAV 取得失敗を捕捉し `error="voicevox synthesis failed"` 等で返す
- 再生失敗（sox 異常終了）を捕捉し `error="playback failed"` で返す

### エッジケース

- 長文テキスト（数百文字）でも再生が途切れない
- 連続 `voice_speak` 呼び出し時、前の再生完了を待ってから次の合成 / 再生を開始する

## 依存関係

- 前提（着手前に完了が必要）: `01-mcp-server-foundation/01-server-skeleton`
- ブロックする: `04-voice-chat-loop/01-voice-chat-command-and-loop`

理由: 共有モジュール（types / config）とサーバ雛形がないと実装できない。ループは speak の存在を前提にする。

## スコープ外

- 何を読み上げるかの判断（Claude / Epic 04）
- 読み上げ中の割り込み（モデル B）

## 補足

- 再生は `sox` の `waveaudio` 出力（`sox -t wav - -t waveaudio default`。Windows Multimedia Audio 既定デバイス）
- 関連設計:
  - [design.md#構成](../../../design/design.md#構成)（speak/ サブパッケージの責務）
  - [design.md#インターフェース](../../../design/design.md#インターフェース)（MCP ツール / speak 公開 API / 内部関数 / VOICEVOX 外部 API）
  - [design.md#相互作用状態エラー方針](../../../design/design.md#相互作用状態エラー方針)（speak フロー・失敗パス・直列化）
