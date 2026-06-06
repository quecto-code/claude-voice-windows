---
type: epic
title: 環境構築
label: must-have
depends_on: []
---

## 背景・目的

claude-voice は Python ランタイム・MCP SDK・faster-whisper・vosk・VOICEVOX エンジン・sox など、複数の外部依存と重い静的データ（vosk モデル）に乗っている。これらが揃っていないと、後続の MCP サーバ／speak／listen のいかなる実装タスクも実機で受入確認できない。この Epic でコードを書く前の前提を整える。

実装系の各 Epic（01〜04）は本 Epic に `depends_on` する。

## ゴール・成功基準

- `.venv/` が存在し `python` と `pytest` が動く
- VOICEVOX エンジンがローカルで起動でき、`/version` が 200 を返す
- vosk 日本語モデルが既定の配置先に置かれている
- README.md の手順どおりにクローン → 起動が再現できる
- git remote の方針（GitHub 等に push する／ローカルのみ）が確定し記録されている

## 想定ユーザー

開発者（作者自身）。本 Epic の成果物は実装フェーズ全体の前提条件として消費される。

## 主要なユースケース

- 新しい開発環境で README を見て手順を踏むと claude-voice の MCP サーバが起動する状態に到達できる
- 後続 Epic のタスクが、依存ライブラリと外部サービスの存在を前提に安全に実装着手できる

## スコープ

### 含むもの (in scope)

- Python 仮想環境（uv による `.venv` 構築）と pytest 初期スキャフォールド
- VOICEVOX 音声合成エンジン（**Windows 版**、[ADR-0005](../../adr/0005-windows-native-audio-path.md)）の DL と起動手段の整備
- vosk 日本語モデル（vosk-model-ja-0.22 を想定）の DL と配置
- セットアップ手順 README（前提条件・起動方法・git remote 方針）

### 含まないもの (out of scope)

- 実装コード（`src/claude_voice/` 配下）は本 Epic では作らない（Epic 01）
- pyproject.toml への**実装依存**（mcp / faster-whisper / vosk / requests）の追加。これは Epic 01 のスキャフォールド時に `uv add` で行う。本 Epic は venv 雛形（pytest など dev 系のみ）まで
- CI 設定（個人プロジェクトのため対象外）

## 配下 Story（計画）

- `01-local-runtime` ローカル開発環境（venv + pytest 雛形）
- `02-external-services` 外部依存（VOICEVOX エンジン・vosk モデル）
- `03-setup-documentation` セットアップ手順を README に記す

## 依存関係

- 前提: なし
- ブロックする: `01-mcp-server-foundation`, `02-voice-output-speak`, `03-voice-input-listen`, `04-voice-chat-loop`（後続 Epic 全て）

理由: 全実装タスクの前提条件。これが整わないと受入確認できない。

## リスク・未決事項

- git remote 方針は未確定（GitHub 等を使うか、ローカルのみか）。`03-setup-documentation/01-write-setup-readme` で確定する
- VOICEVOX Windows 版の正確な配置先（VOICEVOX アプリ同梱 / エンジン単体配布）は実装時に決める

## 補足

- 本 Epic は ADR・design.md の対象外（環境構築は設計判断ではなく前提条件）
- 関連ファイル予定: `README.md`, `.venv/`, `models/vosk-model-ja-0.22/`, VOICEVOX エンジン起動スクリプトまたは手順
