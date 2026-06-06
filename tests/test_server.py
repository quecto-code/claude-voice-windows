from unittest import mock

from claude_voice import server
from claude_voice.types import ListenResult, SpeakResult


def test_voice_ping():
    assert server.voice_ping() == "pong"


def test_voice_listen_delegates():
    sentinel = ListenResult("やあ", "ok")
    with mock.patch.object(server, "_listen", return_value=sentinel) as m:
        assert server.voice_listen() is sentinel
        m.assert_called_once_with()


def test_voice_speak_delegates():
    sentinel = SpeakResult(ok=True, error=None)
    with mock.patch.object(server, "_speak", return_value=sentinel) as m:
        assert server.voice_speak("テスト") is sentinel
        m.assert_called_once_with("テスト")
