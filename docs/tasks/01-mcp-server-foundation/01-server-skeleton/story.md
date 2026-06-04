---
type: story
title: MCP サーバの雛形と共有モジュールを整える
label: must-have
depends_on: []
---

## 背景・目的

全ツールの土台となるパッケージ・共有型・設定モジュール・MCP サーバの雛形を作り、Claude Code から認識される状態にする。`design.md` の構成節そのままの骨組みをここで用意する。

## ユーザーストーリー

**As a** claude-voice を開発する開発者
**I want to** claude-voice MCP サーバを Claude Code に登録し起動できる土台を作りたい
**So that** この上に listen / speak のパイプラインを実装していける

## 受入条件

- [ ] `pyproject.toml` と `src/claude_voice/{__init__.py, __main__.py, server.py, types.py, config.py}` が存在する
- [ ] `python -m claude_voice` で stdio MCP サーバが起動し、MCP ハンドシェイクを完了する
- [ ] サーバが疎通確認用ツール `voice_ping() -> str` を 1 個公開し、Claude から呼ぶと `"pong"` が返る
- [ ] `types.py` に `FinalizeReason`（enum: silence / word / timeout）、`ListenResult`（dataclass: transcript, status）、`SpeakResult`（dataclass: ok, error）が定義されている
- [ ] `config.py` に `SILENCE_SEC` / `ONSET_TIMEOUT_SEC` / `FINALIZE_WORD` / `WHISPER_MODEL_SIZE` / `VOSK_MODEL_PATH` / `VOICEVOX_URL` / `SPEAKER_ID` が定数として宣言され、対応する環境変数で上書きできる
- [ ] Claude Code の MCP 設定に claude-voice が登録され、ツール一覧に `voice_ping` が表示される

## 仕様詳細

### UI / 画面

なし（CLI / MCP）

### API / Server Action

- MCP ツール `voice_ping() -> str`（疎通確認用、後続で削除可）
- 内部: `claude_voice.types`, `claude_voice.config` を listen / speak から import 可能にする

### データモデル

`design.md#データモデル` の値オブジェクト 3 種をそのまま実装。

### バリデーション

- 環境変数で上書きする値の型（float / int / str / Path）を `config.py` で検証して落とす

### エラーハンドリング

- 起動失敗時は stderr にスタックトレースを出す（Claude Code の MCP ログで確認できる）

### エッジケース

- Python 3.10 / 3.11 のどちらで動かすか固定し、`pyproject.toml` の `requires-python` に明記する
- vosk モデルの実体は配置必須だがダウンロード手順は README に逃がす（このストーリーでは型と設定だけ用意）

## 依存関係

- 前提（着手前に完了が必要）: なし
- ブロックする: `02-voice-output-speak/01-synthesize-and-play`, `03-voice-input-listen/01-record-and-finalize`

理由: 共有モジュールとサーバ雛形がないと listen / speak を載せられない。

## スコープ外

- 録音・再生・STT・TTS の実装
- `/voice-chat` スラッシュコマンド

## 補足

- [ADR-0001](../../../adr/0001-mcp-tool-driven-turn-based.md)
- 関連設計: [design.md#構成](../../../design/design.md#構成) / [design.md#データモデル](../../../design/design.md#データモデル) / [design.md#インターフェース](../../../design/design.md#インターフェース)
