import argparse
import os
import shlex
import types
import sys
import pytest

from cliqq import main, prep, classes


@pytest.mark.parametrize(
    "user_input,expected_command,expected_arg,expected_prompt",
    [
        # starts with "cliqq"
        ("cliqq /withargs hey", "/withargs", ["hey"], []),  # valid command with args
        ("cliqq /withargs", "/invalid", ["/withargs"], []),  # invalid command w args
        ("cliqq /noargs", "/noargs", None, []),  # valid command
        (
            "cliqq /noargs hey",
            "/invalid",
            ["/noargs", "hey"],
            [],
        ),  # invalid command no args
        ("cliqq", None, None, []),  # empty prompt w prog name
        ("cliqq hi", None, None, ["hi"]),  # 1 word prompt
        ("cliqq what is this", None, None, ["what", "is", "this"]),  # multi-word prompt
        # no "cliqq"
        ("/withargs hey", "/withargs", ["hey"], []),  # valid command with args
        (
            "/withargs",
            "/invalid",
            ["/withargs"],
            [],
        ),  # invalid command with args
        ("/noargs", "/noargs", None, []),  # valid command no args
        (
            "/noargs hey",
            "/invalid",
            ["/noargs", "hey"],
            [],
        ),  # invalid command no args
        ("", None, None, []),  # empty
        ("hi", None, None, ["hi"]),  # free prompt
        ("what is this", None, None, ["what", "is", "this"]),  # free prompt
    ],
)
def test_parse_input(user_input, expected_command, expected_arg, expected_prompt):
    """Check parse_input for both normal and invalid cases."""
    command_registry = classes.CommandRegistry()
    # using fake commands
    commands = {
        "/noargs": classes.Command(
            name="/noargs",
            description="A command with no args",
            function=lambda *a, **k: None,
        ),
        "/withargs": classes.Command(
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

    # only check .args if it exists
    if hasattr(parsed_input, "args"):
        assert parsed_input.args == expected_arg
    else:
        assert expected_arg is None


def test_parse_commands():
    """Check parse_input for both normal and invalid cases."""
    command_registry = classes.CommandRegistry()
    # using fake commands
    commands = {
        "/noargs": classes.Command(
            name="/noargs",
            description="A command with no args",
            function=lambda *a, **k: None,
        ),
        "/withargs": classes.Command(
            name="/withargs",
            description="A command with args",
            function=lambda *a, **k: None,
            args="arguments",
        ),
    }
    command_registry.commands = commands
    parser = prep.parse_commands(command_registry)

    # check subcommands
    subparsers_action = None
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            subparsers_action = action
            break

    assert subparsers_action is not None

    subcommands = subparsers_action.choices
    assert "/noargs" in subcommands
    assert "/withargs" in subcommands

    # check help text
    assert (
        subcommands["/noargs"].description
        == command_registry.commands["/noargs"].description
    )
    assert (
        subcommands["/withargs"].description
        == command_registry.commands["/withargs"].description
    )


def test_load_template(tmp_path, file_content):
    """Check load_template"""
    # Create a fake template file
    tfile = tmp_path / "templates" / "starter.txt"
    tfile.parent.mkdir()
    tfile.write_text(file_content)

    # check file is loaded correctly
    prepped_template = main.load_template(tfile).strip()
    assert prepped_template == file_content


@pytest.mark.parametrize(
    "template,expected",
    [
        ("hello template", "hello template"),
        ("OS={OS}", "OS=win32"),
        (
            "You are in {SHELL} at {CWD}",
            "You are in bash at /fake/path",
        ),
        ("question: {QUESTION}", "question: hello"),
    ],
)
def test_prep_prompt(monkeypatch, template, expected):
    """Check load_template_local and prep_prompt with different templates."""

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
