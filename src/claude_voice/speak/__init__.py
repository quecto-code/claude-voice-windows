"""speak パイプライン。synthesizer と player を順に呼ぶオーケストレータ。

公開するのは ``speak(text) -> SpeakResult`` のみ。synthesizer / player は実装詳細。

連続呼び出しでの再生重なりを防ぐため、合成 + 再生をモジュールレベルの
``threading.Lock`` で直列化する（design.md「単一スピーカー」の下支え）。
"""

from __future__ import annotations

import threading

from .. import config
from ..types import SpeakResult
from . import player, synthesizer

# 合成 + 再生を直列化するロック（再生重なり防止）。
_lock = threading.Lock()


def speak(text: str) -> SpeakResult:
    """テキストを VOICEVOX で合成し、sox で再生する。

    4 分岐（空文字 / 合成失敗 / 再生失敗 / 成功）で SpeakResult を返す。
    """
    if not text:
        return SpeakResult(ok=True, error=None)

    with _lock:
        wav = synthesizer.synthesize(text, speaker=config.SPEAKER_ID)
        if wav is None:
            return SpeakResult(ok=False, error="voicevox synthesis failed")
        ok = player.play(wav)

    return SpeakResult(ok=ok, error=None if ok else "playback failed")
