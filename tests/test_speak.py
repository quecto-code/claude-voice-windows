import threading
import time
from unittest import mock

from claude_voice import config
from claude_voice.speak import speak
import claude_voice.speak as speak_pkg
from claude_voice.types import SpeakResult


def test_empty_text_returns_ok_without_synthesis():
    with mock.patch.object(speak_pkg.synthesizer, "synthesize") as syn:
        assert speak("") == SpeakResult(ok=True, error=None)
        assert syn.call_count == 0


def test_synthesis_failure():
    with mock.patch.object(speak_pkg.synthesizer, "synthesize", return_value=None):
        assert speak("x") == SpeakResult(ok=False, error="voicevox synthesis failed")


def test_playback_failure():
    with mock.patch.object(speak_pkg.synthesizer, "synthesize", return_value=b"wav"), \
         mock.patch.object(speak_pkg.player, "play", return_value=False):
        assert speak("x") == SpeakResult(ok=False, error="playback failed")


def test_success_passes_speaker_id():
    with mock.patch.object(speak_pkg.synthesizer, "synthesize", return_value=b"wav") as syn, \
         mock.patch.object(speak_pkg.player, "play", return_value=True):
        assert speak("やあ") == SpeakResult(ok=True, error=None)
    assert syn.call_args.kwargs["speaker"] == config.SPEAKER_ID


def test_lock_is_threading_lock():
    assert isinstance(speak_pkg._lock, type(threading.Lock()))


def test_no_overlap_under_concurrency():
    in_flight = {"n": 0}
    overlap_seen = []

    def slow_play(_wav):
        in_flight["n"] += 1
        if in_flight["n"] > 1:
            overlap_seen.append(True)
        time.sleep(0.05)
        in_flight["n"] -= 1
        return True

    with mock.patch.object(speak_pkg.synthesizer, "synthesize", return_value=b"wav"), \
         mock.patch.object(speak_pkg.player, "play", side_effect=slow_play):
        threads = [threading.Thread(target=lambda: speak("x")) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    assert overlap_seen == []
