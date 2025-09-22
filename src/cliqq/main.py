import shlex
import logging
import sys
import argparse
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


def handle_init_args(
    intro: str,
    parser: argparse.ArgumentParser,
    api_config: ApiConfig,
    history: ChatHistory,
    command_registry: CommandRegistry,
    paths: PathManager,
) -> str | None:

    tokens = sys.argv[1:]
    if tokens and tokens[0] == "cliqq":
        tokens = tokens[1:]

    args = parse_input(tokens, parser)

    if args.command:
        if args.command == "/q":
            dispatch(api_config, history, command_registry, paths, args)
            return None
        program_output(intro)
        program_output("Hello! I am Cliqq, the command-line AI chatbot.")
        dispatch(api_config, history, command_registry, paths, args)
        return None
    elif args.prompt:
        program_output(intro)
        program_output("Hello! I am Cliqq, the command-line AI chatbot.")
        return " ".join(args.prompt)
    else:
        program_output(intro)
        program_output(
            "Hello! I am Cliqq, the command-line AI chatbot.\nHow can I help you today?"
        )
        return None


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

    # check for if program was invoked with a command
    # build the parser once and reuse it in the interactive loop
    parser = parse_commands(command_registry)
    # store parser on session so help cmd can access it
    command_registry.parser = parser

    init_arg = handle_init_args(
        intro, parser, api_config, history, command_registry, paths
    )

    if init_arg:
        input = init_arg
    else:
        input = user_input().strip()

    # interactive mode below
    while input != "exit":

        # check if user gave command
        tokens = shlex.split(input)

        # removing cliqq b/c argparse will interpret it as a command (prog)
        if tokens and tokens[0] == "cliqq":
            tokens = tokens[1:]

        args = parse_input(tokens, parser)

        if args.command:
            dispatch(api_config, history, command_registry, paths, args)
            input = ""
        else:
            # treat all args as an AI prompt
            input = " ".join(args.prompt)

        # most console output is handled within functions

        if input:
            user_prompt = prep_prompt(input, template)

            response_content = ai_response(user_prompt, api_config, history, paths)

            if response_content:
                if response_content["actionable"]:
                    actionable = response_content["content"]
                    if run(actionable, api_config, history, paths):  # type: ignore
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

# NOTE further ideas:
# implement file uploads
# append to files?
