import os
import shlex
import sys
import logging
from pathlib import Path

from prompt_toolkit import prompt
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText, to_plain_text
from styles import DEFAULT_STYLE
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit import choice

from classes import ApiConfig, ChatHistory, CommandRegistry, PathManager
from prep import prep_prompt, parse_commands
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
def load_template_local(file_name: str, script_path: Path) -> str:
    path = script_path.joinpath("templates", file_name)
    with open(path, encoding="utf-8") as f:
        return f.read()


def user_input(sensitive: bool = False) -> str:
    message = FormattedText(
        [
            ("class:user", ">> "),
        ]
    )
    input = prompt(
        message=message, style=DEFAULT_STYLE, auto_suggest=AutoSuggestFromHistory()
    )
    if not sensitive:
        logger.info(f"{to_plain_text(message)}{input}\n")
    return input


def program_choice(question: str, choices: list, sensitive: bool = False) -> str:
    # for simple menus
    message = FormattedText([("class:prompt", "(cliqq) "), ("class:action", question)])
    result = choice(
        message=message,
        options=choices,
        style=DEFAULT_STYLE,
    )
    if not sensitive:
        logger.info(f"{to_plain_text(message[0][1])}{question}\n")
        logger.info(f">> {result}\n")
    return result


def program_output(
    text: str,
    end: str = "\n",
    style_name: str = "program",
    sensitive: bool = False,
):
    # action error program
    formatted_text = [
        ("class:name", "(cliqq) "),
        (f"class:{style_name}", text),
    ]

    logger = logging.getLogger("cliqq")
    if not sensitive:
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
    paths.create_paths()

    user_prompt = None
    input = ""
    template = ""

    # or "reminder_template.txt"
    template = load_template_local("starter_template.txt", paths.script_path)

    history.remember({"role": "system", "content": template})

    # better to defer API validation until first op that requires it
    # so the user can run simple commands w/o setting up API info

    # check for if program was invoked with a command
    # build the parser once and reuse it in the interactive loop
    parser = parse_commands(command_registry)
    # store parser on session so help cmd can access it
    command_registry.parser = parser
    try:
        # get from sys.argv
        args = parser.parse_args()

        if args.command:

            # if program was called in non-interactively
            if args.command == "q":
                dispatch(api_config, history, command_registry, paths, args)
                sys.exit()

            program_output(intro)
            program_output("Hello! I am Cliqq, the command-line AI chatbot.")
            dispatch(api_config, history, command_registry, paths, args)

        else:
            program_output(intro)
            program_output(
                "Hello! I am Cliqq, the command-line AI chatbot.\nHow can I help you today?",
            )
    # FIXME check that this is right
    except SystemExit:
        # argparse calls sys.exit() on errors
        program_output("Hello! I am Cliqq, the command-line AI chatbot.")
        program_output(
            "That is not a valid command.\nYou can start talking to cliqq by typing 'cliqq'\nYou can get an immediate response to a question by typing 'cliqq q [question]'\nType 'help' for details and more options",
            style_name="error",
        )

    # input to start interactive loop
    input = user_input()

    # interactive mode below
    while input != "exit":

        try:
            # check if user gave command
            args = shlex.split(input.strip())
            args = parser.parse_args(args)

            if args.command:

                # ignore cmd and just take the user's prompt
                if args.command == "q":
                    input = args.arg
                else:
                    dispatch(api_config, history, command_registry, paths, args)
                    continue

        except (SystemExit, ValueError):
            # FIXME user did not enter a command so just recognize it as a normal prompt
            input = args.arg

        # console output is handled within functions
        user_prompt = prep_prompt(input, template)
        session, actionable = ai_response(user_prompt, api_config, history, paths)
        if actionable:
            run(actionable, api_config, history, paths)

        input = user_input()

    exit_cliqq()


if __name__ == "__main__":
    main()

# NOTE further ideas:
# implement file uploads
# append to files?
