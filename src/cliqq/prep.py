import os
import sys
import json
import psutil
import argparse
from pathlib import Path
from cliqq.log import logger
from cliqq.models import CommandRegistry, QuietArgParser


def parse_commands(registry: CommandRegistry) -> argparse.ArgumentParser:
    """Build the argument parser with available subcommands.
    Usage: parser.parse_args([list of each argument given]) = obj with properties that correspond to args given

    ex. cliqq q "how to make pasta", q = subcommand, "how to make pasta" = arg for sub
    ex. cliqq how to make pasta

    args = parser.parse_args(["cliqq", "how to make pasta"])
    args.prompt = "how to make pasta"

    Args:
        registry (CommandRegistry): Registry containing command definitions.

    Returns:
        argparse.ArgumentParser: Configured parser instance.
    """

    parser = QuietArgParser(
        prog="cliqq", description="A simple, lightweight command line chat assistant"
    )

    subparsers = parser.add_subparsers(dest="command")

    for command_name, command in registry.commands.items():
        subparser = subparsers.add_parser(command_name, help=command.description)

        if command.args:
            subparser.add_argument("args", nargs="+", help=command.args)

    parser.add_argument(
        "prompt",
        nargs=argparse.REMAINDER,
        help="Start a conversation with Cliqq with your prompt",
    )

    return parser


def parse_input(
    tokens: list[str], parser: argparse.ArgumentParser
) -> argparse.Namespace:
    """Normalize raw input tokens into an argparse.Namespace.

    Handles filtering of program invocation tokens, error recovery,
    and ensures `.command`, `.args`, and `.prompt` attributes always exist.

    Args:
        tokens (list[str]): Raw input tokens.
        parser (argparse.ArgumentParser): Parser for known commands.

    Returns:
        argparse.Namespace: Parsed and normalized namespace.
    """

    # removing "cliqq" b/c argparse will interpret it as a command (prog)
    if len(tokens) > 0 and tokens[0] == "cliqq":
        tokens = tokens[1:]

    try:
        ns = parser.parse_args(tokens)

    except (SystemExit, ValueError):
        # occurs if argsv only has 1 word non-prompt or if user starts prompt with "cliqq"
        # or if user enters a command with no args with an argument
        # fallback: treat everything as a prompt
        if tokens and tokens[0].startswith("/"):
            # user tried a command but misused it
            ns = argparse.Namespace(command="/invalid", args=tokens, prompt=[])
        else:
            ns = argparse.Namespace(command=None, prompt=tokens)

    # NORMALIZATION ==> want a consistent structure
    # ensure .args and .prompt always exists
    setattr(ns, "args", getattr(ns, "args", []))
    setattr(ns, "prompt", getattr(ns, "prompt", []))
    # should only have empty [] rather than [""]
    ns.prompt = [x for x in ns.prompt if x] if ns.prompt else []

    return ns


def prep_prompt(prompt: str, template: str) -> str:
    """Insert system context and user question into a template."""

    op_sys = sys.platform
    shell = psutil.Process(os.getppid()).name()
    cwd = os.getcwd()
    # this is potentially sensitive info
    safe_cwd = cwd.replace(str(Path.home()), "~")

    prompt_template = template.replace("<OS>", op_sys)
    prompt_template = prompt_template.replace("<SHELL>", shell)
    prompt_template = prompt_template.replace("<CWD>", safe_cwd)
    prompt_template = prompt_template.replace("<QUESTION>", prompt)
    return prompt_template


def parse_action(action_str: str) -> dict[str, str] | None:
    """Attempt to parse a JSON-encoded action string."""

    try:
        return json.loads(action_str)
    except json.JSONDecodeError as e:
        logger.exception("JSONDecodeError: Unable to parse action: %s", e)
        return None


# NOTE: for while i'm testing
def load_template(file_path: Path) -> str:
    """Load a text template from disk.

    Returns:
        str: Template contents, or a fallback default if file not found.
    """

    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError as e:
        logger.exception("FileNotFoundError: Error while loading template\n%s", e)
        return "You are a command line assistant running in a {OS} {SHELL} in {CWD}. {QUESTION}"


# NOTE: for when this is a pip-installable package
""" def load_template_pack(name: str) -> str:
    # templates is a subpackage of mypackage
    with resources.files("mypackage.templates").joinpath(name).open(
        "r", encoding="utf-8"
    ) as f:
        return f.read() """
