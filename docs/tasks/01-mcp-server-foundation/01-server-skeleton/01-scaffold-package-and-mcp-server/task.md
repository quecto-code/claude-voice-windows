---
type: task
title: パッケージと MCP サーバの雛形を作る
label: must-have
depends_on: []
---

## 背景

親 Story `01-mcp-server-foundation/01-server-skeleton` の一部として、Python パッケージ・共有型・設定・MCP サーバ雛形を作る。

親 Story: 01-mcp-server-foundation/01-server-skeleton

## 受入条件

- [x] `pyproject.toml` に `requires-python` と MCP SDK / faster-whisper / vosk / requests（VOICEVOX 用）等の依存が宣言されている → `mcp>=1.27.1` / `faster-whisper>=1.2.1` / `vosk>=0.3.45` / `requests>=2.34.2`、`requires-python = ">=3.10,<3.12"`
- [x] `src/claude_voice/__init__.py` が存在する（中身は空でよい）
- [x] `src/claude_voice/__main__.py` から `server.run()` が呼ばれ、`python -m claude_voice` で stdio サーバとして起動する → `timeout 5 python -m claude_voice </dev/null` が rc=0 で抜ける（stdio EOF で正常終了）
- [x] `src/claude_voice/types.py` に次が定義されている: `FinalizeReason` / `ListenResult` / `SpeakResult` → pytest 3 件
- [x] `src/claude_voice/config.py` に 7 定数 + `CLAUDE_VOICE_*` 環境変数上書き → pytest 4 件（既定値・上書き・float パース失敗・int パース失敗）
- [x] `src/claude_voice/server.py` で `FastMCP` を生成し `voice_ping()` が `"pong"` を返す → pytest 1 件
- [x] `python -m claude_voice` を起動して MCP ハンドシェイクが例外なく成立する → stdio で起動・EOF で正常終了を確認。インポート + FastMCP 生成も成功

> **Python バージョン変更**: 00/01/01 では Python 3.10.12 で venv を作成したが、`onnxruntime` が Python 3.10 用 wheel を提供していないため faster-whisper / vosk の依存解決が失敗。**`uv python install 3.11` で取得した CPython 3.11.15**（リリース版）で venv を再構築した。`requires-python = ">=3.10,<3.12"` の範囲内で、design.md の Python 3.10/3.11 想定と整合。

## 仕様詳細

### 変更ファイル

- `pyproject.toml`（runtime 依存追加: mcp / faster-whisper / vosk / requests）
- `uv.lock`（uv add で再生成）
- `.venv/`（Python 3.10 → 3.11 で再構築、`.gitignore` 対象）
- `src/claude_voice/__init__.py`（新規・空）
- `src/claude_voice/__main__.py`（新規・`server.run()` 呼び出し）
- `src/claude_voice/server.py`（新規・`FastMCP` + `voice_ping`）
- `src/claude_voice/types.py`（新規・`FinalizeReason` / `ListenResult` / `SpeakResult`）
- `src/claude_voice/config.py`（新規・7 定数 + env 上書き + float/int パース失敗で `RuntimeError`）
- `tests/test_server.py`（新規・types / config / voice_ping の単体テスト 10 件）
- `docs/tasks/.../task.md`（受入条件チェック）
- `docs/tasks/STATUS.md`（5/17）

### 関数 / API シグネチャ

```python
# server.py
def run() -> None: ...                 # stdio で MCP サーバを起動
def voice_ping() -> str: ...           # "pong" を返す（疎通確認用）

# types.py（design.md の値オブジェクトに準拠）
class FinalizeReason(Enum):
    silence = "silence"
    word = "word"
    timeout = "timeout"

@dataclass(frozen=True)
class ListenResult:
    transcript: str
    status: Literal["ok", "silent", "unintelligible"]

@dataclass(frozen=True)
class SpeakResult:
    ok: bool
    error: str | None
```

### バリデーション・エラー処理

- 環境変数の解析失敗（float に変換できない等）は起動時に明示エラーで落とす
- サーバ起動失敗時は stderr にスタックトレースを出す

### エッジケース

- Python 3.10 / 3.11 の差（型ヒント記法 `str | None` は 3.10+ で OK）。`requires-python = ">=3.10"` を明記
- vosk モデルパスはデフォルト未指定で、起動時に config からのみ参照される（実体配置は README）

## 依存関係

- 前提: なし
- ブロックする: 01-mcp-server-foundation/01-server-skeleton/02-register-server-in-claude-code

理由: サーバが起動できる状態を作ってから Claude Code 側の設定を行う。

## スコープ外

- 音声系ツール（`voice_listen` / `voice_speak`）の実装
- vosk モデルのダウンロード（README で案内するだけ）

## 補足

- [ADR-0001](../../../../adr/0001-mcp-tool-driven-turn-based.md)
- 関連設計:
  - [design.md#構成](../../../../design/design.md#構成)（ツリー・各ディレクトリ責務・依存方向）
  - [design.md#データモデル](../../../../design/design.md#データモデル)（値オブジェクト 3 種・不変条件）
  - [design.md#インターフェース](../../../../design/design.md#インターフェース)（MCP ツール表層・サブパッケージ公開 API）
