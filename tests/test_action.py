import pytest
from unittest.mock import Mock
from cliqq import action


@pytest.mark.parametrize(
    "input_str,expected",
    [
        (
            '{"action":"command","command":"echo hi"}',
            {"action": "command", "command": "echo hi"},
        ),
        (
            '{"action":"file","path":"/fake/path","content":"this is in the file"}',
            {"action": "file", "path": "/fake/path", "content": "this is in the file"},
        ),
        ("not valid json", None),
    ],
)
def test_parse_actionable(input_str, expected):
    result = action.parse_actionable(input_str)
    if expected is None:
        assert result is None
    else:
        assert result == expected


def test_execute_command_success():
    code, out, err = action.execute_command("echo hello")
    assert code == 0
    assert "hello" in out
    assert err == ""


def test_execute_command_notfound():
    code, out, err = action.execute_command("nonexistent_command_xyz")
    assert code == 127
    assert out == ""
    assert "Command not found" in err


def test_run_command(monkeypatch):
    monkeypatch.setattr(action, "run_command", lambda d: True)
    data = '{"action":"command","command":"ls"}'
    result = action.run(data, Mock(), Mock(), Mock())
    assert result is True


def test_run_file(monkeypatch):
    monkeypatch.setattr(action, "save_file", lambda d: True)
    data = '{"action":"file","path":"/tmp/test","content":"ok"}'
    result = action.run(data, Mock(), Mock(), Mock())
    assert result is True


def test_run_invalid():
    data = '{"action":"other","text":"what?"}'
    result = action.run(data, Mock(), Mock(), Mock())
    assert result is False


def test_save_file_success(tmp_path):
    fpath = tmp_path / "out.txt"
    file = {"path": fpath, "content": "hello"}
    result = action.save_file(file, overwrite=True)
    assert result
    assert fpath.read_text() == "hello"


def test_save_file_conflict_overwrite(monkeypatch, tmp_path):
    # create file
    fpath = tmp_path / "out.txt"
    fpath.write_text("old")
    # same path as existing
    file = {"path": fpath, "content": "new"}

    monkeypatch.setattr(action, "program_choice", lambda *a, **k: "yes")
    result = action.save_file(file, overwrite=False)
    assert result
    assert fpath.read_text() == "new"


def test_save_file_conflict_newfile(monkeypatch, tmp_path):
    fpath = tmp_path / "out.txt"
    fpath.write_text("old")
    file = {"path": fpath, "content": "new"}

    monkeypatch.setattr(action, "program_choice", lambda *a, **k: "no")
    monkeypatch.setattr(action, "user_input", lambda: "other.txt")
    result = action.save_file(file, overwrite=False)
    assert result
    assert (tmp_path / "other.txt").exists()
