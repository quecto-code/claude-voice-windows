---
type: task
title: vosk 日本語モデルを DL して配置する
label: must-have
depends_on: []
---

## 背景

親 Story `00-environment-setup/02-external-services` の一部として、vosk の日本語モデル（`vosk-model-ja-0.22` 想定）を DL し、`config.VOSK_MODEL_PATH` の既定先に配置する。

親 Story: 00-environment-setup/02-external-services

## 受入条件

- [x] `models/vosk-model-ja-0.22/` ディレクトリが存在する → `1.6GB`、配下 7 サブディレクトリ
- [x] その配下に少なくとも `conf/`, `am/`, `ivector/`, `graph/` のいずれか主要サブディレクトリが含まれる（vosk の典型構造）→ **4 つ全て**揃った: `conf/` `am/` `ivector/` `graph/`（加えて `rescore/` と `README`）
- [x] `models/` が `.gitignore` に追加されており、リポジトリにモデル本体が混入しない → `git check-ignore models/vosk-model-ja-0.22` で確認
- [x] DL 元 URL と展開コマンドが後続 Story 03 の README に記載される → 下の「変更ファイル」に記録（Story 03 で README に転記）

## 仕様詳細

### 変更ファイル

- `.gitignore`（新規・このブランチでは `models/` 1 行）
- `models/vosk-model-ja-0.22/`（DL 物・git 管理外）
- `docs/tasks/.../task.md`（受入条件チェック）
- `docs/tasks/STATUS.md`（進捗更新）

**配置先と DL 手順（Story 03 で README に転記する想定）**:
- **モデル名**: `vosk-model-ja-0.22`
- **配置先**: `<repo>/models/vosk-model-ja-0.22/`
- **DL 元 URL**: `https://alphacephei.com/vosk/models/vosk-model-ja-0.22.zip`（約 1.04GB）
- **DL & 展開コマンド**:
  ```bash
  mkdir -p models && cd models
  curl -fL -O https://alphacephei.com/vosk/models/vosk-model-ja-0.22.zip
  7z x vosk-model-ja-0.22.zip   # unzip でも可
  rm vosk-model-ja-0.22.zip
  ```
- **展開後の確認**: `ls models/vosk-model-ja-0.22/` に `conf/ am/ ivector/ graph/ rescore/` が並べばOK
- **`config.VOSK_MODEL_PATH` の既定値**: `models/vosk-model-ja-0.22`（Epic 01 で `config.py` に反映する想定）

### 関数 / API シグネチャ

該当なし

### バリデーション・エラー処理

- ZIP 展開後にサブディレクトリ構造を `ls` で確認する手順を README に残す

### エッジケース

- DL サイズが約 1GB と大きい。Windows ネイティブのローカルディスク（プロジェクト直下 `models/`）に配置する（[ADR-0005](../../../../adr/0005-windows-native-audio-path.md)）
- 別バージョン（`vosk-model-small-ja-*` 等）を使う場合は `config.VOSK_MODEL_PATH` を上書きすればよい旨を README に明記

## 依存関係

- 前提: なし
- ブロックする: 03-voice-input-listen/01-record-and-finalize/02-add-vosk-streaming-and-finalize-word

理由: vosk Recognizer の初期化に実モデルが必要。

## スコープ外

- モデルの精度評価
- 複数モデルの切り替え自動化

## 補足

- vosk モデルの配布元: alphacephei の公開リポジトリ（URL は README に記載）
