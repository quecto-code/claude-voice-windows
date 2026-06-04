---
type: task
title: sox 子プロセスと読取スレッドの骨格を作る
label: must-have
depends_on: []
---

## 背景

親 Story `03-voice-input-listen/01-record-and-finalize` の前半として、`recorder.py` に sox サブプロセス起動・stdout 読取スレッド・onset timeout・sox 自然終了による silence 確定を実装する（vosk と確定ワード検出は次タスクで追加）。

親 Story: 03-voice-input-listen/01-record-and-finalize

## 受入条件

- [x] `src/claude_voice/listen/recorder.py` に `record(finalize_word: str, silence_sec: float, onset_timeout_sec: float) -> tuple[bytes, FinalizeReason]` の関数骨格が存在する → シグネチャ検証 pytest 1 件、`finalize_word` は `del` で明示的に未使用
- [x] sox を仕様どおりのコマンドで起動する → mock の Popen 呼出引数で 4-token プレフィックス・raw/signed/16bit・silence エフェクト + `silence_sec` の文字列化を検証
- [x] 単一読取スレッドが stdout から 4096 バイトずつ読み bytearray に蓄積する → `loud` 2 チャンクを流して `pcm == loud + loud` を検証 + `_chunk_amplitude` 単体テスト
- [x] sox 自然終了で `(bytes(buffer), FinalizeReason.silence)` → 蓄積テストで同時確認
- [x] onset timeout で sox を `terminate()` → `(b"", FinalizeReason.timeout)` → 永続無音ストリーム + `onset_timeout_sec=0.2` で `terminate_called == True` と elapsed < 2s を検証
- [x] sox 起動失敗で `(b"", FinalizeReason.timeout)` + stderr ログ → `FileNotFoundError` / 任意 `PermissionError` / 非 0 終了 の 3 ケース
- [x] 例外を上位に伝播させない → reader 内で `RuntimeError` を仕込んでも `record()` が完走し `pcm == b""` を返すことを確認

## 仕様詳細

### 変更ファイル

- `src/claude_voice/listen/__init__.py`（新規・空、listen サブパッケージ初期化）
- `src/claude_voice/listen/recorder.py`（新規・`record` 関数 + `_build_sox_command` / `_chunk_amplitude` ヘルパ）
- `tests/test_recorder.py`（新規・unittest.mock 9 件）
- `docs/tasks/.../task.md`（受入条件チェック）
- `docs/tasks/STATUS.md`（9/17）

実装ポイント:
- sox コマンドは仕様の引数列をそのまま `subprocess.Popen` に渡す（`-r 16000 -c 1 -t raw -e signed -b 16 -` + `silence 1 0.05 1% 1 {silence_sec} 1%`）
- onset 判定は `int16` LE PCM の絶対値平均 > 500 を閾値（暫定値・将来 `config` 化可）
- 単一読取スレッド (`daemon=True`) + メインの `time.sleep(0.05)` ポーリングで sox の自然終了 / onset timeout / 起動失敗の 3 経路を捌く
- onset timeout 時は `proc.terminate()` → `proc.wait(timeout=1.0)` → 必要なら `proc.kill()`
- 例外はすべて stderr ログ + `(b"", FinalizeReason.timeout)` にマップ
- `finalize_word` は本タスク範囲では未使用なので `del finalize_word` で明示
- pytest 46 件全 pass（既出 37 + 新 9）

### 関数 / API シグネチャ

```python
def record(finalize_word: str,
           silence_sec: float,
           onset_timeout_sec: float) -> tuple[bytes, FinalizeReason]:
    """sox 子プロセスで録音し、無音 / タイムアウトで停止して PCM と FinalizeReason を返す。
    本タスクでは finalize_word は未使用（次タスクで vosk と統合）。"""
```

### バリデーション・エラー処理

- sox の終了コード非 0 はログを残し timeout 扱いにする
- onset 検出はシンプルに「チャンクの int16 絶対値平均 > 閾値」（閾値は内部定数として暫定値、将来 config 化可）

### エッジケース

- 無音のまま onset_timeout_sec 経過 → reason=timeout
- 入力ゲインが極端に低いとき：onset 検出されず timeout になる（許容）
- sox が起動できない（バイナリ未配置）→ stderr ログ + reason=timeout

## 依存関係

- 前提: なし
- ブロックする: 03-voice-input-listen/01-record-and-finalize/02-add-vosk-streaming-and-finalize-word

理由: sox + 読取スレッドの骨格が動いてから vosk を載せる。

## スコープ外

- vosk / 確定ワード検出（次タスク）
- 最終文字起こし

## 補足

- 関連設計:
  - [design.md#相互作用状態エラー方針](../../../../design/design.md#相互作用状態エラー方針)（listen フローの sox 部分・状態 waiting_onset → recording → finalized(silence|timeout)）
  - [design.md#インターフェース](../../../../design/design.md#インターフェース)（recorder.record シグネチャ）
