import os
import sys
import re
import psutil
import argparse
from dotenv import load_dotenv

from prompt_toolkit import prompt
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from styles import DEFAULT_STYLE
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit import choice

from prep import prep_prompt, parse_commands
from commands import dispatch, CliqqSession
from ai import ai_response, find_api_info
from action import run

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


def log(text, session):
    with open(session.paths["log_path"], "a") as file:
        file.write(text)


def create_paths():
    # TODO: in main or in class cliqq
    home_path = os.path.expanduser("~") + "/.cliqq/"
    os.makedirs(os.path.dirname(home_path), exist_ok=True)
    paths = {}
    paths["home_path"] = home_path
    paths["log_path"] = home_path + "log.txt"
    paths["script_path"] = os.path.dirname(__file__)
    return paths


def user_input():
    message = FormattedText(
        [
            ("class:user", ">> "),
        ]
    )
    input = prompt(
        message=message, style=DEFAULT_STYLE, auto_suggest=AutoSuggestFromHistory()
    )
    return input


def program_choice(question, choices: list):
    # for simple menus
    message = [("class:prompt", "(cliqq) "), ("class:action", question)]
    result = choice(
        message=message,
        options=choices,
        style=DEFAULT_STYLE,
    )
    return result


def program_output(text, end="\n", style_name="program"):
    # replace all print with this!

    # action error program
    formatted_text = [
        ("class:name", "(cliqq)"),
        (f"class:{style_name}", text),
    ]
    print_formatted_text(formatted_text, style=DEFAULT_STYLE, end=end, flush=True)


def main():
    # set up session
    session = CliqqSession()
    # need function for non-interactive
    user_prompt = None
    input = ""
    template_path = "/templates/reminder_template.txt"
    starter_template = "/templates/starter_template.txt"

    # get api details before anything
    session.config = find_api_info()

    # get starter_template
    with open(starter_template) as file:
        template = file.read()

    session.chat_history.append({"role": "system", "content": template})

    # check for if program was invoked with a command
    try:
        # get from sys.argv
        args = parse_commands(session)

        if args.command:

            # if program was called in non-interactively
            if args.command == "q":
                dispatch(args, session)
                exit(0)

            program_output(intro)
            program_output("Hello! I am Cliqq, the command-line AI chatbot.")
            dispatch(args, session)

        else:
            program_output(intro)
            program_output(
                "Hello! I am Cliqq, the command-line AI chatbot.\nHow can I help you today?"
            )

    except SystemExit:
        # argparse calls sys.exit() on errors
        program_output(
            "That is not a valid command. Type 'help' for options", style_name="error"
        )

    # input to start interactive loop
    input = user_input()

    # interactive mode below
    while input != "quit" or input != "q" or input != "exit":

        try:
            # check if user gave command
            args = parse_commands(session)

            if args.command:

                # ignore cmd and just take the user's prompt
                if args.command == "q":
                    input = args.arg
                else:
                    dispatch(args, session)
                    continue

        except SystemExit:
            # just in case
            program_output(
                "That is not a valid command. You can type 'help' for options or ask me another question",
                style_name="error",
            )
            continue

        # console output is handled within functions
        user_prompt = prep_prompt(input, template_path)
        session, actionable = ai_response(user_prompt, session)
        if actionable:
            run(actionable, session)

        input = user_input()

    exit()


if __name__ == "__main__":
    main()
