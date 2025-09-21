import shlex
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

    # check for if program was invoked with a command
    # build the parser once and reuse it in the interactive loop
    parser = parse_commands(command_registry)
    # store parser on session so help cmd can access it
    command_registry.parser = parser
    try:
        # get from sys.argv
        args = parser.parse_args()

        if args.command:
            if args.command != "q":
                program_output(intro)
            program_output("Hello! I am Cliqq, the command-line AI chatbot.")
            dispatch(api_config, history, command_registry, paths, args)

        else:
            program_output(intro)
            program_output(
                "Hello! I am Cliqq, the command-line AI chatbot.\nHow can I help you today?",
            )

    except SystemExit:
        # argparse calls sys.exit() on errors
        # if user only calls cliqq w 1 word (ex. cliqq hi) it'll assume it's a subcommand and raise an error since it's not registered
        program_output("Hello! I am Cliqq, the command-line AI chatbot.")

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
            input = args.arg

        # most console output is handled within functions

        user_prompt = prep_prompt(input, template)

        response_content = ai_response(user_prompt, api_config, history, paths)

        if response_content:
            if response_content["actionable"]:
                actionable = response_content.get("content")
                if run(actionable, api_config, history, paths):
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

        input = user_input()

    exit_cliqq()


if __name__ == "__main__":
    main()

# NOTE further ideas:
# implement file uploads
# append to files?
