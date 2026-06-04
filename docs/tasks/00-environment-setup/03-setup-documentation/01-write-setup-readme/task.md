---
type: task
title: セットアップ手順 README を書く
label: must-have
depends_on: []
---

## 背景

親 Story `00-environment-setup/03-setup-documentation` の一部として、README.md を作成（または既存に追記）し、前提条件・セットアップ・起動・git remote 方針を集約する。

親 Story: 00-environment-setup/03-setup-documentation

## 受入条件

- [x] プロジェクト直下に `README.md` が存在する → 124 行
- [x] `grep -E '^## (前提条件|セットアップ|起動|git remote 方針)' README.md | wc -l` が `4` を返す → 4
- [x] `## セットアップ` 節に次のコマンド類が記載されている: `uv venv` 系の作成手順・VOICEVOX エンジンの起動コマンド・vosk モデルの DL/展開コマンド → `uv venv` / `voicevox-engine/linux-nvidia/run --use_gpu` / `vosk-model-ja-0.22.zip` を grep 確認
- [x] `## 起動` 節に `python -m claude_voice`（または `.venv/bin/python -m claude_voice`）が含まれている
- [x] `## git remote 方針` 節に「使う」または「使わない」が明記され、使う場合は remote 名と URL の記入欄がある → 「使う」、`origin` / `git@github.com:quecto-code/claude-voice.git` を明記

## 仕様詳細

### 変更ファイル

- `README.md`（新規執筆。main 上の既存ファイルは 0 行の空ファイルだったため実質新規）
- `docs/tasks/.../task.md`（受入条件チェック）
- `docs/tasks/STATUS.md`（進捗更新）

README に含めた節:
- **前提条件**: OS / Python / uv / 7z / curl / GPU / 音声 I/O
- **セットアップ**: ① venv 構築 ② VOICEVOX エンジン DL & 起動 ③ vosk モデル DL & 配置
- **起動**: `python -m claude_voice` + 環境変数表（`CLAUDE_VOICE_*` で `config.py` を上書き）
- **git remote 方針**: 使う / `origin` / `git@github.com:quecto-code/claude-voice.git` / `main`

### 関数 / API シグネチャ

該当なし

### バリデーション・エラー処理

- 既存 README がある場合は節の差分追加のみ（既存節の上書き禁止）

### エッジケース

- VOICEVOX エンジンの配置先パスが固定でない場合は環境変数で差し替える旨を `config.py` の説明として README に書く
- vosk モデルバージョン違いを許容するため `config.VOSK_MODEL_PATH` の差し替え方を README に書く

## 依存関係

- 前提: なし
- ブロックする: なし

理由: 書く内容は親 Story 経由で他タスクの結果から確定する。

## スコープ外

- 詳細な使い方ガイド（`/voice-chat` の体験談など）
- バッジ・ロゴ等の見栄え整備

## 補足

- 本タスクは task-executor の push 動作にも直結するため、git remote 方針は曖昧にせず明確に書く
