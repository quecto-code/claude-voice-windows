---
type: task
title: faster-whisper 文字起こしを実装する
label: must-have
depends_on: []
---

## 背景

親 Story `03-voice-input-listen/02-transcribe-and-expose-tool` の前半として、確定 PCM を faster-whisper で日本語文字起こしする関数を実装する。

親 Story: 03-voice-input-listen/02-transcribe-and-expose-tool

## 受入条件

- [x] `src/claude_voice/listen/transcriber.py` に `transcribe(pcm: bytes) -> str | None` が実装されている → シグネチャ検証 pytest
- [x] faster-whisper を `config.WHISPER_MODEL_SIZE`（既定 `"small"`）と CUDA で初期化（シングルトン化） → `WhisperModel` mock の呼出引数で `args[0]=="small"` / `kwargs["device"]=="cuda"` + 3 回 transcribe しても WhisperModel コンストラクタが 1 回のみ
- [x] 16kHz/mono/s16le の生 PCM を float32 numpy 配列に変換して `transcribe()` に渡す（language="ja"） → mock の transcribe 呼出引数で `np.ndarray` / `dtype == float32` / 振幅スケール (-1, 1) / `language=="ja"` を検証 + `_pcm_to_float32` ヘルパ単体テスト
- [x] セグメントを連結した文字列を返す → 3 セグメントの mock で `"こんにちは、世界。"` 連結を確認
- [x] 空 PCM / 極端に短い PCM (0.1 秒未満 = 3200 bytes) は推論せず `None` → `b""` / 3000 bytes で None + WhisperModel ロード呼ばれず。境界 3200 bytes で推論に進むことも確認
- [x] CUDA 利用不可・モデルロード失敗・推論失敗を捕捉し `None` + stderr ログ → `WhisperModel` を `RuntimeError` raise / `transcribe` 失敗 / `WhisperModel is None` (import 失敗想定) の 3 ケース + ロード失敗が記憶されて再試行しないことも確認
- [x] 例外を上位に伝播させない → 任意の `OSError` を仕込んでも `None` を返し例外を投げないこと

## 仕様詳細

### 変更ファイル

- `src/claude_voice/listen/transcriber.py`（新規・`transcribe(pcm) -> str | None`、`_get_model` シングルトン、`_pcm_to_float32` ヘルパ）
- `tests/test_transcriber.py`（新規・unittest.mock 15 件 + CUDA 統合テスト 1 件 (torch 未導入のため skip)）
- `docs/tasks/.../task.md`（受入条件チェック）
- `docs/tasks/STATUS.md`（11/17）

実装ポイント:
- `_MIN_PCM_BYTES = 3200` (16kHz/mono/s16le × 0.1 秒)
- `_model` + `_model_lock` + `_model_load_failed` の三点でロード結果をシングルトン化。失敗状態を記憶して再ロードしない (CUDA ドライバ無いマシンで毎回失敗ログを出すのを防ぐ)
- `_pcm_to_float32` で int16 LE → float32 [-1, 1] へ変換。奇数長は末尾 1 バイトを捨てて読む
- 推論結果は `"".join(seg.text for seg in segments).strip()`。空白だけなら `or None` で None に倒す
- faster-whisper 本体のインポート失敗にも `WhisperModel is None` 経路で対応
- pytest 70 件 pass + 1 件 skip (CUDA 統合は torch 未導入のためスキップ)

### 関数 / API シグネチャ

```python
def transcribe(pcm: bytes) -> str | None:
    """16kHz/mono/s16le の生 PCM を faster-whisper で文字起こし。
    失敗・空・極短入力で None。"""
```

### バリデーション・エラー処理

- PCM 長 < 一定（例: 0.1 秒 = 3200 bytes）→ None
- モデル初回ロードの失敗をシングルトン側で捕捉

### エッジケース

- CUDA 利用不可時の挙動（None を返す or CPU フォールバック）を決める。本タスクではログ + None で十分
- 結果テキストが空白だけの場合 None 扱い

## 依存関係

- 前提: なし
- ブロックする: 03-voice-input-listen/02-transcribe-and-expose-tool/02-implement-listen-pipeline-and-expose-tool

理由: 文字起こしの上で listen() パイプラインと voice_listen ツールを組む。

## スコープ外

- 確定ワード「以上」の除去（listen() 側で行う）
- ストリーミング暫定表示（vosk 側の責務）

## 補足

- GPU: RTX 3050 8GB / `libcuda.so` は WSL から利用可（確認済み）
- [ADR-0003](../../../../adr/0003-dual-engine-streaming-listen.md)
- 関連設計:
  - [design.md#インターフェース](../../../../design/design.md#インターフェース)（transcribe シグネチャ）
  - [design.md#相互作用状態エラー方針](../../../../design/design.md#相互作用状態エラー方針)（unintelligible 失敗パス）
