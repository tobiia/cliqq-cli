from os import system
import sys

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

        self._commands = {
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
        return self._chat_history  # return copy if you want immutability

    def remember(self, msg: dict[str, str]):
        # TODO make sure printing works ok with the Formatted text and stuff
        self._chat_history.append(msg)

    def forget(self):
        self._chat_history.clear()
        self._config.clear()
        self._paths.clear()

    # logging
    # TODO what if file doesn't exist?
    def log(self, text: str):
        with open(self.log_path, "a") as f:
            f.write(str(text) + "\n")


def help(session):
    session.parser.print_help()


def exit_cliqq(session):
    sys.exit(0)


def clear(session):
    system("clear||cls")


def show_log(session):
    # TODO fix lol
    with open(session.paths["log_path"]) as file:
        log = file.read()
        program_output(log, session)


def flush_log(session):
    with open(session.paths["log_path"], "w") as f:
        pass


def clear_context(session):
    # TODO output indicating these were done!
    session.chat_history.clear()


def quick_response(user_prompt, session):
    ai_response(user_prompt, session)


def dispatch(args, session):
    command_info = session.commands[args.command]
    func = command_info["function"]

    if command_info.get("args") is not None:
        # Pass along the positional arg
        return func(args.arg, session)
    else:
        return func()
