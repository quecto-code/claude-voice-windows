"""MCP サーバ。FastMCP に 2 つの純粋関数ツールを登録する薄いラッパ。

公開ツール:
- ``voice_listen()``     — マイクから 1 発話を録音・文字起こしして返す（FR-2）
- ``voice_speak(text)``  — テキストを VOICEVOX で合成して再生する（FR-3/4, A-2）
- ``voice_ping()``       — 疎通確認用

ロジックは listen / speak サブパッケージに住み、ここには書かない（design.md
「server.py は薄いラッパに留める」）。
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .listen import listen as _listen
from .speak import speak as _speak
from .types import ListenResult, SpeakResult

mcp = FastMCP("claude-voice")


@mcp.tool()
def voice_ping() -> str:
    """疎通確認用。常に "pong" を返す。"""
    return "pong"


@mcp.tool()
def voice_listen() -> ListenResult:
    """マイクから 1 発話を録音・文字起こしして返す（listen.listen の薄いラッパ）。"""
    return _listen()


@mcp.tool()
def voice_speak(text: str) -> SpeakResult:
    """テキストを音声で読み上げる（speak.speak の薄いラッパ）。"""
    return _speak(text)


def run() -> None:
    """stdio で MCP サーバを起動する。"""
    mcp.run()
