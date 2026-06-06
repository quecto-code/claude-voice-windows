import importlib

import pytest


def _reload(monkeypatch, **env):
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    import claude_voice.config as config
    return importlib.reload(config)


def test_defaults(monkeypatch):
    for key in [
        "CLAUDE_VOICE_SILENCE_SEC", "CLAUDE_VOICE_ONSET_TIMEOUT_SEC",
        "CLAUDE_VOICE_FINALIZE_WORD", "CLAUDE_VOICE_VOSK_MODEL_PATH",
        "CLAUDE_VOICE_WHISPER_MODEL_SIZE", "CLAUDE_VOICE_VOICEVOX_URL",
        "CLAUDE_VOICE_SPEAKER_ID", "CLAUDE_VOICE_PLAYBACK_SAMPLE_RATE",
        "CLAUDE_VOICE_SOX_BUFFER_BYTES",
    ]:
        monkeypatch.delenv(key, raising=False)
    config = _reload(monkeypatch)
    assert config.SILENCE_SEC == 1.2
    assert config.ONSET_TIMEOUT_SEC == 30.0
    assert config.FINALIZE_WORD == "以上"
    assert config.VOSK_MODEL_PATH == "models/vosk-model-ja-0.22"
    assert config.WHISPER_MODEL_SIZE == "small"
    assert config.VOICEVOX_URL == "http://127.0.0.1:50021"
    assert config.SPEAKER_ID == 1
    assert config.PLAYBACK_SAMPLE_RATE == 48000
    assert config.SOX_BUFFER_BYTES == 32768


def test_env_override(monkeypatch):
    config = _reload(
        monkeypatch,
        CLAUDE_VOICE_SILENCE_SEC="0.8",
        CLAUDE_VOICE_FINALIZE_WORD="おわり",
        CLAUDE_VOICE_SPEAKER_ID="3",
        CLAUDE_VOICE_PLAYBACK_SAMPLE_RATE="44100",
    )
    assert config.SILENCE_SEC == 0.8
    assert config.FINALIZE_WORD == "おわり"
    assert config.SPEAKER_ID == 3
    assert config.PLAYBACK_SAMPLE_RATE == 44100


def test_float_parse_failure(monkeypatch):
    with pytest.raises(RuntimeError):
        _reload(monkeypatch, CLAUDE_VOICE_SILENCE_SEC="not-a-number")
    _reload(monkeypatch, CLAUDE_VOICE_SILENCE_SEC=None)  # 復旧


def test_int_parse_failure(monkeypatch):
    with pytest.raises(RuntimeError):
        _reload(monkeypatch, CLAUDE_VOICE_SPEAKER_ID="x")
    _reload(monkeypatch, CLAUDE_VOICE_SPEAKER_ID=None)  # 復旧
