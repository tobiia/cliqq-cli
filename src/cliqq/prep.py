import os
import sys
import re
import psutil
import argparse

from classes import CommandRegistry


# usage
# args = parser.parse_args([list of each argument given]) = obj with properties that correspond to args given
def parse_commands(registry: CommandRegistry) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cliqq", description="A simple, lightweight command line chat assistant"
    )

    """ ex. cliqq q "how to make pasta", q = subcommand, "how to make pasta" = arg for sub
    commands are considered args, so below line adds an attr same as the one above
    so can access command via args.command, which is an obj that can have its own args (add_argument) and such 
    """
    subparsers = parser.add_subparsers(dest="command")

    for command_name, command in registry.commands.items():
        subparser = subparsers.add_parser(command_name, help=command.description)

        if command.args:
            subparser.add_argument("arg", nargs=argparse.REMAINDER, help=command.args)
            # NOTE parser_foo.set_defaults(func=foo) --> use if you can figure out a way to avoid passing session explicitly

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


def prep_prompt(prompt: str, template: str) -> str:
    op_sys = sys.platform
    shell = psutil.Process(os.getppid()).name()
    cwd = os.getcwd()

    prompt_template = re.sub(r"{OS}", op_sys, template)
    prompt_template = re.sub(r"{SHELL}", shell, prompt_template)
    prompt_template = re.sub(r"{CWD}", cwd, prompt_template)
    prompt_template = re.sub(r"{QUESTION}", prompt, prompt_template)
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
