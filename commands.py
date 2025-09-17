import os
import sys
import argparse
from typing import Callable, Optional, TypedDict

from ai import ai_response
from action import run_command
from main import program_output


# for typing...probably not necessary
class CommandSpec(TypedDict):
    description: str
    # Callable[[types of the args...], return type]
    # below = any callable, any args, returning anything --> most general
    function: Callable[..., object]
    args: Optional[str]  # means None or whatever is written


# adding properties and get/setters for readability
# less dict accesses
class CliqqSession:
    def __init__(self):
        # "private" vars
        self._config: dict[str, str] = {"model_name": "", "base_url": "", "api_key": ""}
        self._chat_history: list[dict[str, str]] = []
        self._paths: dict[str, str] = {}
        self._parser: argparse.ArgumentParser = argparse.ArgumentParser()
        self._log_buffer: list[str] = []
        self._log_buffer_size = 10

        self._commands: dict[str, CommandSpec] = {
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
            "wipe": {
                "description": "Empty log file",
                "function": clear_log,
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
            # TODO cliqq api [model_name] [base_url], and [api_key]
            # maybe call find_api_info with these as optional args
        }

    # config
    @property
    def commands(self) -> dict[str, CommandSpec]:
        return self._commands

    # no setter, commands are hardcoded

    # config
    # func marked @property is the getter
    @property
    def model_name(self) -> str:
        return self._config.get("model_name", "")

    # this is how you mark setters, notice prop name after @
    @model_name.setter
    def model_name(self, value: str):
        self._config["model_name"] = value

    @property
    def base_url(self) -> str:
        return self._config.get("base_url", "")

    @base_url.setter
    def base_url(self, value: str):
        self._config["base_url"] = value

    @property
    def api_key(self) -> str:
        return self._config.get("api_key", "")

    @api_key.setter
    def api_key(self, value: str):
        self._config["api_key"] = value

    # for updating everything at once for ease
    def set_config(self, config: dict[str, str]):
        self._config = config

    # paths
    @property
    def home_path(self):
        return self._paths.get("home_path", "~/.cliqq")

    @property
    def log_path(self):
        return self._paths.get("log_path", "~/.cliqq/log.txt")

    @property
    def env_path(self):
        return self._paths.get("env_path", "~/.cliqq/.env")

    @property
    def script_path(self):
        # maybe putting a func here isn't the best idea?
        return self._paths.get("script_path", os.path.dirname(__file__))

    def set_path(self, path_name: str, path: str):
        self._paths[path_name] = path

    def get_path(self, path_name: str):
        self._paths.get(path_name, self.home_path)

    # chat history
    @property
    # sole for AI's benefit, log is for user
    def chat_history(self) -> list[dict[str, str]]:
        return self._chat_history

    def remember(self, msg: dict[str, str]):
        self._chat_history.append(msg)

    def forget(self):
        self._chat_history.clear()

    # logging
    def log(self, text: str):
        self._log_buffer.append(text)
        if len(self._log_buffer) >= self._log_buffer_size:
            self.flush_log()

    def flush_log(self):
        # TODO make atomic in case program crash mid-write
        log_dir = os.path.dirname(self.log_path)
        os.makedirs(log_dir, exist_ok=True)

        if not self._log_buffer:
            return

        try:
            log_text = "".join(self._log_buffer)
            with open(self.log_path, "a") as f:
                f.write(log_text)
        except Exception as e:
            # TODO deal with this in a non-distruptive way
            pass

        self._log_buffer.clear()


def help(session: CliqqSession):
    session._parser.print_help()


def exit_cliqq(session: CliqqSession):
    session.flush_log()
    program_output("Bye! Let's talk again soon!", session)
    sys.exit(0)


def clear(session: CliqqSession):
    os.system("clear||cls")


def show_log(session: CliqqSession):
    try:
        session.flush_log()
        with open(session.log_path) as f:
            log = f.read()
            # TODO a better way to display log, especially if it's large
            program_output(log, session, style_name="action")
            program_output(
                "--------- end of log ---------", session, style_name="action"
            )
    except FileNotFoundError:
        program_output("The log is empty!", session, style_name="error")
        # create log if it doesn't exist, probably redundant but check
        f = open(session.log_path, "a")
        f.close()
    except IOError as e:
        program_output(f"Error reading log file: {e}", session, style_name="error")


def clear_log(session: CliqqSession):
    try:
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
    session.forget()
    program_output(
        "Chat history cleared. I don't remember anything? I don't remember anything!",
        session,
        style_name="action",
    )
    program_output("How can I help you?", session)


def quick_response(user_prompt: str, session: CliqqSession):
    ai_response(user_prompt, session)


def dispatch(args, session: CliqqSession):
    command_info = session.commands[args.command]
    func = command_info["function"]
    if command_info.get("args") is not None:
        # functions that take positional args
        # currently all commands only take one, alter if future commands need more
        return func(args.arg, session)
    else:
        # TODO many of these functions don't take session as arg
        return func(session)
