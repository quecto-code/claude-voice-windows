"""パイプラインの境界を流れる値オブジェクト（葉モジュール）。

design.md「データモデル」の値オブジェクトに対応する。エンティティ（同一性を
持つ概念）は存在せず、ここにあるのは中間値のみ。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class FinalizeReason(Enum):
    """録音停止の理由。"""

    silence = "silence"  # sox の silence エフェクトが自然停止（無音検出）
    word = "word"        # vosk が確定ワードを検出し SIGTERM で停止
    timeout = "timeout"  # 発話開始が onset timeout 以内に観測されず kill


@dataclass(frozen=True)
class ListenResult:
    """``voice_listen()`` の戻り値。

    不変条件:
    - ``status == "ok"``  ⇒ ``transcript`` は非空
    - ``status != "ok"``  ⇒ ``transcript == ""``
    """

    transcript: str
    status: Literal["ok", "silent", "unintelligible"]


@dataclass(frozen=True)
class SpeakResult:
    """``voice_speak(text)`` の戻り値。

    不変条件:
    - ``ok is True``  ⇒ ``error is None``
    - ``ok is False`` ⇒ ``error`` は非空文字列
    """

    ok: bool
    error: str | None
