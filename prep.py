import os
import sys
import re
import psutil
import argparse

commands = {
    "help": {
        "description": "List Cliqq commands and what they do",
        "function": help,
        "args": None,
    },
    "log": {
        "description": "See chat log",
        "function": show_log,
        "args": None,
    },
    "clear": {
        "description": "Clear the terminal window",
        "function": clear,
        "args": None,
    },
    "run": {
        "description": "Run a command and have Cliqq analyze the output",
        "function": run_command,
        "args": "[command]",
    },
    "reset": {
        "description": "Reset Cliqq conversation history",
        "function": clear_history,
        "args": None,
    },
    "q": {
        "description": "Non-interactive mode: send a single prompt and quickly get a response",
        "function": quick_response,
        "args": "[prompt]",
    },
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="A simple, lightweight command line chat assistant"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command, info in commands.items():
        subparser = subparsers.add_parser(command, help=info["description"])

        if info.get("args") is not None:
            if "positional" in info["args"]:
                subparser.add_argument("arg", help=info["args"])

    """"
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose mode"
    )
    """

    return parser.parse_args()


def dispatch(args):
    """Run the appropriate function based on parsed args."""
    command_info = commands[args.command]
    func = command_info["function"]

    if command_info.get("args") is not None:
        # Pass along the positional arg
        return func(args.arg)
    else:
        return func()


def prep_prompt(prompt, path):
    op_sys = sys.platform
    shell = psutil.Process(os.getppid()).name()
    cwd = os.getcwd()

    with open(path) as file:
        prompt_template = file.read()
    prompt_template = re.sub(r"{OS}", op_sys, prompt_template)
    prompt_template = re.sub(r"{SHELL}", shell, prompt_template)
    prompt_template = re.sub(r"{CWD}", cwd, prompt_template)
    prompt_template = re.sub(r"{QUESTION}", prompt, prompt_template)
    return prompt_template
