---
type: task
title: VOICEVOX 合成クライアントを実装する
label: must-have
depends_on: []
---

## 背景

親 Story `02-voice-output-speak/01-synthesize-and-play` の一部として、テキストから VOICEVOX で WAV を生成する関数を実装する。

親 Story: 02-voice-output-speak/01-synthesize-and-play

## 受入条件

- [x] `src/claude_voice/speak/synthesizer.py` に `synthesize(text: str, speaker: int) -> bytes | None` が実装されている → シグネチャ検証 pytest 1 件
- [x] `POST {config.VOICEVOX_URL}/audio_query?text=<text>&speaker=<speaker>` を呼び audio_query JSON を取得する → mock で呼び出し順・URL・params 確認 + 実 VOICEVOX 統合テスト
- [x] 続いて `POST {config.VOICEVOX_URL}/synthesis?speaker=<speaker>` に audio_query JSON を body として送り、レスポンスを WAV bytes として返す → 同上、統合テストで RIFF ヘッダ + 長さ > 1000 確認
- [x] エンジン未起動 / HTTP 非 200 / タイムアウト / 接続失敗を捕捉して `None` を返し、stderr に理由をログ出力する → audio_query 5xx / synthesis 5xx / 空 body / ConnectionError / Timeout / JSON decode error の 6 パターン pytest
- [x] 空文字 text の場合は HTTP を呼ばず `None` を返す → mock の call_count == 0 確認
- [x] 例外を上位に伝播させない → 任意の `RuntimeError` を仕込んでも `None` 返却を確認

## 仕様詳細

### 変更ファイル

- `src/claude_voice/speak/__init__.py`（新規・空、speak サブパッケージ初期化）
- `src/claude_voice/speak/synthesizer.py`（新規・`synthesize` 関数）
- `tests/test_synthesizer.py`（新規・unittest.mock による単体 11 件 + 実 VOICEVOX 統合 1 件）
- `docs/tasks/.../task.md`（受入条件チェック）
- `docs/tasks/STATUS.md`（7/17）

実装ポイント:
- timeout: 接続 3.0s / 読取 10.0s（task 仕様の合理的デフォルト）
- 失敗時の stderr ログは `voicevox audio_query failed` / `voicevox synthesis failed` / `voicevox synthesize error` で type 別に出し分け
- 例外捕捉は最も外側 `try: ... except Exception as e:` で全例外を `None` にマップ
- `config.VOICEVOX_URL` を参照、speaker は呼び出し側から受け取るだけ（design 通り）

### 関数 / API シグネチャ

```python
def synthesize(text: str, speaker: int) -> bytes | None:
    """VOICEVOX エンジンに合成リクエストし WAV bytes を返す。失敗時 None。"""
```

### バリデーション・エラー処理

- HTTP タイムアウトは合理的なデフォルト（例: 接続 3s / 読取 10s）を設定
- 5xx / 接続失敗 / JSON デコード失敗 / 空ボディを `None` にマップ

### エッジケース

- VOICEVOX エンジンの起動先 URL（既定 `http://127.0.0.1:50021`）は `config.VOICEVOX_URL` から取り、env で差し替え可能
- speaker は `config.SPEAKER_ID` を呼び出し側で渡す（synthesizer は素直に受け取るだけ）

## 依存関係

- 前提: なし
- ブロックする: 02-voice-output-speak/01-synthesize-and-play/02-implement-player-and-expose-voice-speak-tool

理由: 合成ができてから再生・ツール公開につなぐ。

## スコープ外

- 音声の再生（次タスク）
- 直列化ロック（speak/__init__.py 側で扱う）

## 補足

- 関連設計:
  - [design.md#インターフェース](../../../../design/design.md#インターフェース)（外部 API VOICEVOX のエンドポイント・各モジュール責務 IF）
  - [design.md#相互作用状態エラー方針](../../../../design/design.md#相互作用状態エラー方針)（speak フロー・失敗モード「VOICEVOX 接続不可」）
