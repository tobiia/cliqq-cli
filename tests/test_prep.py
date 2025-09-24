import argparse
import os
import shlex
import types
import sys
import pytest

from cliqq import models, prep


@pytest.mark.parametrize(
    "user_input,expected_command,expected_arg,expected_prompt",
    [
        # starts with "cliqq"
        ("cliqq /withargs hey", "/withargs", ["hey"], []),  # valid command with args
        ("cliqq /withargs", "/invalid", ["/withargs"], []),  # invalid command w args
        ("cliqq /noargs", "/noargs", [], []),  # valid command
        (
            "cliqq /noargs hey",
            "/invalid",
            ["/noargs", "hey"],
            [],
        ),  # invalid command no args
        ("cliqq", None, [], []),  # empty prompt w prog name
        ("cliqq hi", None, [], ["hi"]),  # 1 word prompt
        ("cliqq what is this", None, [], ["what", "is", "this"]),  # multi-word prompt
        # no "cliqq"
        ("/withargs hey", "/withargs", ["hey"], []),  # valid command with args
        (
            "/withargs",
            "/invalid",
            ["/withargs"],
            [],
        ),  # invalid command with args
        ("/noargs", "/noargs", [], []),  # valid command no args
        (
            "/noargs hey",
            "/invalid",
            ["/noargs", "hey"],
            [],
        ),  # invalid command no args
        ("", None, [], []),  # empty
        ("hi", None, [], ["hi"]),  # free prompt
        ("what is this", None, [], ["what", "is", "this"]),  # free prompt
    ],
)
def test_parse_input(user_input, expected_command, expected_arg, expected_prompt):
    command_registry = models.CommandRegistry()
    # using fake commands
    commands = {
        "/noargs": models.Command(
            name="/noargs",
            description="A command with no args",
            function=lambda *a, **k: None,
        ),
        "/withargs": models.Command(
            name="/withargs",
            description="A command with args",
            function=lambda *a, **k: None,
            args="arguments",
        ),
    }
    command_registry.commands = commands

    parser = prep.parse_commands(command_registry)
    tokens = shlex.split(user_input) if user_input else []
    parsed_input = prep.parse_input(tokens, parser)

    assert parser.prog == "cliqq"
    # can return false negative if any are None

    if expected_command is None:
        assert parsed_input.command is None
    else:
        assert parsed_input.command == expected_command

    if expected_prompt is None:
        assert parsed_input.prompt is None
    else:
        assert parsed_input.prompt == expected_prompt

    if expected_arg is None:
        assert parsed_input.args is None
    else:
        assert parsed_input.args == expected_arg


def test_parse_commands():
    command_registry = models.CommandRegistry()
    # using fake commands
    commands = {
        "/noargs": models.Command(
            name="/noargs",
            description="A command with no args",
            function=lambda *a, **k: None,
        ),
        "/withargs": models.Command(
            name="/withargs",
            description="A command with args",
            function=lambda *a, **k: None,
            args="arguments",
        ),
    }
    command_registry.commands = commands
    parser = prep.parse_commands(command_registry)

    help_output = parser.format_help()

    # verify both commands are added to the parser
    assert "/noargs" in help_output
    assert "/withargs" in help_output

    # verify both descriptions are in the help msg
    assert command_registry.commands["/noargs"].description in help_output
    assert command_registry.commands["/withargs"].description in help_output


@pytest.mark.parametrize(
    "template,expected",
    [
        ("hello template", "hello template"),
        ("OS=<OS>", "OS=win32"),
        (
            "You are in <SHELL> at <CWD>",
            "You are in bash at /fake/path",
        ),
        ("question: <QUESTION>", "question: hello"),
    ],
)
def test_prep_prompt(monkeypatch, template, expected):

    # monkeypath = fixture that lets you replace attributes, functions, or variables in tests
    # setattr -> replace an attribute on an object or module
    # remember: methods are just attributes on classes
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(os, "getcwd", lambda: "/fake/path")
    monkeypatch.setattr(
        "psutil.Process", lambda pid: types.SimpleNamespace(name=lambda: "bash")
    )

    result = prep.prep_prompt("hello", template)
    assert result == expected


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
def test_parse_action(input_str, expected):
    result = prep.parse_action(input_str)
    if expected is None:
        assert result is None
    else:
        assert result == expected


def test_load_template(tmp_path):
    # Create a fake template file
    file_content = "this is meant to be inside a file!"
    tfile = tmp_path / "templates" / "starter.txt"
    tfile.parent.mkdir(parents=True, exist_ok=True)
    tfile.write_text(file_content)

    # check file is loaded correctly
    template = prep.load_template(tfile).strip()
    assert template == file_content
