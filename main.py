import os
import sys
import argparse
from dotenv import load_dotenv

from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from styles import DEFAULT_STYLE
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit import choice

from prep import prep_prompt
from ai import ai_response, find_api_info
from action import run

intro = r""" 

╔───────────────────────────────────────────────────╗
│                                                   │
│      █████████  ████   ███                        │
│     ███░░░░░███░░███  ░░░                         │
│    ███     ░░░  ░███  ████   ████████  ████████   │
│   ░███          ░███ ░░███  ███░░███  ███░░███    │
│   ░███          ░███  ░███ ░███ ░███ ░███ ░███    │
│   ░░███     ███ ░███  ░███ ░███ ░███ ░███ ░███    │
│    ░░█████████  █████ █████░░███████ ░░███████    │
│     ░░░░░░░░░  ░░░░░ ░░░░░  ░░░░░███  ░░░░░███    │
│                                 ░███      ░███    │
│                                 █████     █████   │
│                                ░░░░░     ░░░░░    │
│                                                   │
╚───────────────────────────────────────────────────╝

 """

# TODO might need to be global
session = PromptSession()

commands = {
    "help": {"description": "list cliqq commands and what they do", "function": help},
    "log": {"description": "See chat log", "function": show_log},
    "clear": {"description": "Clear the terminal window", "function": clear},
    "run": {
        "description": "Run a command and have Cliqq analyze the output",
        "function": run_command,
    },
    "reset": {
        "description": "Reset Cliqq conversation history",
        "function": clear_history,
    },
}


def user_input():
    message = [
        ("class:user", ">> "),
    ]
    input = session.prompt(
        message=message, style=DEFAULT_STYLE, auto_suggest=AutoSuggestFromHistory()
    )
    return input


def program_choice(question, choices=[]):
    # for simple menus
    message = [("class:prompt", "(cliqq) "), ("class:action", question)]
    """
    options = [
        ("pizza", "Pizza with mushrooms"),
        ("pizza", "Pizza with mushrooms"),
        ("pizza", "Pizza with mushrooms"),
    ]
    """
    result = choice(
        message=message,
        options=choices,
        style=DEFAULT_STYLE,
    )
    return result


def program_output(text, end="\n", action=False):
    # replace all print with this!
    if action:
        formatted_text = [
            ("class:name", "(cliqq)"),
            ("class:action", text),
        ]
    else:
        formatted_text = [
            ("class:name", "(cliqq)"),
            ("class:program", text),
        ]
    print_formatted_text(formatted_text, style=DEFAULT_STYLE, end=end, flush=True)


def main():
    #
    # additional: log chat history, print or save to file
    # additional: help command + info at first prompt
    model_name = ""
    base_url = ""
    api_key = ""
    user_prompt = None
    input = ""
    chat_history = None
    api_config = None
    template_path = "/templates/reminder_template.txt"
    starter_template = "/templates/starter_template.txt"

    program_output(intro)

    program_output("Hello! I am Cliqq, the command-line AI chatbot.")

    # method to check for api details, as if you don't get them
    api_config = find_api_info()

    # check for commands

    program_output("How can I help you today?")

    # get starter_template
    with open(starter_template) as file:
        template = file.read()

    chat_history = (
        [
            {"role": "system", "content": template},
        ],
    )

    input = user_input()

    while input != "quit" or input != "q" or input != "exit":

        # console output is handled within functions
        user_prompt = prep_prompt(input, template_path)
        chat_history, actionable = ai_response(api_config, user_prompt, chat_history)
        if actionable:
            run(actionable)
        input = user_input()

    exit()
