"""listen パイプライン。recorder と transcriber を順に呼ぶオーケストレータ。

公開するのは ``listen() -> ListenResult`` のみ。recorder / transcriber は実装詳細。

フロー（design.md「主要フロー: listen」）:
    record → (timeout なら silent で短絡) → transcribe
           → (None/空/空白なら unintelligible)
           → 確定ワード除去 → (除去後に空なら unintelligible)
           → ListenResult(text, "ok")
"""

from __future__ import annotations

import sys

from .. import config
from ..types import FinalizeReason, ListenResult
from . import recorder, transcriber

# 末尾から剥がす空白・句読点（確定ワード除去の前処理）。
_TRAILING_CHARS = "。、！？.,!?\n\r\t 　"


def _strip_finalize_word(text: str, word: str) -> str:
    """末尾の確定ワードを 1 回だけ除去する。

    末尾の空白・句読点を一旦剥がしてから ``endswith(word)`` で判定する。
    """
    stripped = text.rstrip(_TRAILING_CHARS)
    if word and stripped.endswith(word):
        stripped = stripped[: -len(word)]
    return stripped.rstrip(_TRAILING_CHARS)


def listen() -> ListenResult:
    """マイクから 1 発話を録音・文字起こしして返す。例外は status で表現する。"""
    try:
        pcm, reason = recorder.record(
            finalize_word=config.FINALIZE_WORD,
            silence_sec=config.SILENCE_SEC,
            onset_timeout_sec=config.ONSET_TIMEOUT_SEC,
        )
    except Exception as exc:  # noqa: BLE001 - 境界では例外を投げない
        print(f"listen recorder error: {exc}", file=sys.stderr)
        return ListenResult("", "unintelligible")

    if reason == FinalizeReason.timeout:
        return ListenResult("", "silent")

    try:
        text = transcriber.transcribe(pcm)
    except Exception as exc:  # noqa: BLE001
        print(f"listen transcriber error: {exc}", file=sys.stderr)
        return ListenResult("", "unintelligible")

    if not text or not text.strip():
        return ListenResult("", "unintelligible")

    text = _strip_finalize_word(text, config.FINALIZE_WORD)
    if not text:
        return ListenResult("", "unintelligible")

    return ListenResult(text, "ok")
