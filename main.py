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

from prep import prep_prompt, parse_args
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


def user_input():
    message = [
        ("class:user", ">> "),
    ]
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


# easier to pass around globals?
class CliqqSession:
    def __init__(self):
        self.config = {}
        self.chat_history = []


def main():
    # set up session
    session = CliqqSession()
    # need function for non-interactive
    user_prompt = None
    input = ""
    # TODO: send reminder occasionally with ai_prompt
    template_path = "/templates/reminder_template.txt"
    starter_template = "/templates/starter_template.txt"

    # get api details before anything
    session.config = find_api_info(session)

    # get starter_template
    with open(starter_template) as file:
        template = file.read()

    session.chat_history.append({"role": "system", "content": template})

    # TODO: check args/commands
    args = parse_args()  # uses sys.argv by default

    if args.command is not None:
        # --- Non-interactive mode (subcommand given) ---
        result = dispatch(args, session)  # pass session into functions that need it
        return result

        # if non-interactive, goes here
        # program logic
        exit()

    # interactive mode below

    program_output(intro)

    program_output("Hello! I am Cliqq, the command-line AI chatbot.")

    # if command, handle

    # else

    program_output("How can I help you today?")

    input = user_input()

    while input != "quit" or input != "q" or input != "exit":

        # console output is handled within functions
        user_prompt = prep_prompt(input, template_path)
        session, actionable = ai_response(user_prompt, session)
        if actionable:
            run(actionable, session)
        input = user_input()

    exit()


if __name__ == "__main__":
    main()
