import os
import sys
from dotenv import load_dotenv

from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from styles import DEFAULT_STYLE
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit import choice
from openai import (
    OpenAI,
    APIError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)

from prep import prep_prompt
from ai import ai_response
from action import run

session = PromptSession()
model_name = ""
base_url = ""
api_key = ""


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
    # tasks: change things on computer via commands + run, have ai create things, send files to ask questions

    # additional: log chat history, print or save to file
    # additional: help command + info at first prompt
    ai_output = None
    response = None
    user_prompt = None
    input = None
    chat_history = None

    program_output("Hello! I am Cliqq, the command-line AI chatbot.")

    # method to check for api details, as if you don't get them

    program_output("How can I help you today?")

    # get from starter_template
    with open("/templates/starter_template.txt") as file:
        template = file.read()

    chat_history = (
        [
            {"role": "system", "content": template},
        ],
    )

    input = user_input()

    while input != "quit" or input != "q" or input != "exit":
        # console output is handled within functions
        user_prompt = prep_prompt(input)
        chat_history, actionable = ai_response(
            api_key, base_url, model_name, user_prompt, chat_history
        )
        if actionable:
            run(actionable)
        input = user_input()

    exit()
