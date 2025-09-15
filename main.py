import os
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

session = PromptSession()
style = Style.from_dict(
    {
        # User input (default text).
        "": "#ff0066",
        # Prompt.
        "user": "#884444",
        "name": "#00aa00",
        "program": "#00aa00",
    }
)


def user_input():
    message = [
        ("class:user", ">> "),
    ]
    input = session.prompt(message, style=style, auto_suggest=AutoSuggestFromHistory())
    return input


def program_output(text):
    # replace all print with this!
    formatted_text = FormattedText(
        [
            ("class:name", "(cliqq)"),
            ("class:program", text),
        ]
    )
    print_formatted_text(formatted_text, style=style)


def main():
    # tasks: change things on computer via commands + run, have ai create things, send files to ask questions
    ai_output = None
    response = None
    user_prompt = None
    input = None

    print("hello! i am cliqq, the command-line ai chatbot. how can i help you?")
    input = user_input()

    while input != "quit" or input != "q" or input != "exit":
        user_prompt = parse_input(input)
        ai_output = prompt_ai(user_prompt)
        response = parse_output(ai_output)
        program_output(response)
        input = user_input()
    exit()
