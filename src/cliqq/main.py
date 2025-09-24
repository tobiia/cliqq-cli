# cd cliqq-cli
# pip install -e .
# don't forget the . !!

# cd src
# python -m cliqq
# for local

import shlex
import sys
from pathlib import Path
import json

from cliqq.log import logger
from cliqq.io import program_choice, program_output, user_input
from cliqq.models import ApiConfig, ChatHistory, CommandRegistry, PathManager
from cliqq.prep import (
    parse_action,
    prep_prompt,
    parse_commands,
    parse_input,
    load_template,
)
from cliqq.commands import dispatch, exit_cliqq, register_commands
from cliqq.ai import ai_response
from cliqq.action import run


def main() -> None:

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
    registry = CommandRegistry()
    register_commands(registry)
    paths = PathManager()

    user_prompt = None
    input = ""
    template = ""

    # FIXME probably should save the templates...make sure to change all when i do
    template = load_template(paths.script_path / "templates" / "starter_template.txt")
    history.remember({"role": "system", "content": template})
    template = load_template(paths.script_path / "templates" / "reminder_template.txt")

    # check for if program was invoked with a command
    # build the parser once and reuse it in the interactive loop
    parser = parse_commands(registry)
    # store parser on session so help cmd can access it
    registry.parser = parser

    parsed_input = parse_input(sys.argv, parser)

    if parsed_input.command:
        if parsed_input.command == "/q":
            dispatch(parsed_input, api_config, history, registry, paths)
        elif parsed_input.command == "/invalid":
            program_output(
                "You have entered a command incorrectly. Type just '/help' to learn more.",
                style_name="error",
            )
        else:
            program_output(intro)
            program_output("Hello! I am Cliqq, the command-line AI chatbot.")
            dispatch(parsed_input, api_config, history, registry, paths)

        init_arg = None
    elif parsed_input.prompt:
        program_output(intro)
        program_output("Hello! I am Cliqq, the command-line AI chatbot.")

        init_arg = " ".join(parsed_input.prompt)
    else:
        program_output(intro)
        program_output(
            "Hello! I am Cliqq, the command-line AI chatbot.\nHow can I help you today?"
        )

        init_arg = None

    if init_arg:
        input = init_arg
    else:
        input = user_input().strip()

    # interactive mode below
    while input not in ("exit", "/exit"):

        tokens = shlex.split(input)

        parsed_input = parse_input(tokens, parser)

        if parsed_input.command:
            # FIXME i think this tries to get flags even if they're ok...
            if parsed_input.command == "/invalid":
                program_output(
                    "You have entered a command incorrectly. Type just '/help' to learn more.",
                    style_name="error",
                )
                input = ""
            else:
                dispatch(parsed_input, api_config, history, registry, paths)
            input = ""
        else:
            # treat all words written by user as an AI prompt
            input = " ".join(parsed_input.prompt)

        # most console output is handled within functions

        if input:
            user_prompt = prep_prompt(input, template)

            action_str, response = ai_response(
                user_prompt, paths.env_path, api_config, history
            )
            print("\n")

            if response:

                if action_str:

                    action = parse_action(action_str)

                    if action:

                        action_type = action.get("type")

                        if action_type == "command":
                            cmd = action.get("command")
                            program_output(cmd, end="", style_name="action")
                        elif action_type == "file":
                            file_path = action.get("path")
                            program_output(
                                f"Saved file: {file_path}", end="", style_name="action"
                            )
                        else:
                            # rejection handled by action module
                            program_output(
                                f"Action: {action_type}", end="", style_name="action"
                            )
                    else:
                        # json error
                        program_output(
                            "Sorry, I got confused and can't complete your request!\nDo you have another one for me?",
                            style_name="error",
                        )
                        continue

                    choices = [
                        ("yes", "Yes"),
                        ("no", "No"),
                    ]
                    user_choice = program_choice(
                        "Would you like me to carry this out?",
                        choices,
                    )
                    if user_choice == "yes" and run(action, api_config, history, paths):
                        program_output(
                            "And your request has been completed! Do you have another question?"
                        )
                    else:
                        program_output(
                            "Sorry I couldn't complete your request. Do you have another one for me?"
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


def safe_main():
    try:
        main()
    except Exception as e:
        logger.exception("Fatal error in Cliqq startup or main loop: %s", e)
        program_output(
            "Cliqq encountered a fatal error and needs to exit.\nPlease check the logs for details.",
            style_name="error",
        )
        sys.exit(1)


if __name__ == "__main__":
    safe_main()

"""
# Make CLI runnable from source tree with
if not __package__:
    # OYTHONPATH = "src/package"
    package_source_path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, package_source_path)
"""

# NOTE further ideas:
# implement file uploads
# append to files?
