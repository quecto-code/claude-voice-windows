from unittest import mock

import claude_voice.listen as listen_pkg
from claude_voice import config
from claude_voice.listen import listen, _strip_finalize_word
from claude_voice.types import FinalizeReason, ListenResult


def _patch(record_ret=None, record_exc=None, transcribe_ret=None, transcribe_exc=None):
    rec = mock.patch.object(
        listen_pkg.recorder, "record",
        side_effect=record_exc, return_value=record_ret,
    )
    tr = mock.patch.object(
        listen_pkg.transcriber, "transcribe",
        side_effect=transcribe_exc, return_value=transcribe_ret,
    )
    return rec, tr


def test_timeout_short_circuits_to_silent():
    rec, tr = _patch(record_ret=(b"", FinalizeReason.timeout))
    with rec, tr:
        assert listen() == ListenResult("", "silent")


def test_silence_with_none_transcript_is_unintelligible():
    rec, tr = _patch(record_ret=(b"pcm", FinalizeReason.silence), transcribe_ret=None)
    with rec, tr:
        assert listen() == ListenResult("", "unintelligible")


def test_silence_with_blank_transcript_is_unintelligible():
    rec, tr = _patch(record_ret=(b"pcm", FinalizeReason.silence), transcribe_ret="   ")
    with rec, tr:
        assert listen() == ListenResult("", "unintelligible")


def test_silence_with_text_is_ok():
    rec, tr = _patch(record_ret=(b"pcm", FinalizeReason.silence), transcribe_ret="ファイルを開いて")
    with rec, tr:
        assert listen() == ListenResult("ファイルを開いて", "ok")


def test_word_with_text_strips_finalize_word():
    rec, tr = _patch(record_ret=(b"pcm", FinalizeReason.word), transcribe_ret="ビルドして以上")
    with rec, tr:
        assert listen() == ListenResult("ビルドして", "ok")


def test_record_uses_config_values():
    rec, tr = _patch(record_ret=(b"", FinalizeReason.timeout))
    with rec as record_mock, tr:
        listen()
    assert record_mock.call_args.kwargs == {
        "finalize_word": config.FINALIZE_WORD,
        "silence_sec": config.SILENCE_SEC,
        "onset_timeout_sec": config.ONSET_TIMEOUT_SEC,
    }


def test_record_exception_is_unintelligible():
    rec, tr = _patch(record_exc=RuntimeError("boom"))
    with rec, tr:
        assert listen() == ListenResult("", "unintelligible")


def test_transcribe_exception_is_unintelligible():
    rec, tr = _patch(record_ret=(b"pcm", FinalizeReason.silence), transcribe_exc=OSError("x"))
    with rec, tr:
        assert listen() == ListenResult("", "unintelligible")


def test_strip_finalize_word_handles_trailing_punct():
    assert _strip_finalize_word("テストして、以上。", "以上") == "テストして"
    assert _strip_finalize_word("以上のみ", "以上") == "以上のみ"  # 末尾でなければ残す
    assert _strip_finalize_word("やる 以上", "以上") == "やる"
