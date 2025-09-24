import pytest
import re
from unittest.mock import Mock
from cliqq import action


def test_execute_command_success():
    code, out, err = action.execute_command("python --version")
    assert code == 0
    assert "Python" in out or "Python" in err


def test_execute_command_notfound():
    code, out, err = action.execute_command("nonexistent_command_xyz")
    assert code != 0
    assert out == ""

    error_patterns = [
        r"not.*recognized",
        r"not.*found",
        r"No such file",
        r"command.*not.*found",
    ]

    assert any(
        re.search(pattern, err, re.IGNORECASE) for pattern in error_patterns
    ), f"Expected error pattern not found in: {err}"


# testing func run
def test_run_valid_command(monkeypatch):
    monkeypatch.setattr(action, "run_command", lambda *a, **k: True)
    data = {"action": "command", "command": "cd"}
    result = action.run(data, Mock(), Mock(), Mock())
    assert result is True


# testing func run
def test_run_file(monkeypatch):
    monkeypatch.setattr(action, "save_file", lambda *a, **k: True)
    data = {"action": "file", "path": "/tmp/test", "content": "ok"}
    result = action.run(data, Mock(), Mock(), Mock())
    assert result is True


def test_run_invalid_json():
    data = {"action": "other", "text": "what?"}
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
