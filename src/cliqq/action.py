import json
import os
from pathlib import Path
import subprocess
import shlex

from main import user_input, program_output, program_choice
from classes import ApiConfig, ChatHistory, PathManager
from ai import ai_response
from log import logger


def run(
    actionable: str, api_config: ApiConfig, history: ChatHistory, paths: PathManager
) -> None:
    try:
        data = json.loads(actionable)
    except json.JSONDecodeError as e:
        logger.exception("Exception: %s", e)
        program_output(
            "Something went wrong with my response and I can't parse it. I'm sorry! Please ask me again!",
            style_name="error",
        )
        return
    except Exception as e:
        logger.exception("Exception: %s", e)
        program_output(f"Unexpected error: {e}", style_name="error")
        return

    action = data.get("action")
    if action == "command":
        run_command(data["command"], api_config, history, paths)
    elif action == "file":
        save_file(data)
    else:
        program_output(
            f"Failed to find action '{action}'. Please try again!",
            style_name="error",
        )


def run_command(
    command: str,
    api_config: ApiConfig,
    history: ChatHistory,
    paths: PathManager,
    ask: bool = True,
) -> None:
    """
    TODO: comments :(
    """
    try:
        cmd = shlex.split(command)

        output = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if output.returncode != 0:
            program_output(
                f"Command {command} failed with exit code {output.returncode}:\n{output.stderr.strip()}\nPlease try again!",
                style_name="error",
            )
        else:
            program_output(output.stdout.strip(), style_name="action")
        # send output to ai
        if ask:
            choices = [
                ("yes", "Yes"),
                ("no", "No"),
            ]
            user_choice = program_choice(
                "Would you like for me to analyze this output?",
                choices,
            )
            if user_choice == "yes":
                ai_response(output.stdout.strip(), api_config, history, paths)

    except FileNotFoundError as e:
        logger.exception("FileNotFoundError: %s", e)
        program_output(
            f"Failed to find command {command}\nPlease try again!",
            style_name="error",
        )

    except Exception as e:
        logger.exception("Exception: %s", e)
        program_output(f"Unexpected error: {e}", style_name="error")


def save_file(file: dict[str, str], overwrite: bool = False) -> None:
    # file is in json format
    path = Path(file["path"]).expanduser()
    content = file["content"]
    file_name = path.name

    # ensure the directory exists
    path.parent.mkdir(exist_ok=True)

    try:
        with open(path, "x") as f:
            f.write(content)

    except FileExistsError as e:
        if overwrite:
            with open(path, "w") as f:
                f.write(content)
        else:
            choices = [("yes", "Yes"), ("no", "No")]
            user_choice = program_choice(
                f"The file '{file_name}' already exists. Should I overwrite its content?",
                choices,
            )

            if user_choice == "yes":
                with open(path, "w") as f:
                    f.write(content)
            else:
                # TODO return the file path just in case it changes
                program_output(
                    "Okay, please provide a different name for the file.",
                    style_name="action",
                )
                new_name = user_input()
                new_path = path.parent / new_name

                try:
                    with open(new_path, "x") as f:
                        f.write(content)
                except FileExistsError:
                    program_output(
                        f"The file '{new_name}' already exists too. This operation will be aborted.\nPlease request this file again!",
                        style_name="error",
                    )

    except Exception as e:
        logger.exception("Exception: %s", e)
        program_output(f"Unexpected error: {e}", style_name="error")
