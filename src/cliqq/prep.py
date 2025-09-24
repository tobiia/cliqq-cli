import os
import sys
import re
import psutil
import argparse
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cliqq.models import CommandRegistry


# usage
# args = parser.parse_args([list of each argument given]) = obj with properties that correspond to args given
# note: this is written where you always have .prompt and .command, args iff needed
def parse_commands(registry: CommandRegistry) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
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

    # removing "cliqq" b/c argparse will interpret it as a command (prog)
    if len(tokens) > 0 and tokens[0] == "cliqq":
        tokens = tokens[1:]
    try:
        ns = parser.parse_args(tokens)
    except SystemExit:
        # occurs if argsv only has 1 word non-prompt or if user starts prompt with "cliqq"
        # or if user enters a command with no args with an argument
        # fallback: treat everything as a prompt
        if tokens and tokens[0].startswith("/"):
            # user tried a command but misused it
            ns = argparse.Namespace(command="/invalid", args=tokens, prompt=[])
        else:
            ns = argparse.Namespace(command=None, prompt=tokens)
    # ensure .args always exists
    if not hasattr(ns, "args"):
        ns.args = []
    return ns


def prep_prompt(prompt: str, template: str) -> str:
    op_sys = sys.platform
    shell = psutil.Process(os.getppid()).name()
    cwd = os.getcwd()
    # this is potentially sensitive info
    safe_cwd = cwd.replace(str(Path.home()), "~")

    prompt_template = re.sub(r"<OS>", op_sys, template)
    prompt_template = re.sub(r"<SHELL>", shell, prompt_template)
    prompt_template = re.sub(r"<CWD>", safe_cwd, prompt_template)
    prompt_template = re.sub(r"<QUESTION>", prompt, prompt_template)
    return prompt_template


# ARGPARSE --> when adding more commands, some examples:
"""
    ex. for flag args
    change api key --> would probs update .env and/or sys envars, repeat for model and url
    name = what user sees, dest = var name which defaults to name
    parser.add_argument(
        "--key", 
        "--api-key",
        nargs=1,
        help="change api key",
        dest="key",
    )
    cliqq --key sk-s7gd8
    args.key = [sk-s7gd8]    (won't be in a list if you don't specify nargs) 
"""

"""
    cliqq api beepo-8 www.beep.com sk-s7gd8 --> error if you don't put all 3
    ways to implement the above:
    subparser.add_argument(
        "api",
        nargs=3,
        metavar=("model_name", "base_url", "api_key"),
        help="Set API credentials immediately.",
    )
        args.api = [model_name, base_url, api_key]
        you can use nargs="*" for above or ="?" below if you want to allow less and have it match
    OR
    subparser.add_argument("model_name", help="The model name")
    subparser.add_argument("base_url", help="The API base URL")
    subparser.add_argument("api_key", help="The API key")
        args.model_name --> for all, order is guarenteed
"""
