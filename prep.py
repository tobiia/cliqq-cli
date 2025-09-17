import os
import sys
import re
import psutil
import argparse
from commands import CliqqSession


def parse_commands(session: CliqqSession) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A simple, lightweight command line chat assistant"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command, info in session._commands.items():
        subparser = subparsers.add_parser(command, help=info["description"])

        if info.get("args") is not None:
            if "positional" in info["args"]:
                subparser.add_argument("arg", help=info["args"])

    # parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
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
