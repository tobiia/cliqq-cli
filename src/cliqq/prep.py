import os
import sys
import json
import psutil
import argparse
from pathlib import Path
from cliqq.log import logger
from cliqq.models import CommandRegistry, QuietArgParser


# usage
# args = parser.parse_args([list of each argument given]) = obj with properties that correspond to args given
# note: this is written where you always have .prompt and .command, args iff needed
def parse_commands(registry: CommandRegistry) -> argparse.ArgumentParser:
    parser = QuietArgParser(
        prog="cliqq", description="A simple, lightweight command line chat assistant"
    )

    """ ex. cliqq q "how to make pasta", q = subcommand, "how to make pasta" = arg for sub
    commands are considered args, so below line adds an attr same as the one above
    so can access command via args.command, which is an obj that can have its own args (add_argument) and such 
    """
    subparsers = parser.add_subparsers(dest="command")
    # dest means .command always exists

    for command_name, command in registry.commands.items():
        subparser = subparsers.add_parser(command_name, help=command.description)

        if command.args:
            subparser.add_argument("args", nargs="+", help=command.args)

    # ex. cliqq how to make pasta
    # args = parser.parse_args(["cliqq", "how to make pasta"])
    # args.prompt = "how to make pasta"
    # order when adding subcommands and args matters a lot hence above
    parser.add_argument(
        "prompt",
        nargs=argparse.REMAINDER,
        help="Start a conversation with Cliqq with your prompt",
    )

    return parser


# namespace returned ALWAYS has .command, .prompt. and .args
def parse_input(
    tokens: list[str], parser: argparse.ArgumentParser
) -> argparse.Namespace:

    cleaned = []
    for t in tokens:
        if not t:  # skip empty
            continue
        # strip away things like `cliqq`, `cliqq.exe`, `python`, `-m`, or file paths ending in .py
        if t in {"cliqq", "python", "python.exe", "-m"}:
            continue
        if t.endswith(".py") or t.endswith("__main__.py"):
            continue
        cleaned.append(t)
    tokens = cleaned

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
    try:
        return json.loads(action_str)
    except json.JSONDecodeError as e:
        logger.exception("Unable to parse actionable: %s", e)
        return None
