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
from commands import dispatch, CliqqSession, exit_cliqq
from ai import ai_response
from action import run


def create_paths(session: CliqqSession):
    home_path = os.path.join(os.path.expanduser("~"), ".cliqq")
    # NOTE don't need to do this in every func b/c this func is always called
    os.makedirs(os.path.dirname(home_path), exist_ok=True)

    session.set_path("home_path", home_path)

    log_path = os.path.join(home_path, "log.txt")
    session.set_path("log_path", log_path)

    env_path = os.path.join(home_path, ".env")
    session.set_path("env_path", env_path)

    session.set_path("script_path", os.path.dirname(__file__))


# NOTE: for when this is a pip-installable package
""" def load_template_pack(name: str) -> str:
    # templates is a subpackage of mypackage
    with resources.files("mypackage.templates").joinpath(name).open(
        "r", encoding="utf-8"
    ) as f:
        return f.read() """


# NOTE: for while i'm testing
def load_template_local(name: str, session: CliqqSession) -> str:
    path = os.path.join(session.script_path, "templates", name)
    with open(path, encoding="utf-8") as f:
        return f.read()


def user_input(session: CliqqSession, sensitive=False) -> str:
    message = FormattedText(
        [
            ("class:user", ">> "),
        ]
    )
    input = prompt(
        message=message, style=DEFAULT_STYLE, auto_suggest=AutoSuggestFromHistory()
    )
    if not sensitive:
        session.log(f"{to_plain_text(message)}{input}\n")
    return input


def program_choice(
    question: str, choices: list, session: CliqqSession, sensitive=False
) -> str:
    # for simple menus
    message = FormattedText([("class:prompt", "(cliqq) "), ("class:action", question)])
    result = choice(
        message=message,
        options=choices,
        style=DEFAULT_STYLE,
    )
    if not sensitive:
        session.log(f"{to_plain_text(message[0][1])}{question}\n")
        session.log(f">> {result}\n")
    return result


def program_output(
    text: str, session: CliqqSession, end="\n", style_name="program", sensitive=False
):
    # action error program
    formatted_text = [
        ("class:name", "(cliqq) "),
        (f"class:{style_name}", text),
    ]

    if not sensitive:
        if end:
            session.log(f"{formatted_text[0][1]}{text}{end}")
        else:
            session.log(formatted_text[0][1] + text)

    print_formatted_text(formatted_text, style=DEFAULT_STYLE, end=end, flush=True)


def main():
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
    session = CliqqSession()
    create_paths(session)

    user_prompt = None
    input = ""
    template = ""

    # or "reminder_template.txt"
    template = load_template_local("starter_template.txt", session)

    session.remember({"role": "system", "content": template})

    # better to defer API validation until first op that requires it
    # so the user can run simple commands w/o setting up API info

    # check for if program was invoked with a command
    # build the parser once and reuse it in the interactive loop
    parser = parse_commands(session)
    # store parser on session so help cmd can access it
    session._parser = parser
    try:
        # get from sys.argv
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
            args = parser.parse_args(args)

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

# NOTE further ideas:
# implement file uploads
# append to files?
