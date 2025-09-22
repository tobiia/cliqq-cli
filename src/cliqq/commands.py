import os
import sys
import logging
import inspect
from typing import Callable, NoReturn, Optional, Any
from dataclasses import dataclass

from classes import ApiConfig, ChatHistory, CommandRegistry, PathManager
from ai import ai_response
from main import program_output
from action import run_command
from log import logger


@dataclass(frozen=True)
class Command:
    name: str
    description: str
    function: Callable[..., Any]
    args: Optional[str] = None


def help(command_registry: CommandRegistry) -> None:
    command_registry.parser.print_help()


def exit_cliqq() -> NoReturn:
    logging.shutdown()
    program_output("Bye! Let's talk again soon!")
    sys.exit(0)


def clear() -> None:
    os.system("clear||cls")


def show_log(paths: PathManager) -> None:
    try:
        for handler in logger.handlers:
            handler.flush()
        with open(paths.log_path) as f:
            log = f.read()
            # TODO a better way to display log, especially if it's large
            program_output(log, style_name="action")
            program_output("--------- end of log ---------", style_name="action")
    except FileNotFoundError:
        program_output("The log is empty!", style_name="error")
        # create log if it doesn't exist, probably redundant but check
        f = open(paths.log_path, "a")
        f.close()
    except IOError as e:
        logger.exception("IOError: %s", e)
        program_output(f"Error reading log file: {e}", style_name="error")


# TODO go through return None funcs to see if they should return something...
def clear_log(paths: PathManager) -> None:
    try:
        with open(paths.log_path, "w") as f:
            f.write("")
        program_output("Chat log cleared, let's start fresh!", style_name="action")
    except IOError as e:
        logger.exception("IOError: %s", e)
        program_output(f"Error clearing log file: {e}", style_name="error")


def clear_context(history: ChatHistory) -> None:
    history.forget()
    program_output(
        "Chat history cleared. I don't remember anything? I don't remember anything!",
        style_name="action",
    )
    program_output("How can I help you?")


def quick_response(
    user_prompt: str, api_config: ApiConfig, history: ChatHistory, paths: PathManager
) -> None:

    ai_response(user_prompt, api_config, history, paths)
    exit_cliqq()


def dispatch(
    api_config: ApiConfig,
    history: ChatHistory,
    registry: CommandRegistry,
    paths: PathManager,
    args,  # probably a namespace?
):
    command = registry.commands[args.command]

    func = command.function

    sig = inspect.signature(func)
    kwargs = {}

    if "api_config" in sig.parameters:
        kwargs["api_config"] = api_config
    if "history" in sig.parameters:
        kwargs["history"] = history
    if "registry" in sig.parameters:
        kwargs["registry"] = registry
    if "paths" in sig.parameters:
        kwargs["paths"] = paths

    if command.args:
        # functions that take positional args
        # currently all commands only take one, alter if future commands need more
        kwargs["args"] = args.arg

    func(**kwargs)


DEFAULT_COMMANDS: list[Command] = [
    # TODO cliqq api [model_name] [base_url], and [api_key]
    # maybe call find_api_info with these as optional args
    Command(
        name="/help",
        description="List Cliqq commands and what they do",
        function=help,
    ),
    Command(
        name="/exit",
        description="Say goodbye to Cliqq (exit program)",
        function=exit_cliqq,
    ),
    Command(
        name="/log",
        description="See chat log",
        function=show_log,
    ),
    Command(
        name="/wipe",
        description="Empty log file",
        function=clear_log,
    ),
    Command(
        name="/clear",
        description="Clear the terminal window",
        function=clear,
    ),
    Command(
        name="/forget",
        description="Reset Cliqq's memory",
        function=clear_context,
    ),
    Command(
        name="/run",
        description="Run a command and have Cliqq analyze the output",
        function=run_command,
        args="[command]",
    ),
    Command(
        name="/q",
        description="Non-interactive mode: send a single prompt and quickly get a response",
        function=quick_response,
        args="[prompt]",
    ),
]
