"""しきい値・モデル名・URL 等の設定値を一箇所に集約する（葉モジュール）。

各定数は ``CLAUDE_VOICE_*`` 環境変数で上書きできる。数値のパースに失敗した場合は
起動時に ``RuntimeError`` で明示的に落とす（design.md の config 責務 / 運用方針）。

マジックナンバーを各モジュールに散らさず、必ずここを参照する。
"""

from __future__ import annotations

import os


def _get_str(env_key: str, default: str) -> str:
    value = os.environ.get(env_key)
    return value if value is not None and value != "" else default


def _get_float(env_key: str, default: float) -> float:
    raw = os.environ.get(env_key)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise RuntimeError(
            f"環境変数 {env_key} を float として解釈できません: {raw!r}"
        ) from exc


def _get_int(env_key: str, default: int) -> int:
    raw = os.environ.get(env_key)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(
            f"環境変数 {env_key} を int として解釈できません: {raw!r}"
        ) from exc


# --- listen（録音・確定） -------------------------------------------------

#: 無音による確定までの秒数（sox silence エフェクトに渡す）。
SILENCE_SEC: float = _get_float("CLAUDE_VOICE_SILENCE_SEC", 1.2)

#: 発話開始（onset）がこの秒数以内に観測されなければ timeout として打ち切る。
ONSET_TIMEOUT_SEC: float = _get_float("CLAUDE_VOICE_ONSET_TIMEOUT_SEC", 30.0)

#: 発話を即座に確定させる確定ワード（vosk のスポッティング対象）。
FINALIZE_WORD: str = _get_str("CLAUDE_VOICE_FINALIZE_WORD", "以上")

#: vosk 日本語モデルの配置先（README の DL 手順で配置する）。
VOSK_MODEL_PATH: str = _get_str(
    "CLAUDE_VOICE_VOSK_MODEL_PATH", "models/vosk-model-ja-0.22"
)

#: faster-whisper のモデルサイズ。
WHISPER_MODEL_SIZE: str = _get_str("CLAUDE_VOICE_WHISPER_MODEL_SIZE", "small")


# --- speak（合成・再生） --------------------------------------------------

#: VOICEVOX エンジンの URL。
VOICEVOX_URL: str = _get_str("CLAUDE_VOICE_VOICEVOX_URL", "http://127.0.0.1:50021")

#: VOICEVOX の話者 id。
SPEAKER_ID: int = _get_int("CLAUDE_VOICE_SPEAKER_ID", 1)

#: 再生時の出力サンプルレート。Windows 音声エンジンの underrun 耐性の保険として
#: sox 側で高品質リサンプリングして渡す（Audio Quality NFR。ADR-0005）。
PLAYBACK_SAMPLE_RATE: int = _get_int("CLAUDE_VOICE_PLAYBACK_SAMPLE_RATE", 48000)

#: sox 再生時のバッファサイズ（バイト）。underrun 由来のプツプツを抑える保険。
SOX_BUFFER_BYTES: int = _get_int("CLAUDE_VOICE_SOX_BUFFER_BYTES", 32768)

#: 再生末尾に付ける無音パディング（秒）。sox の waveaudio 出力はデバイスを閉じる
#: 際に最後の 1 バッファ分をドレインせず捨てることがあり、末尾の音声が切れる。
#: 取りこぼされるのが無音になるよう、バッファ長以上のパディングを付ける（ADR-0005）。
PLAYBACK_TAIL_PAD_SEC: float = _get_float("CLAUDE_VOICE_PLAYBACK_TAIL_PAD_SEC", 0.8)
