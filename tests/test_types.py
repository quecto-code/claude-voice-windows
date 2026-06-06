from claude_voice.types import FinalizeReason, ListenResult, SpeakResult


def test_finalize_reason_values():
    assert FinalizeReason.silence.value == "silence"
    assert FinalizeReason.word.value == "word"
    assert FinalizeReason.timeout.value == "timeout"


def test_listen_result_frozen():
    r = ListenResult("こんにちは", "ok")
    assert r.transcript == "こんにちは"
    assert r.status == "ok"


def test_speak_result_frozen():
    r = SpeakResult(ok=True, error=None)
    assert r.ok is True
    assert r.error is None
