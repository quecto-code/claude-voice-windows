---
type: story
title: ローカル開発環境を整える
label: must-have
depends_on: []
---

## 背景・目的

Python 仮想環境（uv による `.venv`）と pytest 初期スキャフォールドを用意し、`pip` 壊れた状態でも依存解決とテスト実行ができる土台を作る。Epic 01 以降の `uv add` / `pytest` が動く前提を満たす。

## ユーザーストーリー

**As a** claude-voice を開発する開発者
**I want to** `.venv` と pytest が動く状態を用意したい
**So that** Epic 01 以降の依存追加・テストが破綻なく回る

## 受入条件

- [ ] `.venv\Scripts\python.exe --version` が `Python 3.10.*` または `3.11.*` を返す
- [ ] `.venv\Scripts\pytest.exe --version` がエラーなく成功する
- [ ] `pyproject.toml` が存在し `requires-python` が固定されている（dev 依存に pytest を含む）
- [ ] `tests/__init__.py` と最低 1 個のプレースホルダテスト（例: `tests/test_smoke.py` の `def test_smoke(): assert True`）が存在し、`.venv\Scripts\pytest.exe` が 1 件 pass する
- [ ] `uv lock` 由来の lockfile（`uv.lock`）が生成されている

## 仕様詳細

### UI / 画面

なし

### API / Server Action

なし（環境セットアップ）

### データモデル

なし

### バリデーション

- Python バージョンが 3.10 / 3.11 のどちらかであること（実装が使う型ヒント記法に整合）

### エラーハンドリング

- 既存の壊れた `pip` には依存しない（uv 経由のみ）

### エッジケース

- 既存の `.venv` がある場合は再作成するか保持するか方針を決めて従う（既定: 既存があれば中身を確認のみで再作成しない）

## 依存関係

- 前提（着手前に完了が必要）: なし
- ブロックする: `00-environment-setup/02-external-services`, `00-environment-setup/03-setup-documentation`, および全実装 Epic（01〜04）

理由: 仮想環境がないと依存追加・テスト実行・実装着手ができない。

## スコープ外

- 実装系の依存追加（mcp / faster-whisper / vosk / requests）— Epic 01 で行う
- lint / formatter の導入（ruff 等）

## 補足

- 推奨: `uv venv --python 3.11` で venv を作成し、`uv add --dev pytest` を加える
- 関連設計: なし（環境構築は設計判断対象外）
