---
type: task
title: Claude Code に claude-voice を登録する
label: must-have
depends_on:
  - 01-mcp-server-foundation/01-server-skeleton/01-scaffold-package-and-mcp-server
---

## 背景

親 Story `01-mcp-server-foundation/01-server-skeleton` の一部として、雛形サーバを Claude Code の MCP 設定に登録し、`voice_ping` の疎通までを通す。

親 Story: 01-mcp-server-foundation/01-server-skeleton

## 受入条件

- [ ] MCP 設定（`.mcp.json` もしくは `claude mcp add` 相当）に claude-voice サーバの起動コマンドが定義されている（`python -m claude_voice`、絶対パスまたは venv 経路で解決可能）→ `.mcp.json` に `command=C:\\Users\\yuno\\dev\\claude-voice\\.venv\\Scripts\\python.exe`、`args=["-m","claude_voice"]`（Windows ネイティブ、[ADR-0005](../../../../adr/0005-windows-native-audio-path.md)）
- [ ] Claude Code 起動後、ツール一覧に `voice_ping` が表示される → **手動検証**: 次回 Claude Code 起動時に確認
- [ ] Claude から `voice_ping` を呼ぶと `"pong"` が返る → **手動検証**: 同上、再起動後に呼び出して確認

## 仕様詳細

### 変更ファイル

- `.mcp.json`（新規・プロジェクト直下）— claude-voice サーバの起動設定
- `docs/tasks/.../task.md`（受入条件チェック）
- `docs/tasks/STATUS.md`（6/17）

`.mcp.json` の内容（venv の python を絶対パスで指定。Windows なので `.venv\Scripts\python.exe`。JSON ではバックスラッシュをエスケープ）:
```json
{
  "mcpServers": {
    "claude-voice": {
      "command": "C:\\Users\\yuno\\dev\\claude-voice\\.venv\\Scripts\\python.exe",
      "args": ["-m", "claude_voice"]
    }
  }
}
```

### 関数 / API シグネチャ

該当なし（設定作業）

### バリデーション・エラー処理

- 登録後にサーバが起動しない場合、Claude Code の MCP ログでエラーを確認できる
- venv / Python 実行パスが Claude Code から解決可能か確認する

### エッジケース

- Windows のパス（`.venv\Scripts\python.exe`）を Claude Code 側から絶対パスで指す（[ADR-0005](../../../../adr/0005-windows-native-audio-path.md)）

## 依存関係

- 前提: 01-mcp-server-foundation/01-server-skeleton/01-scaffold-package-and-mcp-server
- ブロックする: なし

理由: 起動できる雛形が先に必要。

## スコープ外

- 音声系ツール（`voice_listen` / `voice_speak`）の登録は各 Epic で行う

## 補足

- [ADR-0001](../../../../adr/0001-mcp-tool-driven-turn-based.md)
- 関連設計: [design.md#構成](../../../../design/design.md#構成)（ツリー）
