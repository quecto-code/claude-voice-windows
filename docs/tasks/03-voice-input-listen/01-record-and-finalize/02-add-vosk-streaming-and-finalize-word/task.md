---
type: task
title: vosk 供給と確定ワード SIGTERM を recorder に追加する
label: must-have
depends_on:
  - 03-voice-input-listen/01-record-and-finalize/01-scaffold-recorder-sox-subprocess
---

## 背景

親 Story `03-voice-input-listen/01-record-and-finalize` の後半として、`recorder.py` の読取スレッドで vosk Recognizer に PCM を逐次供給し、確定ワード「以上」を検出した時点で sox を SIGTERM して `FinalizeReason.word` で確定させる（[ADR-0003](../../../../adr/0003-dual-engine-streaming-listen.md)、[design.md 設計判断 2](../../../../design/design.md#主要な設計判断とその理由)）。

親 Story: 03-voice-input-listen/01-record-and-finalize

## 受入条件

- [x] `recorder.py` の `record()` 内で、`config.VOSK_MODEL_PATH` から vosk Model をロードし、Recognizer を 16kHz で初期化する → `vosk.Model` と `vosk.KaldiRecognizer` を mock し、Model 引数が `config.VOSK_MODEL_PATH` に一致 / Recognizer の第 2 引数 == 16000 を検証
- [x] 読取スレッドが PCM チャンクを (a) 全 PCM バッファに蓄積、(b) vosk Recognizer に `AcceptWaveform` で供給する → `_FakeRecognizer.accept_calls` と `pcm == loud+loud` を同時検証
- [x] vosk の partial result（JSON）に `finalize_word` が含まれた時点で sox に `terminate()`（SIGTERM）を送る → `_FakeRecognizer` の partial を「以上」を含む値に切り替えると `terminate_called == True` になることを確認 + 連続検出で複数回呼ばれない（`word_detected.is_set()` で 1 回ガード）
- [x] SIGTERM 起因で sox が終了したら `(bytes(buffer), FinalizeReason.word)` を返す → 同シナリオで戻り値が `FinalizeReason.word` + buffer 非空
- [x] sox 自然終了（無音）→ `FinalizeReason.silence`、onset timeout → `FinalizeReason.timeout` → 既存テスト 8 件を維持
- [x] vosk モデルロード失敗を捕捉し `(b"", FinalizeReason.timeout)` を返し stderr ログ → `vosk.Model` が `RuntimeError` を投げると sox は起動せず timeout で返り `vosk model load error` ログ。`KaldiRecognizer` 失敗時も同様
- [x] 読取スレッドは 1 本のまま → `threading.active_count()` を録音中ピーク監視し reader 1 本のみ（watcher 込み +2 以下）を確認
- [x] 例外を上位に伝播させない → `vosk.AcceptWaveform` に `RuntimeError` を仕込んでも `record()` は silence で帰る + reader 内例外 + JSON デコード失敗の 3 ケース

## 仕様詳細

### 変更ファイル

- `src/claude_voice/listen/recorder.py`（既存に vosk 統合を追加・`_vosk_model` シングルトン、`_get_vosk_model` / `_partial_text` ヘルパ、reader 内 `AcceptWaveform` + partial 検出ロジック、`word_detected: threading.Event` で重複 SIGTERM ガード、戻り値分岐に `FinalizeReason.word` 経路を追加）
- `tests/test_recorder.py`（vosk 関連 10 件追加、既存 8 件は `_patch_vosk` 経由に書き換えて維持。計 18 件）
- `docs/tasks/.../task.md`（受入条件チェック）
- `docs/tasks/STATUS.md`（10/17）

実装ポイント:
- `vosk.Model` はモジュールスコープでシングルトン化（`_vosk_model_lock` 保護）。`KaldiRecognizer` は record 呼び出しごとに作る（状態を持つため）
- `_partial_text` で JSON デコード失敗を吸収（vosk バージョン差で出力形式が違うケースに備える）
- 確定ワード SIGTERM は `word_detected: threading.Event` で 1 回限りにガード
- vosk 初期化失敗 / `Recognizer` 失敗 / `AcceptWaveform` 中の例外 / `Popen` 失敗を全て stderr ログ + `FinalizeReason.timeout` (sox 起動済なら non-zero 経路) にマップ
- スレッド数は前タスクから増やさず reader 1 本のみ。vosk 推論は同スレッドで逐次
- pytest 55 件全 pass（既出 37 + recorder 18）

### 関数 / API シグネチャ

```python
def record(finalize_word: str,
           silence_sec: float,
           onset_timeout_sec: float) -> tuple[bytes, FinalizeReason]: ...
# 前タスクと同じシグネチャ。中身に vosk 供給と確定ワード SIGTERM を追加。
```

### バリデーション・エラー処理

- vosk モデル未配置 → ログ + reason=timeout
- partial 結果が JSON でなければ無視（vosk のバージョン差に備える）

### エッジケース

- `finalize_word` が指示本文に紛れて早期 SIGTERM される（許容、`config.FINALIZE_WORD` で語を変更可）
- 連続した partial 更新で同じ語が繰り返し出る場合、最初の検出で SIGTERM して以降は無視
- SIGTERM 直後にも数チャンクが届きうる：それらも buffer に追加してから返す（取りこぼし最小化）

## 依存関係

- 前提: 03-voice-input-listen/01-record-and-finalize/01-scaffold-recorder-sox-subprocess
- ブロックする: 03-voice-input-listen/02-transcribe-and-expose-tool/02-implement-listen-pipeline-and-expose-tool

理由: sox + 読取スレッドの骨格に vosk を重ねる順序。

## スコープ外

- 最終文字起こし（faster-whisper、別 Story）
- 確定ワードの transcript からの除去（transcriber 側で対応）

## 補足

- [ADR-0003](../../../../adr/0003-dual-engine-streaming-listen.md)
- 関連設計:
  - [design.md#相互作用状態エラー方針](../../../../design/design.md#相互作用状態エラー方針)（listen フローの vosk 部分・FinalizeReason.word での停止）
  - [design.md#データモデル](../../../../design/design.md#データモデル)（FinalizeReason）
