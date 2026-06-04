---
type: epic
title: MCP サーバ基盤
label: must-have
depends_on:
  - 00-environment-setup
---

## 背景・目的

claude-voice は Claude Code が stdio で起動する MCP サーバとして動く（[ADR-0001](../../adr/0001-mcp-tool-driven-turn-based.md)）。後続の音声入力（listen）・音声出力（speak）はすべてこのサーバ上のツールとして載るため、サーバ雛形・共有モジュール（types / config）・最小の MCP 疎通が成立していることが全機能の前提となる。

## ゴール・成功基準

- `claude-voice` MCP サーバが Claude Code から起動・認識され、ツール一覧に `voice_ping` が現れて疎通する。
- ベース型（`FinalizeReason` / `ListenResult` / `SpeakResult`）と設定モジュール（`config.py`）が、listen / speak から再利用できる形で存在する。

## 想定ユーザー

開発者（作者自身）。直接は触れず、後続 Epic のツールを載せる土台として機能する。

## 主要なユースケース

- ユースケース 1: Claude Code 起動時に claude-voice が子プロセスとして立ち上がる
- ユースケース 2: Claude が claude-voice の提供するツールを呼べる（最小: `voice_ping`）

## スコープ

### 含むもの (in scope)

- Python パッケージ構成（`pyproject.toml` / `src/claude_voice/` / `__init__.py` / `__main__.py`）
- `types.py`（`FinalizeReason` / `ListenResult` / `SpeakResult`）
- `config.py`（しきい値・モデル名・VOICEVOX URL・speaker id・確定ワードを定数 + env 上書き）
- `server.py`（MCP サーバ、`voice_ping` のみ登録）
- Claude Code 設定への登録

### 含まないもの (out of scope)

- 実際の録音・再生・STT・TTS ロジック（Epic 02 / 03）
- `/voice-chat` スラッシュコマンド（Epic 04）

## 配下 Story（計画）

- `01-server-skeleton` MCP サーバの雛形と共有モジュールを整え Claude Code に認識させる

## 依存関係

- 前提: なし
- 関連: `02-voice-output-speak` / `03-voice-input-listen`（本基盤に依存）

## リスク・未決事項

特になし。

## 補足

- アーキテクチャ根拠: [ADR-0001](../../adr/0001-mcp-tool-driven-turn-based.md)
- 関連設計: [design.md#構成](../../design/design.md#構成) / [design.md#データモデル](../../design/design.md#データモデル) / [design.md#インターフェース](../../design/design.md#インターフェース)
