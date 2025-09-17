import os
import sys
import argparse

from ai import ai_response
from action import run_command
from main import program_output


# adding properties and get/setters for readability
# less dict accesses
class CliqqSession:
    def __init__(self):
        # "private" vars
        self._config: dict[str, str] = {}
        self._chat_history: list[dict[str, str]] = []
        self._paths: dict[str, str] = {}
        self._parser: argparse.ArgumentParser = argparse.ArgumentParser()

        self._commands: dict[str, dict] = {
            "help": {
                "description": "List Cliqq commands and what they do",
                "function": help,
                "args": None,
            },
            "exit": {
                "description": "Say goodbye to Cliqq (exit program)",
                "function": exit_cliqq,
                "args": None,
            },
            "log": {
                "description": "See chat log",
                "function": show_log,
                "args": None,
            },
            "flush": {
                "description": "Empty log file",
                "function": flush_log,
                "args": None,
            },
            "clear": {
                "description": "Clear the terminal window",
                "function": clear,
                "args": None,
            },
            "forget": {
                "description": "Reset Cliqq's memory",
                "function": clear_context,
                "args": None,
            },
            "run": {
                "description": "Run a command and have Cliqq analyze the output",
                "function": run_command,
                "args": "[command]",
            },
            "q": {
                "description": "Non-interactive mode: send a single prompt and quickly get a response",
                "function": quick_response,
                "args": "[prompt]",
            },
        }

    # config
    @property
    def commands(self) -> dict[str, dict]:
        return self._commands

    # config
    @property
    def config(self):
        return self._config

    def get_config(self, key: str) -> str:
        return self._config[key]

    def set_config(self, info):
        self._config.update(info)

    # paths
    @property
    def log_path(self):
        return self._paths.get("log_path", "~/.cliqq/log.txt")

    def env_path(self):
        return self._paths.get("env_path", "~/.cliqq/.env")

    def set_path(self, path):
        self._paths.update(path)

    # chat history
    @property
    def chat_history(self) -> list[dict[str, str]]:
        return self._chat_history

    def remember(self, msg: dict[str, str]):
        self._chat_history.append(msg)

    def forget(self):
        self._chat_history.clear()
        self._config.clear()
        self._paths.clear()

    # logging
    # TODO opening and writing to a file EVERY time very inefficient
    def log(self, text: str):
        try:
            log_dir = os.path.dirname(self.log_path)
            os.makedirs(log_dir, exist_ok=True)

            with open(self.log_path, "a") as f:
                f.write(str(text) + "\n")
        except IOError as e:
            pass


def help(session: CliqqSession):
    session._parser.print_help()


def exit_cliqq(session: CliqqSession):
    program_output("Bye! Let's talk again soon!", session)
    sys.exit(0)


def clear(session: CliqqSession):
    os.system("clear||cls")


def show_log(session: CliqqSession):
    # TODO should log the long output via appending THEN read it
    try:
        with open(session.log_path, "r") as file:
            log = file.read()
            program_output(log, session)
    except FileNotFoundError:
        program_output(
            "I couldn't find the log file, I'm sorry!", session, style_name="error"
        )
    except IOError as e:
        program_output(f"Error reading log file: {e}", session, style_name="error")


def flush_log(session: CliqqSession):
    try:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(session.log_path)
        os.makedirs(log_dir, exist_ok=True)

        with open(session.log_path, "w") as f:
            f.write("")
        program_output(
            "Chat log cleared, let's start fresh!", session, style_name="action"
        )
    except IOError as e:
        program_output(f"Error clearing log file: {e}", session, style_name="error")


def clear_context(session: CliqqSession):
    session.chat_history.clear()
    program_output(
        "Chat history cleared, I don't remember anything.", session, style_name="action"
    )
    program_output("How can I help you?", session)


def quick_response(user_prompt: str, session: CliqqSession):
    ai_response(user_prompt, session)


def dispatch(args, session: CliqqSession):
    command_info = session.commands[args.command]
    func = command_info["function"]

    if command_info.get("args") is not None:
        # Pass along the positional arg
        return func(args.arg, session)
    else:
        return func()
