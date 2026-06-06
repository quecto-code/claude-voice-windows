from unittest import mock

from claude_voice import config
from claude_voice.speak import player


def _ok():
    r = mock.Mock()
    r.returncode = 0
    r.stderr = b""
    return r


def test_play_success_runs_sox_with_input():
    with mock.patch.object(player.subprocess, "run", return_value=_ok()) as run:
        assert player.play(b"RIFFwav") is True
    cmd = run.call_args.args[0]
    assert cmd[0] == "sox"
    assert run.call_args.kwargs["input"] == b"RIFFwav"


def test_play_uses_waveaudio_device():
    with mock.patch.object(player.subprocess, "run", return_value=_ok()) as run:
        player.play(b"x")
    cmd = run.call_args.args[0]
    # Windows ネイティブ: 出力は waveaudio 既定デバイス（ADR-0005）
    assert "waveaudio" in cmd
    assert "pulseaudio" not in cmd
    i = cmd.index("waveaudio")
    assert cmd[i + 1] == "default"


def test_play_command_has_buffer_and_rate():
    with mock.patch.object(player.subprocess, "run", return_value=_ok()) as run:
        player.play(b"x")
    cmd = run.call_args.args[0]
    assert "--buffer" in cmd
    assert cmd[cmd.index("--buffer") + 1] == str(config.SOX_BUFFER_BYTES)
    assert "rate" in cmd and "-v" in cmd
    assert cmd[-1] == str(config.PLAYBACK_SAMPLE_RATE)


def test_play_nonzero_returncode_returns_false():
    r = mock.Mock()
    r.returncode = 1
    r.stderr = b"sox error"
    with mock.patch.object(player.subprocess, "run", return_value=r):
        assert player.play(b"x") is False


def test_play_file_not_found_returns_false():
    with mock.patch.object(player.subprocess, "run", side_effect=FileNotFoundError()):
        assert player.play(b"x") is False


def test_play_arbitrary_exception_returns_false():
    with mock.patch.object(player.subprocess, "run", side_effect=OSError("boom")):
        assert player.play(b"x") is False
