---
type: task
title: listen パイプラインと voice_listen ツールを公開する
label: must-have
depends_on:
  - 03-voice-input-listen/02-transcribe-and-expose-tool/01-implement-faster-whisper-transcriber
  - 03-voice-input-listen/01-record-and-finalize/02-add-vosk-streaming-and-finalize-word
---

## 背景

親 Story `03-voice-input-listen/02-transcribe-and-expose-tool` の後半として、`recorder.record` と `transcriber.transcribe` を束ねた `listen.listen()` を実装し、`voice_listen` MCP ツールとして `server.py` に登録する。

親 Story: 03-voice-input-listen/02-transcribe-and-expose-tool

## 受入条件

- [x] `src/claude_voice/listen/__init__.py` から `listen() -> ListenResult` が公開されている → callable + 引数なし + 返り値 ListenResult を pytest で確認
- [x] `listen()` の中身は仕様の順序どおりの分岐 → record/transcribe を mock し timeout / silence + None / silence + 空 / silence + 空白だけ / silence + 文字列 / word + 文字列 の 6 分岐を pytest 検証 + record が `config.FINALIZE_WORD, SILENCE_SEC, ONSET_TIMEOUT_SEC` で呼ばれることを確認
- [x] `src/claude_voice/server.py` に MCP ツール `voice_listen() -> ListenResult` が追加され、`listen.listen()` を呼ぶ薄いラッパとして動く → `server._listen` を mock してデリゲーションを検証
- [ ] Claude から `voice_listen()` を呼ぶと、実マイク発話に対し `status="ok"` + 妥当な transcript が返る → **手動検証**: Claude Code 再起動後に実マイクで確認（task-executor 範囲外）
- [x] 発話開始なしで放置すると `status="silent"`、雑音のみで放置すると `status="unintelligible"` が返る → mock で `timeout` 経路と `transcribe → None/空` 経路をそれぞれ確認
- [x] 例外を上位に投げない（status で表現） → recorder / transcriber に例外を仕込んでも `ListenResult("", "unintelligible")` で帰ることを確認

## 仕様詳細

### 変更ファイル

- `src/claude_voice/listen/__init__.py`（新規実装・`listen()` パイプライン + `_strip_finalize_word` ヘルパ）
- `src/claude_voice/server.py`（追記・`voice_listen` MCP ツール登録）
- `tests/test_listen_pipeline.py`（新規・21 件: 分岐 6 + パラメタライズド 10 + 統合 2 + 例外 2 + 公開 API 1）
- `tests/test_voice_listen_tool.py`（新規・3 件）
- `docs/tasks/.../task.md`（受入条件チェック）
- `docs/tasks/STATUS.md`（12/17）

実装ポイント:
- `listen()` は recorder → (timeout なら silent で短絡) → transcriber → (None/空/空白なら unintelligible) → `_strip_finalize_word` → (除去後に空なら unintelligible) → `ListenResult(text, "ok")` の順
- `_strip_finalize_word` は末尾の空白・句読点 (`。、！？.,!? + 改行 + 全角空白`) を一旦剥がしてから `endswith(word)` で 1 回だけ除去
- recorder / transcriber の各例外を別経路で捕捉して `ListenResult("", "unintelligible")` + stderr ログにマップ
- 受入条件 4 (実マイク発話) は Claude Code 再起動 + 実マイク必要のため task-executor では機械検証せず手動検証扱い
- pytest 94 件 pass + 1 件 skip (faster-whisper の CUDA 統合のみ)

### 関数 / API シグネチャ

```python
# listen/__init__.py
def listen() -> ListenResult: ...

# server.py（追加）
def voice_listen() -> ListenResult: ...   # listen.listen の薄いラッパ
```

### バリデーション・エラー処理

- recorder / transcriber の各失敗を status にマップ
- 例外発生時は `ListenResult("", "unintelligible")` をデフォルトに stderr ログ

### エッジケース

- transcript の末尾改行 / 句読点を含む形でも `finalize_word` 除去が機能する（末尾空白・句読点を許容するトリム）
- 同じ partial 検出と最終 transcribe で「以上」が二重に出ても 1 回除去で十分

## 依存関係

- 前提: 03-voice-input-listen/02-transcribe-and-expose-tool/01-implement-faster-whisper-transcriber, 03-voice-input-listen/01-record-and-finalize/02-add-vosk-streaming-and-finalize-word
- ブロックする: 04-voice-chat-loop/01-voice-chat-command-and-loop

理由: recorder と transcriber の両方が揃って初めて listen() を組める。ループは voice_listen を前提にする。

## スコープ外

- status を見た後の分岐（Epic 04 のループ指示）
- 暫定表示

## 補足

- [ADR-0003](../../../../adr/0003-dual-engine-streaming-listen.md)
- 関連設計:
  - [design.md#インターフェース](../../../../design/design.md#インターフェース)（MCP ツール voice_listen / listen 公開 API）
  - [design.md#相互作用状態エラー方針](../../../../design/design.md#相互作用状態エラー方針)（listen フロー全体）
  - [design.md#データモデル](../../../../design/design.md#データモデル)（ListenResult / status マッピング）
