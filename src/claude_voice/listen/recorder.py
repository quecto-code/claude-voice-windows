"""sox 子プロセスで録音し、vosk で確定ワードを検出する recorder。

design.md「主要フロー: listen」の recorder 部分。単一の読取スレッドが sox の
stdout を読みながら (a) 全 PCM バッファに蓄積し、(b) vosk Recognizer に逐次供給
する。確定の引き金は 3 つ:

- 無音（sox の silence エフェクトが自然停止）       → FinalizeReason.silence
- 確定ワード（vosk の partial に検出 → SIGTERM）    → FinalizeReason.word
- 発話開始が onset timeout 以内に観測されない        → FinalizeReason.timeout

例外は一切上位に投げず、失敗は (b"", FinalizeReason.timeout) にマップする
（Reliability NFR）。
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time

import vosk

from .. import config
from ..types import FinalizeReason

# 読取チャンクサイズ（bytes）。
_CHUNK_BYTES = 4096

# onset 判定のしきい値（int16 LE PCM の絶対値平均）。暫定値・将来 config 化可。
_ONSET_AMPLITUDE_THRESHOLD = 500

# vosk モデルのシングルトン（プロセス内で 1 度だけロードする）。
_vosk_model: "vosk.Model | None" = None
_vosk_model_lock = threading.Lock()


def _build_sox_command(silence_sec: float) -> list[str]:
    """録音用 sox コマンドを組み立てる。

    16kHz / mono / s16le の raw PCM を stdout に流し、無音 ``silence_sec`` 秒で
    自然終了する。
    """
    return [
        "sox",
        "-t", "pulseaudio", "default",
        "-r", "16000",
        "-c", "1",
        "-t", "raw",
        "-e", "signed",
        "-b", "16",
        "-",
        "silence", "1", "0.05", "1%", "1", str(silence_sec), "1%",
    ]


def _chunk_amplitude(chunk: bytes) -> float:
    """int16 LE PCM チャンクの絶対値平均を返す（onset 判定用）。"""
    n = len(chunk) // 2
    if n == 0:
        return 0.0
    total = 0
    for i in range(0, n * 2, 2):
        sample = int.from_bytes(chunk[i:i + 2], "little", signed=True)
        total += sample if sample >= 0 else -sample
    return total / n


def _get_vosk_model() -> "vosk.Model":
    """vosk Model をシングルトンでロードする。"""
    global _vosk_model
    with _vosk_model_lock:
        if _vosk_model is None:
            _vosk_model = vosk.Model(config.VOSK_MODEL_PATH)
    return _vosk_model


def _partial_text(recognizer: "vosk.KaldiRecognizer") -> str:
    """vosk の partial result からテキストを取り出す。

    JSON デコード失敗（vosk のバージョン差で出力形式が違う等）は空文字に倒す。
    """
    try:
        data = json.loads(recognizer.PartialResult())
    except (ValueError, TypeError):
        return ""
    if isinstance(data, dict):
        return str(data.get("partial", ""))
    return ""


def record(
    finalize_word: str,
    silence_sec: float,
    onset_timeout_sec: float,
) -> tuple[bytes, FinalizeReason]:
    """sox + vosk を回し、確定 PCM と理由を返す。

    例外は投げない。失敗時は ``(b"", FinalizeReason.timeout)`` を返す。
    """
    # vosk モデルのロード失敗は録音を始めずに timeout で返す。
    try:
        model = _get_vosk_model()
        recognizer = vosk.KaldiRecognizer(model, 16000)
    except Exception as exc:  # noqa: BLE001 - 境界では全例外を握る
        print(f"vosk model load error: {exc}", file=sys.stderr)
        return b"", FinalizeReason.timeout

    try:
        proc = subprocess.Popen(
            _build_sox_command(silence_sec),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"sox launch error: {exc}", file=sys.stderr)
        return b"", FinalizeReason.timeout

    buffer = bytearray()
    onset_seen = threading.Event()
    word_detected = threading.Event()

    def reader() -> None:
        try:
            assert proc.stdout is not None
            while True:
                chunk = proc.stdout.read(_CHUNK_BYTES)
                if not chunk:
                    break
                buffer.extend(chunk)
                if not onset_seen.is_set() and _chunk_amplitude(chunk) > _ONSET_AMPLITUDE_THRESHOLD:
                    onset_seen.set()
                # vosk 供給と確定ワード検出。
                try:
                    recognizer.AcceptWaveform(bytes(chunk))
                    if not word_detected.is_set() and finalize_word in _partial_text(recognizer):
                        word_detected.set()
                        proc.terminate()  # SIGTERM
                except Exception as exc:  # noqa: BLE001 - reader 内例外で録音を壊さない
                    print(f"vosk accept error: {exc}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001
            print(f"recorder reader error: {exc}", file=sys.stderr)

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()

    start = time.monotonic()
    reason = FinalizeReason.silence
    try:
        while True:
            if proc.poll() is not None:
                # sox が終了した。word なら SIGTERM 起因、そうでなければ無音停止。
                reason = FinalizeReason.word if word_detected.is_set() else FinalizeReason.silence
                break
            if not onset_seen.is_set() and (time.monotonic() - start) > onset_timeout_sec:
                # 発話開始が観測されないまま onset timeout を超過 → 打ち切り。
                proc.terminate()
                try:
                    proc.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    proc.kill()
                reason = FinalizeReason.timeout
                break
            time.sleep(0.05)
    except Exception as exc:  # noqa: BLE001
        print(f"recorder loop error: {exc}", file=sys.stderr)

    thread.join(timeout=2.0)

    if reason == FinalizeReason.timeout:
        return b"", FinalizeReason.timeout
    return bytes(buffer), reason
