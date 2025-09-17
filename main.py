import os
import shlex
import sys
import re
import psutil
import argparse
from dotenv import load_dotenv
from importlib import resources

from prompt_toolkit import prompt
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText, to_plain_text
from styles import DEFAULT_STYLE
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit import choice

from prep import prep_prompt, parse_commands
from commands import dispatch, CliqqSession
from ai import ai_response, find_api_info
from action import run

BASE_DIR = os.path.dirname(__file__)  # directory containing this file


def create_paths() -> dict[str, str]:
    home_path = os.path.expanduser("~") + "/.cliqq/"
    os.makedirs(os.path.dirname(home_path), exist_ok=True)
    paths = {}

    paths["home_path"] = home_path
    paths["log_path"] = home_path + "log.txt"
    paths["script_path"] = os.path.dirname(__file__)

    return paths


# TODO: for when this is a pip-installable package
""" def load_template_pack(name: str) -> str:
    # templates is a subpackage of mypackage
    with resources.files("mypackage.templates").joinpath(name).open(
        "r", encoding="utf-8"
    ) as f:
        return f.read() """


# TODO: for while i'm testing
def load_template_local(name: str) -> str:
    path = os.path.join(BASE_DIR, "templates", name)
    with open(path, encoding="utf-8") as f:
        return f.read()


def user_input(session: CliqqSession) -> str:
    message = FormattedText(
        [
            ("class:user", ">> "),
        ]
    )
    input = prompt(
        message=message, style=DEFAULT_STYLE, auto_suggest=AutoSuggestFromHistory()
    )
    session.log(to_plain_text(message))
    return input


def program_choice(question: str, choices: list, session: CliqqSession) -> str:
    # for simple menus
    message = FormattedText([("class:prompt", "(cliqq) "), ("class:action", question)])
    session.log(message[0][1] + message[1][1])
    result = choice(
        message=message,
        options=choices,
        style=DEFAULT_STYLE,
    )
    result_text = ">> " + result
    session.log(result_text)
    return result


def program_output(text: str, session: CliqqSession, end="\n", style_name="program"):
    # replace all print with this!

    # action error program
    formatted_text = [
        ("class:name", "(cliqq) "),
        (f"class:{style_name}", text),
    ]
    session.log(formatted_text[0][1] + formatted_text[1][1])
    print_formatted_text(formatted_text, style=DEFAULT_STYLE, end=end, flush=True)


def main():

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
    session = CliqqSession()
    session.set_path(create_paths())

    user_prompt = None
    input = ""
    template = ""

    # get api details before anything
    session.set_config(find_api_info(session))

    # or "reminder_template.txt"
    template = load_template_local("starter_template.txt")

    session.remember({"role": "system", "content": template})

    # check for if program was invoked with a command
    try:
        # get from sys.argv
        parser = parse_commands(session)
        args = parser.parse_args()

        if args.command:

            # if program was called in non-interactively
            if args.command == "q":
                dispatch(args, session)
                sys.exit()

            program_output(intro, session)
            program_output("Hello! I am Cliqq, the command-line AI chatbot.", session)
            dispatch(args, session)

        else:
            program_output(intro, session)
            program_output(
                "Hello! I am Cliqq, the command-line AI chatbot.\nHow can I help you today?",
                session,
            )

    except SystemExit:
        # argparse calls sys.exit() on errors
        program_output("Hello! I am Cliqq, the command-line AI chatbot.", session)
        program_output(
            "That is not a valid command.\nYou can start talking to cliqq by typing 'cliqq'\nYou can get an immediate response to a question by typing 'cliqq q [question]'\nType 'help' for details and more options",
            session,
            style_name="error",
        )

    # input to start interactive loop
    input = user_input(session)

    # interactive mode below
    while input != "quit" or input != "q" or input != "exit":

        try:
            # check if user gave command
            args = shlex.split(input.strip())
            args = parser.parse_args(input)

            if args.command:

                # ignore cmd and just take the user's prompt
                if args.command == "q":
                    input = args.arg
                else:
                    dispatch(args, session)
                    continue

        except (SystemExit, ValueError):
            # user did not enter a command so just recognize it as a normal prompt
            pass

        # console output is handled within functions
        user_prompt = prep_prompt(input, template)
        session, actionable = ai_response(user_prompt, session)
        if actionable:
            run(actionable, session)

        input = user_input(session)

    exit()


if __name__ == "__main__":
    main()
