---
type: story
title: 発話を録音し沈黙または確定ワードで確定する
label: must-have
depends_on:
  - 01-mcp-server-foundation/01-server-skeleton
---

## 背景・目的

マイクから録音し、「一定時間の無音」「確定ワード『以上』」「発話開始タイムアウト」のいずれかで録音を終わらせる関数を `recorder.py` に実装する。`design.md` 設計判断 2 の通り **sox 子プロセス + 単一読取スレッド + vosk + SIGTERM** で実装する（[ADR-0003](../../../adr/0003-dual-engine-streaming-listen.md)）。

## ユーザーストーリー

**As a** 口頭で指示を出したい開発者
**I want to** 喋り終わりを黙るか「以上」と言うかで確定したい
**So that** 自然な発話のまま、待たされずに指示を送れる

## 受入条件

- [ ] `src/claude_voice/listen/recorder.py` に `record(finalize_word: str, silence_sec: float, onset_timeout_sec: float) -> tuple[bytes, FinalizeReason]` が実装されている
- [ ] sox を `sox -t pulseaudio default -r 16000 -c 1 -t raw -e signed -b 16 - silence 1 0.05 1% 1 {silence_sec} 1%` で起動し、stdout から raw PCM（16kHz/mono/s16le）を読み取れる
- [ ] sox が無音 `silence_sec` 秒で自然終了 → `reason=FinalizeReason.silence`、確定 PCM を返す
- [ ] 録音中の PCM チャンクを vosk Recognizer に逐次供給し、partial 結果に `finalize_word` を検出した時点で sox に SIGTERM → `reason=FinalizeReason.word`、確定 PCM を返す
- [ ] 発話開始（最初の振幅閾値超え）が `onset_timeout_sec` 秒以内に観測されない場合、sox を kill → `reason=FinalizeReason.timeout`、空 bytes を返す
- [ ] 単一読取スレッドで実装され、メイン以外のスレッドは 1 本のみ。lock 不要
- [ ] マイク不可・vosk モデル未配置など任意の失敗で例外を投げず、`(b"", FinalizeReason.timeout)` 等で返し stderr にログ出力

## 仕様詳細

### UI / 画面

なし（将来 vosk partial を画面に出す余地は残すが本 Story では対象外）

### API / Server Action

- 内部関数: `recorder.record(finalize_word, silence_sec, onset_timeout_sec) -> (bytes, FinalizeReason)`

### データモデル

- `FinalizeReason`（`types.py`）: `silence | word | timeout`
- 録音 PCM は `bytes`（16kHz/mono/s16le、ヘッダなし raw）

### バリデーション

- 引数のしきい値は `config.SILENCE_SEC` / `config.ONSET_TIMEOUT_SEC` / `config.FINALIZE_WORD` をデフォルトに

### エラーハンドリング

- sox 起動失敗 → `(b"", FinalizeReason.timeout)` + stderr ログ
- vosk モデル未配置 → 同上
- 録音中の例外を全て捕捉し、上位（`listen()`）が status="silent" にマップできるようにする

### エッジケース

- `finalize_word` が指示本文に紛れて早期確定するケース（許容、調整余地として `config.FINALIZE_WORD` で別の語に変更可能）
- 振幅閾値の決め方は実装時にチューニング（簡易 VAD として 16bit PCM の絶対値平均など）

## 依存関係

- 前提（着手前に完了が必要）: `01-mcp-server-foundation/01-server-skeleton`
- ブロックする: `03-voice-input-listen/02-transcribe-and-expose-tool`

理由: 確定音声 PCM がないと文字起こしできない。

## スコープ外

- 最終文字起こし（次 Story の faster-whisper）
- silent/unintelligible 後の分岐（Epic 04）

## 補足

- [ADR-0003](../../../adr/0003-dual-engine-streaming-listen.md)
- 関連設計:
  - [design.md#構成](../../../design/design.md#構成)（listen/ サブパッケージ責務）
  - [design.md#データモデル](../../../design/design.md#データモデル)（FinalizeReason）
  - [design.md#インターフェース](../../../design/design.md#インターフェース)（recorder.record のシグネチャ）
  - [design.md#相互作用状態エラー方針](../../../design/design.md#相互作用状態エラー方針)（listen フローの recorder 部分・状態遷移 waiting_onset → recording → finalized）
