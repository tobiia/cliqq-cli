import pytest
from pathlib import Path
from unittest.mock import Mock


from cliqq import ai


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (["a", "b", "c", "d", "e", "f"], ["abcde", "f"]),
        (
            ["This is a co", "mmand for", " you: \x1e{ '", "do':1 }\x1f"],
            ["This is a command for you: \x1e{ 'do':1 }\x1f"],
        ),
    ],
)
def test_buffer_deltas_basic(test_input, expected):
    # flushes after 5, then final one
    result = list(ai.buffer_deltas(test_input))
    assert result == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ('hello \x1e{ "do":1 }\x1f bye', '{ "do":1 }'),
        ("no markers here", None),
        ("i'm missing one of the delimitors \x1e{'do':1}", None),
    ],
)
def test_extract_action(test_input, expected):
    result = ai.extract_action(test_input)
    if expected is None:
        assert result is None
    else:
        assert result == expected


def test_load_env_file(tmp_path):
    envfile = tmp_path / ".env"
    envfile.write_text("MODEL_NAME=m\nBASE_URL=b\nAPI_KEY=k\n")
    config = ai.load_env_file(envfile)
    assert config == {"model_name": "m", "base_url": "b", "api_key": "k"}


def test_load_sys_env(monkeypatch):
    monkeypatch.setenv("MODEL_NAME", "m")
    monkeypatch.setenv("BASE_URL", "b")
    monkeypatch.setenv("API_KEY", "k")
    config = ai.load_sys_env()
    assert config == {"model_name": "m", "base_url": "b", "api_key": "k"}


def test_validate_api_success(monkeypatch):
    monkeypatch.setattr(ai, "ping_api", lambda c: True)
    monkeypatch.setattr(ai, "offer_save_env", lambda c, e: None)
    valid = ai.validate_api(
        {"model_name": "m", "base_url": "b", "api_key": "k"}, Path("dummy")
    )
    assert valid is True


def test_validate_api_fail(monkeypatch):
    # fake for openai.AuthenticationError b/c constructor won't work
    class FakeAuthError(Exception):
        pass

    monkeypatch.setattr(ai.openai, "AuthenticationError", FakeAuthError)

    def bad_ping(config):
        raise FakeAuthError

    monkeypatch.setattr(ai, "ping_api", bad_ping)

    valid = ai.validate_api(
        {"model_name": "m", "base_url": "b", "api_key": "k"}, Path("dummy")
    )
    assert valid is False


def test_ensure_api_fail(monkeypatch):

    def fail_find(env_path):
        raise ValueError()

    env_path = Path("dummy")
    api_config = Mock()
    # force check api credentials b/c one is empty
    api_config.model_name = ""

    monkeypatch.setattr(ai, "find_api_info", fail_find)
    monkeypatch.setattr(ai, "program_output", lambda *a, **k: None)

    result = ai.ensure_api(api_config, env_path)
    assert result is False


# integration test: success
def test_ai_response_success(monkeypatch):
    # fake ensure_api always valid
    monkeypatch.setattr(ai, "ensure_api", lambda cfg, env: True)
    # fake stream
    monkeypatch.setattr(
        ai,
        "stream_chunks",
        lambda *a, **k: iter(["Hello ", "world\n", "\x1e{1}\x1f", " done"]),
    )
    # silence program_output
    monkeypatch.setattr(ai, "program_output", lambda msg, **k: None)

    api_config = Mock()
    api_config.model_name = "m"
    api_config.base_url = "b"
    api_config.api_key = "k"

    history = Mock()
    history.chat_history = []
    history.remember = Mock()

    actionable, response_content = ai.ai_response(
        "prompt", api_config, history, Path("dummy")
    )

    assert actionable is True
    assert response_content
    assert response_content["text"] == "Hello world\n\x1e{1}\x1f done"
    assert response_content["action"] == "{1}"
    history.remember.assert_any_call({"role": "user", "content": "prompt"})
    history.remember.assert_any_call({"role": "assistant", "content": Mock.ANY})
