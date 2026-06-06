import json
import threading
from unittest import mock

from claude_voice.listen import recorder
from claude_voice.types import FinalizeReason


class _FakeProc:
    """sox 子プロセスの代役。chunks を順に吐き、尽きたら（または terminate 後）終了する。"""

    def __init__(self, chunks, block_forever=False):
        self._chunks = list(chunks)
        self._block_forever = block_forever
        self._terminated = False
        self.terminate_called = False
        self.stdout = self
        self._lock = threading.Lock()

    def read(self, _n):
        with self._lock:
            if self._chunks:
                return self._chunks.pop(0)
        if self._block_forever and not self._terminated:
            import time
            time.sleep(0.01)
            return b"\x00" * 32  # 無音を吐き続ける
        return b""

    def terminate(self):
        self.terminate_called = True
        self._terminated = True
        with self._lock:
            self._chunks = []

    def kill(self):
        self.terminate()

    def poll(self):
        with self._lock:
            empty = not self._chunks
        if self._terminated:
            return -15
        if empty and not self._block_forever:
            return 0
        return None

    def wait(self, timeout=None):
        return 0


class _FakeRecognizer:
    def __init__(self, *_a, **_k):
        self.accept_calls = 0
        self._partial = ""

    def AcceptWaveform(self, _data):
        self.accept_calls += 1
        return False

    def PartialResult(self):
        return json.dumps({"partial": self._partial})

    def set_partial(self, text):
        self._partial = text


def test_signature():
    import inspect
    sig = inspect.signature(recorder.record)
    assert list(sig.parameters) == ["finalize_word", "silence_sec", "onset_timeout_sec"]


def test_build_sox_command_uses_waveaudio():
    cmd = recorder._build_sox_command(1.2)
    # Windows ネイティブ: 入力は waveaudio 既定デバイス（ADR-0005）
    assert cmd[:4] == ["sox", "-t", "waveaudio", "default"]
    assert "pulseaudio" not in cmd
    assert "raw" in cmd and "signed" in cmd
    assert cmd[cmd.index("-b") + 1] == "16"
    assert "silence" in cmd
    assert "1.2" in cmd


def test_chunk_amplitude():
    loud = (b"\xff\x7f") * 10  # 32767
    assert recorder._chunk_amplitude(loud) > 500
    assert recorder._chunk_amplitude(b"\x00\x00" * 10) == 0.0


def test_silence_accumulates_and_supplies_vosk():
    rec = _FakeRecognizer()
    loud = (b"\xff\x7f") * 2048
    proc = _FakeProc([loud, loud])
    recorder._vosk_model = None
    with mock.patch.object(recorder.vosk, "Model", return_value=mock.Mock()), \
         mock.patch.object(recorder.vosk, "KaldiRecognizer", return_value=rec), \
         mock.patch.object(recorder.subprocess, "Popen", return_value=proc):
        pcm, reason = recorder.record("以上", 1.2, 30.0)
    assert pcm == loud + loud
    assert reason == FinalizeReason.silence
    assert rec.accept_calls == 2


def test_finalize_word_triggers_terminate_and_word_reason():
    rec = _FakeRecognizer()
    rec.set_partial("ビルドして以上")
    loud = (b"\xff\x7f") * 2048
    proc = _FakeProc([loud])
    recorder._vosk_model = None
    with mock.patch.object(recorder.vosk, "Model", return_value=mock.Mock()), \
         mock.patch.object(recorder.vosk, "KaldiRecognizer", return_value=rec), \
         mock.patch.object(recorder.subprocess, "Popen", return_value=proc):
        pcm, reason = recorder.record("以上", 1.2, 30.0)
    assert proc.terminate_called is True
    assert reason == FinalizeReason.word
    assert pcm == loud


def test_onset_timeout_terminates_and_returns_empty():
    rec = _FakeRecognizer()
    proc = _FakeProc([], block_forever=True)
    recorder._vosk_model = None
    import time
    start = time.monotonic()
    with mock.patch.object(recorder.vosk, "Model", return_value=mock.Mock()), \
         mock.patch.object(recorder.vosk, "KaldiRecognizer", return_value=rec), \
         mock.patch.object(recorder.subprocess, "Popen", return_value=proc):
        pcm, reason = recorder.record("以上", 1.2, 0.2)
    assert proc.terminate_called is True
    assert pcm == b""
    assert reason == FinalizeReason.timeout
    assert time.monotonic() - start < 2.0


def test_vosk_model_load_failure_returns_timeout():
    recorder._vosk_model = None
    with mock.patch.object(recorder.vosk, "Model", side_effect=RuntimeError("no model")), \
         mock.patch.object(recorder.subprocess, "Popen") as popen:
        pcm, reason = recorder.record("以上", 1.2, 30.0)
    assert pcm == b""
    assert reason == FinalizeReason.timeout
    assert popen.call_count == 0  # sox は起動しない


def test_sox_launch_failure_returns_timeout():
    rec = _FakeRecognizer()
    recorder._vosk_model = None
    with mock.patch.object(recorder.vosk, "Model", return_value=mock.Mock()), \
         mock.patch.object(recorder.vosk, "KaldiRecognizer", return_value=rec), \
         mock.patch.object(recorder.subprocess, "Popen", side_effect=FileNotFoundError()):
        pcm, reason = recorder.record("以上", 1.2, 30.0)
    assert pcm == b""
    assert reason == FinalizeReason.timeout


def test_accept_waveform_exception_does_not_crash():
    rec = _FakeRecognizer()
    rec.AcceptWaveform = mock.Mock(side_effect=RuntimeError("boom"))
    loud = (b"\xff\x7f") * 2048
    proc = _FakeProc([loud])
    recorder._vosk_model = None
    with mock.patch.object(recorder.vosk, "Model", return_value=mock.Mock()), \
         mock.patch.object(recorder.vosk, "KaldiRecognizer", return_value=rec), \
         mock.patch.object(recorder.subprocess, "Popen", return_value=proc):
        pcm, reason = recorder.record("以上", 1.2, 30.0)
    assert reason == FinalizeReason.silence  # 例外は握って完走
