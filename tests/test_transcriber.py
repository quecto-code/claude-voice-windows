from unittest import mock

import numpy as np

from claude_voice import config
from claude_voice.listen import transcriber


def _reset_singleton():
    transcriber._model = None
    transcriber._model_load_failed = False


def _seg(text):
    s = mock.Mock()
    s.text = text
    return s


def test_signature_empty_pcm_returns_none():
    _reset_singleton()
    assert transcriber.transcribe(b"") is None


def test_short_pcm_returns_none_without_model():
    _reset_singleton()
    with mock.patch.object(transcriber, "WhisperModel") as wm:
        assert transcriber.transcribe(b"\x00" * 3000) is None
        assert wm.call_count == 0


def test_pcm_to_float32_scales_and_drops_odd_byte():
    arr = transcriber._pcm_to_float32(b"\x00\x80\xff\x7f\x00")  # -32768, 32767, 余り1byte
    assert arr.dtype == np.float32
    assert len(arr) == 2
    assert arr[0] == -1.0
    assert abs(arr[1] - (32767 / 32768.0)) < 1e-6


def test_happy_path_concatenates_segments():
    _reset_singleton()
    model = mock.Mock()
    model.transcribe.return_value = ([_seg("こんにちは"), _seg("、"), _seg("世界。")], None)
    with mock.patch.object(transcriber, "WhisperModel", return_value=model) as wm:
        out = transcriber.transcribe(b"\x01\x02" * 2000)  # 4000 bytes > 3200
    assert out == "こんにちは、世界。"
    assert wm.call_args.args[0] == config.WHISPER_MODEL_SIZE
    assert wm.call_args.kwargs["device"] == "cuda"
    assert model.transcribe.call_args.kwargs["language"] == "ja"
    audio = model.transcribe.call_args.args[0]
    assert isinstance(audio, np.ndarray) and audio.dtype == np.float32


def test_model_singleton_loaded_once():
    _reset_singleton()
    model = mock.Mock()
    model.transcribe.return_value = ([_seg("a")], None)
    with mock.patch.object(transcriber, "WhisperModel", return_value=model) as wm:
        for _ in range(3):
            transcriber.transcribe(b"\x01\x02" * 2000)
    assert wm.call_count == 1


def test_blank_result_returns_none():
    _reset_singleton()
    model = mock.Mock()
    model.transcribe.return_value = ([_seg("   ")], None)
    with mock.patch.object(transcriber, "WhisperModel", return_value=model):
        assert transcriber.transcribe(b"\x01\x02" * 2000) is None


def test_model_load_failure_returns_none_and_not_retried():
    _reset_singleton()
    with mock.patch.object(transcriber, "WhisperModel", side_effect=RuntimeError("no cuda")) as wm:
        assert transcriber.transcribe(b"\x01\x02" * 2000) is None
        assert transcriber.transcribe(b"\x01\x02" * 2000) is None
        assert wm.call_count == 1  # 失敗を記憶して再試行しない


def test_transcribe_inference_failure_returns_none():
    _reset_singleton()
    model = mock.Mock()
    model.transcribe.side_effect = RuntimeError("boom")
    with mock.patch.object(transcriber, "WhisperModel", return_value=model):
        assert transcriber.transcribe(b"\x01\x02" * 2000) is None
