from unittest import mock

import requests

from claude_voice.speak import synthesizer


def _resp(status=200, json_data=None, content=b""):
    r = mock.Mock()
    r.status_code = status
    r.json.return_value = json_data if json_data is not None else {"q": 1}
    r.content = content
    return r


def test_empty_text_skips_http():
    with mock.patch.object(synthesizer, "requests") as req:
        assert synthesizer.synthesize("", 1) is None
        assert req.post.call_count == 0


def test_happy_path_calls_query_then_synthesis():
    query = _resp(200, {"accent": "x"})
    synth = _resp(200, content=b"RIFFxxxx")
    with mock.patch.object(synthesizer.requests, "post", side_effect=[query, synth]) as post:
        wav = synthesizer.synthesize("こんにちは", 5)
    assert wav == b"RIFFxxxx"
    first, second = post.call_args_list
    assert first.args[0].endswith("/audio_query")
    assert first.kwargs["params"] == {"text": "こんにちは", "speaker": 5}
    assert second.args[0].endswith("/synthesis")
    assert second.kwargs["params"] == {"speaker": 5}
    assert second.kwargs["json"] == {"accent": "x"}


def test_audio_query_5xx_returns_none():
    with mock.patch.object(synthesizer.requests, "post", side_effect=[_resp(500)]):
        assert synthesizer.synthesize("x", 1) is None


def test_synthesis_5xx_returns_none():
    with mock.patch.object(synthesizer.requests, "post", side_effect=[_resp(200), _resp(503)]):
        assert synthesizer.synthesize("x", 1) is None


def test_empty_body_returns_none():
    with mock.patch.object(synthesizer.requests, "post", side_effect=[_resp(200), _resp(200, content=b"")]):
        assert synthesizer.synthesize("x", 1) is None


def test_connection_error_returns_none():
    with mock.patch.object(synthesizer.requests, "post", side_effect=requests.ConnectionError()):
        assert synthesizer.synthesize("x", 1) is None


def test_timeout_returns_none():
    with mock.patch.object(synthesizer.requests, "post", side_effect=requests.Timeout()):
        assert synthesizer.synthesize("x", 1) is None


def test_json_decode_error_returns_none():
    bad = _resp(200)
    bad.json.side_effect = ValueError("bad json")
    with mock.patch.object(synthesizer.requests, "post", side_effect=[bad]):
        assert synthesizer.synthesize("x", 1) is None


def test_arbitrary_exception_returns_none():
    with mock.patch.object(synthesizer.requests, "post", side_effect=RuntimeError("boom")):
        assert synthesizer.synthesize("x", 1) is None
