---
type: story
title: 外部依存（音声エンジンとモデル）を整える
label: must-have
depends_on:
  - 00-environment-setup/01-local-runtime
---

## 背景・目的

claude-voice は **VOICEVOX 音声合成エンジン**（Linux 版、ローカル HTTP）と **vosk 日本語モデル**（ストリーミング確定ワード検出用）を実機で要求する。これらが配置されていないと Epic 02（speak）・Epic 03（listen）の受入確認が成立しない。

## ユーザーストーリー

**As a** ローカル開発環境を整えた開発者
**I want to** VOICEVOX エンジンと vosk モデルを利用可能にしたい
**So that** speak / listen のタスクが実機で動作確認できる

## 受入条件

- [ ] VOICEVOX エンジンが起動でき、`curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:50021/version` が `200` を返す
- [ ] vosk 日本語モデル（`vosk-model-ja-0.22` 想定）が `models/vosk-model-ja-0.22/` に展開され、配下に `conf/`, `am/`, `ivector/` が存在する
- [ ] VOICEVOX エンジンの起動コマンドが文書化されている（後続 Story 03 の README に記載される）

## 仕様詳細

### UI / 画面

なし

### API / Server Action

- 外部 HTTP API: VOICEVOX `/version`（疎通確認）, `/audio_query`, `/synthesis`（実装は Epic 02）

### データモデル

なし

### バリデーション

- VOICEVOX `/version` の 200 応答
- vosk モデルディレクトリの主要サブディレクトリの存在

### エラーハンドリング

- エンジン未起動・モデル未配置のときの README 上の対処（後続 Story 03）

### エッジケース

- VOICEVOX のポートが他サービスと衝突するケース（既定 50021 を維持する想定）
- vosk モデルの ZIP が 1GB 超で DL に時間がかかる

## 依存関係

- 前提（着手前に完了が必要）: `00-environment-setup/01-local-runtime`
- ブロックする: `02-voice-output-speak`, `03-voice-input-listen`

理由: venv の上で `uv run` から VOICEVOX/vosk を叩く前提。

## スコープ外

- VOICEVOX の起動を systemd 等で自動化すること
- 複数モデルの管理（本プロジェクトは vosk-model-ja-0.22 のみ）

## 補足

- VOICEVOX Linux 版の配布元 / vosk モデルの DL URL は後続 Story 03 で README に明記する
