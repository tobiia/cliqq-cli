import argparse
import os
import sys
import logging
import inspect
from typing import NoReturn

from cliqq.log import logger
from cliqq.io import program_output
from cliqq.action import run_command
from cliqq.models import (
    Command,
    ApiConfig,
    ChatHistory,
    CommandRegistry,
    PathManager,
)


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
        with open(paths.log_path, encoding="utf-8") as f:
            log = f.read()
            # TODO a better way to display log, especially if it's large
            program_output(log, style_name="action")
            program_output("--------- end of log ---------", style_name="action")
    except FileNotFoundError:
        program_output("The log is empty!", style_name="error")
        # create log if it doesn't exist, probably redundant but check
        f = open(paths.log_path, "a", encoding="utf-8")
        f.close()
    except IOError as e:
        program_output(f"Error reading log file: {e}", style_name="error")
        raise IOError(f"IOError, error reading log file: {e}")


def clear_log(paths: PathManager) -> None:
    try:
        with open(paths.log_path, "w", encoding="utf-8") as f:
            f.write("")
        program_output("Chat log cleared, let's start fresh!", style_name="action")
    except IOError as e:
        program_output(f"Error clearing log file: {e}", style_name="error")
        raise IOError(f"IOError, error reading log file: {e}")


def clear_context(history: ChatHistory) -> None:
    history.forget()
    program_output(
        "Chat history cleared. I don't remember anything? I don't remember anything!",
        style_name="action",
    )
    program_output("How can I help you?")


def quick_response(
    args, api_config: ApiConfig, history: ChatHistory, paths: PathManager
) -> None:
    from cliqq.ai import ai_response

    # FIXME args might be a list...
    ai_response(args, paths.env_path, api_config, history)
    exit_cliqq()


def dispatch(
    user_input: argparse.Namespace,  # namespace
    api_config: ApiConfig,
    history: ChatHistory,
    registry: CommandRegistry,
    paths: PathManager,
):
    command = registry.commands[user_input.command]

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

    # if this Command takes positional arguments
    if command.args:
        # currently all commands only take one, alter if future commands need more
        kwargs["args"] = user_input.args

    func(**kwargs)


def register_commands(registry: CommandRegistry) -> None:
    registry.register_command(
        "/help",
        Command(
            name="/help",
            description="List Cliqq commands and what they do",
            function=help,
        ),
    )
    registry.register_command(
        "/exit",
        Command(
            name="/exit",
            description="Say goodbye to Cliqq (exit program)",
            function=exit_cliqq,
        ),
    )
    registry.register_command(
        "/log",
        Command(
            name="/log",
            description="See chat log",
            function=show_log,
        ),
    )
    registry.register_command(
        "/wipe",
        Command(
            name="/wipe",
            description="Empty log file",
            function=clear_log,
        ),
    )
    registry.register_command(
        "/clear",
        Command(
            name="/clear",
            description="Clear the terminal window",
            function=clear,
        ),
    )
    registry.register_command(
        "/forget",
        Command(
            name="/forget",
            description="Reset Cliqq's memory",
            function=clear_context,
        ),
    )
    registry.register_command(
        "/run",
        Command(
            name="/run",
            description="Run a command and have Cliqq analyze the output",
            function=run_command,
            args="[command]",
        ),
    )
    registry.register_command(
        "/q",
        Command(
            name="/q",
            description="Non-interactive mode: send a single prompt and quickly get a response",
            function=quick_response,
            args="[prompt]",
        ),
    )
