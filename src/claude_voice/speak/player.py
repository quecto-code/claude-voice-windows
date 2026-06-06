"""sox による WAV の同期再生（Windows ネイティブ / waveaudio）。

design.md「player.py の sox 再生」: VOICEVOX の 24kHz WAV を Windows の音声エンジン
（`-t waveaudio default`）にそのまま渡す。WSLg PulseAudio 由来の歪みは Windows
ネイティブでは発生しない（ADR-0005）が、underrun 耐性の保険として ``--buffer`` で
バッファを拡大し、末尾の ``rate -v`` で高品質リサンプリングして
``PLAYBACK_SAMPLE_RATE`` に整える（Audio Quality NFR、既定で無害）。

例外は一切上位に投げず、成功 True / 失敗 False を返す。
"""

from __future__ import annotations

import subprocess
import sys

from .. import config


def _build_sox_command() -> list[str]:
    return [
        "sox",
        "--buffer", str(config.SOX_BUFFER_BYTES),
        "-t", "wav", "-",
        "-t", "waveaudio", "default",
        "rate", "-v", str(config.PLAYBACK_SAMPLE_RATE),
    ]


def play(wav: bytes) -> bool:
    """WAV bytes を sox で同期再生する。成功 True / 失敗 False。例外は投げない。"""
    try:
        result = subprocess.run(
            _build_sox_command(),
            input=wav,
            check=False,
            capture_output=True,
        )
    except Exception as exc:  # noqa: BLE001 - sox 未配置 (FileNotFoundError) 等を含め全て False
        print(f"sox playback error: {exc}", file=sys.stderr)
        return False

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", "replace") if result.stderr else ""
        print(f"sox playback failed: rc={result.returncode} {stderr}", file=sys.stderr)
        return False
    return True
