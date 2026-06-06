---
type: task
title: 再生音質の歪みを解消する
label: must-have
depends_on:
  - 02-voice-output-speak/01-synthesize-and-play/02-implement-player-and-expose-voice-speak-tool
---

## 背景

親 Story `02-voice-output-speak/01-synthesize-and-play` の追加タスク。VOICEVOX は 24kHz で合成する。WSL2 時代は 24kHz のまま WSLg PulseAudio に渡すと内部リサンプリング/バッファ不足で「カリカリ・プツプツ」歪みが乗ったため `sox` でバッファ拡大＋高品質リサンプリングして解消した。**Windows ネイティブ（[ADR-0005](../../../../adr/0005-windows-native-audio-path.md)）ではこの WSLg 由来の歪みは発生しない**が、`--buffer` / `rate -v` は underrun 耐性の保険として残す（既定で無害、Audio Quality NFR は存続）。

> 本タスクは既存タスク `02-.../02-implement-player...`（完了済み）の**後発の品質改善**であり、元タスクを reopen せず新タスクとして追加した（[CH-001](../../../../changes/CHANGELOG.md)、spec-amend 経由）。元タスクの受入条件「`sox … default` 相当」は本変更後も満たされる。

親 Story: 02-voice-output-speak/01-synthesize-and-play

## 受入条件

- [x] `src/claude_voice/speak/player.py` の `sox` 起動に `--buffer <SOX_BUFFER_BYTES>` と末尾の `rate -v <PLAYBACK_SAMPLE_RATE>` を追加し、再生バッファ不足（underrun）由来の歪みを回避する → mock で sox 引数を確認（`tests/test_player.py`）
- [x] `src/claude_voice/config.py` に `PLAYBACK_SAMPLE_RATE`（既定 48000）と `SOX_BUFFER_BYTES`（既定 32768）を追加し、`CLAUDE_VOICE_PLAYBACK_SAMPLE_RATE` / `CLAUDE_VOICE_SOX_BUFFER_BYTES` で env 上書き可能にする
- [x] `tests/test_player.py` に sox コマンドの `--buffer` と `rate -v <PLAYBACK_SAMPLE_RATE>` を検証するテストを追加し pass する

## 仕様詳細

### 変更ファイル

- `src/claude_voice/config.py`（`PLAYBACK_SAMPLE_RATE` / `SOX_BUFFER_BYTES` 追加）
- `src/claude_voice/speak/player.py`（sox コマンドに `--buffer` + `rate -v` を追加、`config` を参照）
- `tests/test_player.py`（再生品質テスト 1 件追加）

### 関数 / API シグネチャ

該当なし（`play(wav: bytes) -> bool` のシグネチャは不変。内部の sox 引数のみ変更）

### エッジケース

- 実測で 24kHz そのまま再生（A）と 48kHz 高品質変換＋バッファ拡大（B）を比較し、B でプツプツが解消することを確認済み（人耳判定・手動検証）

## 依存関係

- 前提: 02-voice-output-speak/01-synthesize-and-play/02-implement-player-and-expose-voice-speak-tool
- ブロックする: なし

理由: 既存の player 実装の上に、再生品質の調整を載せる。

## スコープ外

- VOICEVOX 側の出力サンプルレート変更（対策1）。今回は再生側（sox）で完結する対策2を採用

## 補足

- [CH-001](../../../../changes/CHANGELOG.md)（spec-amend による変更履歴）
- requirements: Audio Quality NFR（歪み・ノイズなく明瞭に再生）
- 関連設計: [design.md#構成](../../../../design/design.md#構成)（player.py の sox 再生・config 責務）
