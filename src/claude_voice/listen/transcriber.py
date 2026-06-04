"""faster-whisper による確定 PCM の文字起こし。

design.md「インターフェース」「unintelligible 失敗パス」に対応。16kHz/mono/s16le
の生 PCM を float32 numpy 配列へ変換し、faster-whisper（small / CUDA）に渡す。
モデルはシングルトン化し、ロード失敗は記憶して再試行しない。

例外は一切上位に投げず、失敗・空・極短入力では ``None`` を返す。
"""

from __future__ import annotations

import sys
import threading

import numpy as np

try:  # faster-whisper 本体のインポート失敗も None 経路で吸収する。
    from faster_whisper import WhisperModel
except Exception:  # noqa: BLE001
    WhisperModel = None  # type: ignore[assignment, misc]

from .. import config

# 16kHz / mono / s16le × 0.1 秒。これ未満は推論せず None。
_MIN_PCM_BYTES = 3200

_model: "WhisperModel | None" = None
_model_lock = threading.Lock()
_model_load_failed = False


def _get_model() -> "WhisperModel | None":
    """faster-whisper モデルをシングルトンでロードする。失敗は記憶する。"""
    global _model, _model_load_failed
    with _model_lock:
        if _model is not None:
            return _model
        if _model_load_failed:
            return None
        if WhisperModel is None:
            _model_load_failed = True
            print("faster-whisper import failed", file=sys.stderr)
            return None
        try:
            _model = WhisperModel(
                config.WHISPER_MODEL_SIZE, device="cuda", compute_type="float16"
            )
        except Exception as exc:  # noqa: BLE001
            _model_load_failed = True
            print(f"whisper model load error: {exc}", file=sys.stderr)
            return None
        return _model


def _pcm_to_float32(pcm: bytes) -> np.ndarray:
    """int16 LE の生 PCM を float32 [-1, 1] の numpy 配列へ変換する。

    奇数長は末尾 1 バイトを捨てて読む。
    """
    if len(pcm) % 2:
        pcm = pcm[:-1]
    samples = np.frombuffer(pcm, dtype="<i2").astype(np.float32)
    return samples / 32768.0


def transcribe(pcm: bytes) -> str | None:
    """生 PCM を faster-whisper で文字起こしする。失敗・空・極短入力で None。"""
    if not pcm or len(pcm) < _MIN_PCM_BYTES:
        return None

    model = _get_model()
    if model is None:
        return None

    try:
        audio = _pcm_to_float32(pcm)
        segments, _info = model.transcribe(audio, language="ja")
        text = "".join(segment.text for segment in segments).strip()
    except Exception as exc:  # noqa: BLE001
        print(f"whisper transcribe error: {exc}", file=sys.stderr)
        return None

    return text or None
