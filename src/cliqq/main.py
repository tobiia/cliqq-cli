import shlex
import logging
import sys
import argparse
import os
from pathlib import Path

from prompt_toolkit import prompt
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText, to_plain_text
from styles import DEFAULT_STYLE
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit import choice

from classes import ApiConfig, ChatHistory, CommandRegistry, PathManager
from prep import prep_prompt, parse_commands, parse_input
from commands import dispatch, exit_cliqq
from ai import ai_response
from action import run
from log import logger


# NOTE: for when this is a pip-installable package
""" def load_template_pack(name: str) -> str:
    # templates is a subpackage of mypackage
    with resources.files("mypackage.templates").joinpath(name).open(
        "r", encoding="utf-8"
    ) as f:
        return f.read() """


# NOTE: for while i'm testing
def load_template(file_path: Path) -> str:
    try:
        with open(file_path) as f:
            return f.read()
    except FileNotFoundError as e:
        logger.exception("FileNotFoundError: %s", e)
        return "You are a command line assistant running in a {OS} {SHELL} in {CWD}. {QUESTION}"


def user_input(log: bool = True) -> str:
    message = FormattedText(
        [
            ("class:user", ">> "),
        ]
    )
    input = prompt(
        message=message, style=DEFAULT_STYLE, auto_suggest=AutoSuggestFromHistory()
    )
    if log:
        logger.info(f"{to_plain_text(message)}{input}\n")
    return input


def program_choice(question: str, choices: list, log: bool = True) -> str:
    # for simple menus
    message = FormattedText([("class:name", "(cliqq) "), ("class:action", question)])
    result = choice(
        message=message,
        options=choices,
        style=DEFAULT_STYLE,
    )
    if log:
        logger.info(f"{to_plain_text(message[0][1])}{question}\n")
        logger.info(f">> {result}\n")
    return result


# FIXME patch program output like logger in tests
def program_output(
    text: str,
    end: str = "\n",
    style_name: str = "program",
    log: bool = True,
):
    # action error program
    formatted_text = [
        ("class:name", "(cliqq) "),
        (f"class:{style_name}", text),
    ]

    if log:
        if end:
            logger.info(f"{formatted_text[0][1]}{text}{end}")
        else:
            logger.info(formatted_text[0][1] + text)

    print_formatted_text(formatted_text, style=DEFAULT_STYLE, end=end, flush=True)


def main() -> None:
    # REVIEW time for testing...

    intro = r""" 

    ··························
    :       _ _              :
    :   ___| (_) __ _  __ _  :
    :  / __| | |/ _` |/ _` | :
    : | (__| | | (_| | (_| | :
    :  \___|_|_|\__, |\__, | :
    :              |_|   |_| :
    ··························

    """

    # set up session
    api_config = ApiConfig()
    history = ChatHistory()
    command_registry = CommandRegistry()
    paths = PathManager()

    user_prompt = None
    input = ""
    template = ""

    template = load_template(paths.script_path / "templates" / "starter_template.txt")
    history.remember({"role": "system", "content": template})
    template = load_template(paths.script_path / "templates" / "reminder_template.txt")

    # check for if program was invoked with a command
    # build the parser once and reuse it in the interactive loop
    parser = parse_commands(command_registry)
    # store parser on session so help cmd can access it
    command_registry.parser = parser

    parsed_input = parse_input(sys.argv, parser)

    if parsed_input.command:
        if parsed_input.command == "/q":
            dispatch(api_config, history, command_registry, paths, parsed_input)
        elif parsed_input.command == "/invalid":
            program_output(
                "You have entered a command incorrectly. Type just '/help' to learn more.",
                style_name="error",
            )
        else:
            program_output(intro)
            program_output("Hello! I am Cliqq, the command-line AI chatbot.")
            dispatch(api_config, history, command_registry, paths, parsed_input)

        init_arg = None
    elif parsed_input.prompt:
        program_output(intro)
        program_output("Hello! I am Cliqq, the command-line AI chatbot.")

        init_arg = " ".join(parsed_input.prompt)
    else:
        program_output(intro)
        program_output(
            "Hello! I am Cliqq, the command-line AI chatbot.\nHow can I help you today?"
        )

        init_arg = None

    if init_arg:
        input = init_arg
    else:
        input = user_input().strip()

    # interactive mode below
    while input not in ("exit", "/exit"):

        tokens = shlex.split(input)

        parsed_input = parse_input(tokens, parser)

        if parsed_input.command:
            if parsed_input.command == "/invalid":
                program_output(
                    "You have entered a command incorrectly. Type just '/help' to learn more.",
                    style_name="error",
                )
                input = ""
            else:
                dispatch(api_config, history, command_registry, paths, parsed_input)
            input = ""
        else:
            # treat all words written by user as an AI prompt
            input = " ".join(parsed_input.prompt)

        # most console output is handled within functions

        if input:
            user_prompt = prep_prompt(input, template)

            actionable, response_content = ai_response(
                user_prompt, api_config, history, paths.env_path
            )

            if response_content:

                if actionable:
                    action = response_content["action"]  # json
                    # FIXME ask user if they want to run or not
                    if run(action, api_config, history, paths):
                        program_output(
                            "And your request has been completed! Do you have another question?"
                        )
                    else:
                        program_output(
                            "I'm sorry I couldn't complete your request. Do you have another one for me?"
                        )
                else:
                    # maybe have a bank of different wording for this?
                    program_output(
                        "Okay, what is your next question or request? I'm all ears!"
                    )
            else:
                program_output(
                    "I'm sorry I couldn't get an answer for you. Would you like to ask me another question?"
                )

        input = user_input().strip()

    exit_cliqq()


if __name__ == "__main__":
    main()

"""
# Make CLI runnable from source tree with
if not __package__:
    # OYTHONPATH = "src/package"
    package_source_path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, package_source_path)
"""

# NOTE further ideas:
# implement file uploads
# append to files?
