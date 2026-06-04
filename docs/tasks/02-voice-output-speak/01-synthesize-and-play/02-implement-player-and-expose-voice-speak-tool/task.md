---
type: task
title: player と voice_speak ツールを公開する
label: must-have
depends_on:
  - 02-voice-output-speak/01-synthesize-and-play/01-implement-voicevox-synthesizer
---

## 背景

親 Story `02-voice-output-speak/01-synthesize-and-play` の一部として、`sox` 再生関数を実装し、合成 → 再生のパイプライン `speak()` を組み、`voice_speak` MCP ツールとして `server.py` に登録する。

親 Story: 02-voice-output-speak/01-synthesize-and-play

## 受入条件

- [x] `src/claude_voice/speak/player.py` に `play(wav: bytes) -> bool` が実装され、`sox -t wav - -t pulseaudio default` 相当を起動して stdin に WAV bytes を流し、再生完了までブロックする → mock で subprocess.run の引数（コマンド・input）を確認
- [x] 再生失敗（sox の非 0 終了 / 起動失敗）を捕捉し `False` を返し stderr にログ出力する。例外を上位に投げない → `returncode=1` / `FileNotFoundError` / 任意 Exception / OSError の 4 ケースで pytest
- [x] `src/claude_voice/speak/__init__.py` から `speak(text: str) -> SpeakResult` が公開され、4 分岐（空文字 / 合成失敗 / 再生失敗 / 成功）で正しい SpeakResult を返す → pytest 4 件 + synthesize に `config.SPEAKER_ID` を渡すことも確認
- [x] `speak/__init__.py` 内の `threading.Lock()` を取得してから合成 + 再生を行い、連続呼び出しで再生が重ならない → 3 スレッドで同時呼び出し、`slow_play` 内で `in_flight > 1` を観測したらアウト、`overlap_seen == []` を確認 + `_lock` が threading.Lock 由来であることも確認
- [x] `src/claude_voice/server.py` に MCP ツール `voice_speak(text: str) -> SpeakResult` が追加され、`speak.speak(text)` を呼ぶ薄いラッパとして動く → `server._speak` を mock して呼び出しと引数伝播を確認
- [x] Claude から `voice_speak("テスト")` を呼ぶと日本語音声が再生され、`SpeakResult(ok=True, error=None)` が返る → **VOICEVOX 起動状態で `speak("テスト")` を実行、実音声再生 + `SpeakResult(ok=True, error=None)` 返却を確認**（Claude 経由呼び出しは Claude Code 再起動が要るため、内部関数の同等動作で代替確認）

## 仕様詳細

### 変更ファイル

- `src/claude_voice/speak/player.py`（新規・`play`、`sox` サブプロセス + stderr ログ + 例外マッピング）
- `src/claude_voice/speak/__init__.py`（実装・`speak` パイプライン + `threading.Lock` 直列化）
- `src/claude_voice/server.py`（追記・`voice_speak` ツール登録、`_speak` への薄いラッパ）
- `tests/test_player.py`（新規・5 件）
- `tests/test_speak.py`（新規・6 件）
- `tests/test_voice_speak_tool.py`（新規・2 件）
- `docs/tasks/.../task.md`（受入条件チェック）
- `docs/tasks/STATUS.md`（8/17、02 epic 2/2 ✓、01-synthesize-and-play 2/2 ✓）

実装ポイント:
- `play` は `subprocess.run(["sox","-t","wav","-","-t","pulseaudio","default"], input=wav, check=False, capture_output=True)`。`check=False` + 自前で returncode 判定
- `speak` は `with _lock:` で合成 + 再生を直列化（モジュールレベル `_lock = threading.Lock()`）
- `server.voice_speak` は `_speak` への薄いラッパで MCP ツール登録

### 関数 / API シグネチャ

```python
# speak/player.py
def play(wav: bytes) -> bool:
    """WAV bytes を sox で同期再生。成功 True / 失敗 False。例外は投げない。"""

# speak/__init__.py
def speak(text: str) -> SpeakResult: ...

# server.py（追加）
def voice_speak(text: str) -> SpeakResult: ...   # speak.speak の薄いラッパ
```

### バリデーション・エラー処理

- 空文字 text の早期 return
- sox 起動失敗・非 0 終了を `False` にマップ
- 例外を `SpeakResult.error` の文字列に変換

### エッジケース

- 長文 WAV でも sox stdin 経由で詰まらない（ブロッキング書き込み）
- 連続 `voice_speak` 呼び出し時、ロックで再生が重ならない

## 依存関係

- 前提: 02-voice-output-speak/01-synthesize-and-play/01-implement-voicevox-synthesizer
- ブロックする: 04-voice-chat-loop/01-voice-chat-command-and-loop

理由: 合成関数の上に再生とツール公開を載せる。ループは voice_speak を前提にする。

## スコープ外

- 何を読み上げるかの判断（Epic 04 / プロンプト側）

## 補足

- 再生コマンド例: `sox -t wav - -t pulseaudio default`（stdin から WAV を流す）
- 関連設計:
  - [design.md#構成](../../../../design/design.md#構成)（speak/ サブパッケージ責務）
  - [design.md#インターフェース](../../../../design/design.md#インターフェース)（MCP ツール voice_speak / speak 公開 API / player・synthesizer 内部 IF）
  - [design.md#相互作用状態エラー方針](../../../../design/design.md#相互作用状態エラー方針)（speak フロー・直列化・失敗パス）
