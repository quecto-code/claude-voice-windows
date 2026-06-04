---
type: task
title: uv で venv と pytest 雛形を作る
label: must-have
depends_on: []
---

## 背景

親 Story `00-environment-setup/01-local-runtime` の一部として、uv で `.venv` を作成し、pyproject.toml と pytest が走る最小スキャフォールドを用意する。

親 Story: 00-environment-setup/01-local-runtime

## 受入条件

- [x] `uv` がインストールされている（バージョン確認: `uv --version` が成功）→ `uv 0.11.16`
- [x] プロジェクト直下に `pyproject.toml` が存在し、`[project]` に `name = "claude-voice"`、`requires-python = ">=3.10,<3.12"` が含まれる
- [x] `uv venv --python 3.11`（または 3.10）で `.venv/` が作成され、`.venv/bin/python --version` が想定バージョンを返す → `Python 3.10.12`（3.11 は rc1 のため安定版の 3.10 を採用）
- [x] `uv add --dev pytest` で pytest が dev 依存に追加され、`.venv/bin/pytest --version` がエラーなく成功する → `pytest 9.0.3`
- [x] `tests/__init__.py` が存在する（空でよい）
- [x] `tests/test_smoke.py` が存在し、内容は `def test_smoke(): assert True`
- [x] `.venv/bin/pytest tests/` が 1 件以上 pass で終了する（return code 0）→ 1 passed
- [x] `uv.lock` が生成されている
- [x] `.gitignore` に `.venv/` が含まれている

## 仕様詳細

### 変更ファイル

- `pyproject.toml`（新規）
- `.gitignore`（新規）
- `tests/__init__.py`（新規）
- `tests/test_smoke.py`（新規）
- `uv.lock`（uv add で生成）
- `.venv/`（uv venv で生成、`.gitignore` 対象）

### 関数 / API シグネチャ

該当なし（環境セットアップ作業）

### バリデーション・エラー処理

- `uv` 未インストールの場合は事前に手動でインストールする旨を README に記す
- 既存の `.venv` がある場合はそのまま使い、Python バージョンが要件に合わなければ作り直す

### エッジケース

- Python 3.10 と 3.11 が両方ある環境では 3.11 を優先する（型ヒント記法の互換性のため）
- WSL2 上で `uv venv` が `/mnt/c/...` 配下を選ばないようプロジェクト直下で実行する

## 依存関係

- 前提: なし
- ブロックする: 00-environment-setup/02-external-services、その先の全実装タスク

理由: venv がなければ依存追加もテストもできない。

## スコープ外

- 実装依存（mcp / faster-whisper / vosk / requests）— Epic 01 で `uv add` する
- ruff / black などの lint・formatter 導入

## 補足

- `uv` のインストール手順は公式ドキュメント参照（外部 URL は README に書く）
