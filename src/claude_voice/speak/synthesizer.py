"""VOICEVOX HTTP クライアント。テキストから WAV bytes を生成する。

design.md「外部 API（VOICEVOX）」:
    POST {VOICEVOX_URL}/audio_query?text=...&speaker={id} → audio_query JSON
    POST {VOICEVOX_URL}/synthesis?speaker={id}  body: audio_query JSON → WAV bytes

HTTP API は Windows 版 VOICEVOX でも同一（ADR-0005）。例外は一切上位に投げず、
失敗時は ``None`` を返し stderr に理由をログ出力する。
"""

from __future__ import annotations

import sys

import requests

from .. import config

# 接続 3.0s / 読取 10.0s（合理的デフォルト）。
_TIMEOUT = (3.0, 10.0)


def synthesize(text: str, speaker: int) -> bytes | None:
    """VOICEVOX エンジンに合成リクエストし WAV bytes を返す。失敗時 None。"""
    if not text:
        return None

    base = config.VOICEVOX_URL.rstrip("/")
    try:
        query_resp = requests.post(
            f"{base}/audio_query",
            params={"text": text, "speaker": speaker},
            timeout=_TIMEOUT,
        )
        if query_resp.status_code != 200:
            print(
                f"voicevox audio_query failed: status={query_resp.status_code}",
                file=sys.stderr,
            )
            return None
        audio_query = query_resp.json()

        synth_resp = requests.post(
            f"{base}/synthesis",
            params={"speaker": speaker},
            json=audio_query,
            timeout=_TIMEOUT,
        )
        if synth_resp.status_code != 200:
            print(
                f"voicevox synthesis failed: status={synth_resp.status_code}",
                file=sys.stderr,
            )
            return None
        wav = synth_resp.content
        if not wav:
            print("voicevox synthesis failed: empty body", file=sys.stderr)
            return None
        return wav
    except Exception as exc:  # noqa: BLE001 - 接続失敗・JSON デコード失敗など全て None に倒す
        print(f"voicevox synthesize error: {exc}", file=sys.stderr)
        return None
