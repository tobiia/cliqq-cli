import os
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from styles import DEFAULT_STYLE
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from prep import prep_prompt

session = PromptSession()


def user_input():
    message = [
        ("class:user", ">> "),
    ]
    input = session.prompt(
        message, style=DEFAULT_STYLE, auto_suggest=AutoSuggestFromHistory()
    )
    return input


def program_output(text, end="\n", action=False):
    # replace all print with this!
    if action:
        formatted_text = FormattedText(
            [
                ("class:name", "(cliqq)"),
                ("class:action", text),
            ]
        )
    else:
        formatted_text = FormattedText(
            [
                ("class:name", "(cliqq)"),
                ("class:program", text),
            ]
        )
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
    chat_history = (
        [
            {"role": "system", "content": "You are a helpful command-line assistant"},
        ],
    )

    input = user_input()

    while input != "quit" or input != "q" or input != "exit":
        user_prompt = prep_prompt(input)
        ai_output = prompt_ai(key, base_url, model, user_prompt, chat_history)
        response = parse_output(ai_output)
        program_output(response)
        input = user_input()
    exit()
