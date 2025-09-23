import argparse
import json
from pathlib import Path
from typing import Callable, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from cliqq.commands import (
        exit_cliqq,
        show_log,
        clear_log,
        clear,
        clear_context,
        clear_context,
        quick_response,
    )


# should maybe use dependency injection (FastAPI) or contextvars (Flask)...


@dataclass(frozen=True)
class Command:
    name: str
    description: str
    function: Callable[..., Any]
    args: Optional[str] = None


class ApiConfig:
    def __init__(self):
        self._model_name: str = ""
        self._base_url: str = ""
        self._api_key: str = ""

    # func marked @property is the getter
    # properties good for validation + changing attrib access w/o changing public API
    @property
    def model_name(self) -> str:
        return self._model_name

    # this is how you mark setters, notice prop name after @
    @model_name.setter
    def model_name(self, name: str):
        self._model_name = name

    @property
    def base_url(self) -> str:
        return self._base_url

    @base_url.setter
    def base_url(self, url: str):
        self._base_url = url

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, key: str):
        self._api_key = key

    # for updating everything at once for ease
    def set_config(self, config: dict[str, str]):
        self._model_name = config["model_name"]
        self._base_url = config["base_url"]
        self._api_key = config["api_key"]


class ChatHistory:
    def __init__(self):
        self._chat_history: list[dict[str, str]] = []

    @property
    # sole for AI's benefit, log is for user
    def chat_history(self) -> list[dict[str, str]]:
        return self._chat_history

    def remember(self, msg: dict[str, str]):
        self._chat_history.append(msg)

    def forget(self):
        self._chat_history.clear()


class CommandRegistry:
    def __init__(self):
        self._parser: argparse.ArgumentParser = argparse.ArgumentParser()
        self.commands: dict[str, Command] = {cmd.name: cmd for cmd in DEFAULT_COMMANDS}

    def get_command(self, command_name: str) -> Command | None:
        return self.commands.get(command_name)

    def add_command(self, key: str, command: Command) -> None:
        self.commands[key] = command

    @property
    def parser(self) -> argparse.ArgumentParser:
        return self._parser

    @parser.setter
    def parser(self, argument_parser: argparse.ArgumentParser) -> None:
        self._parser = argument_parser


class PathManager:
    def __init__(self):
        config_path = Path("~/.cliqq/config.json").expanduser()
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}

        self._script_path = Path(__file__).parent

        home = Path(config.get("home", "~/.cliqq")).expanduser()
        self._home_path = home

        # Path contruct again just in case, probs not necessary
        self._debug_path = Path(config.get("debug", home / "debug.log")).expanduser()

        self._log_path = Path(config.get("log", home / "cliqq.log")).expanduser()

        self._env_path = Path(config.get("env", home / ".env")).expanduser()

        self.create_paths()

    # func marked @property is the getter
    @property
    def script_path(self) -> Path:
        return self._script_path

    @property
    def home_path(self) -> Path:
        return self._home_path

    @property
    def log_path(self) -> Path:
        return self._log_path

    @property
    def debug_path(self) -> Path:
        return self._debug_path

    @property
    def env_path(self) -> Path:
        return self._env_path

    def create_paths(self):
        self._home_path.mkdir(parents=True, exist_ok=True)

        with open(self._log_path, "a"):
            pass

        with open(self._debug_path, "a"):
            pass

        # .env not created unless user gives permission


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
        function=clear_context,
        args="[command]",
    ),
    Command(
        name="/q",
        description="Non-interactive mode: send a single prompt and quickly get a response",
        function=quick_response,
        args="[prompt]",
    ),
]
