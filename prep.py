import os
import sys
import re
import psutil
import argparse

# TODO add exit command to end program
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
    "reset": {
        "description": "Reset Cliqq conversation history",
        "function": clear_history,
        "args": None,
    },
    "run": {
        "description": "Run a command and have Cliqq analyze the output",
        "function": run_command,
        "args": "[command]",
    },
    "q": {
        "description": "Non-interactive mode: send a single prompt and quickly get a response",
        "function": quick_response,
        "args": "[prompt]",
    },
}


def parse_commands(argv=None):
    parser = argparse.ArgumentParser(
        description="A simple, lightweight command line chat assistant"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command, info in commands.items():
        subparser = subparsers.add_parser(command, help=info["description"])

        if info.get("args") is not None:
            if "positional" in info["args"]:
                subparser.add_argument("arg", help=info["args"])

    # Example global flag
    # parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")

    # if argv is None it will get args from sys
    return parser.parse_args(argv)


def dispatch(args, session):
    command_info = commands[args.command]
    func = command_info["function"]

    if command_info.get("args") is not None:
        # Pass along the positional arg
        return func(args.arg, session)
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
