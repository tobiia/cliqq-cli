import json
from pathlib import Path
import subprocess
import shlex

from cliqq.log import logger
from cliqq.io import user_input, program_output, program_choice
from cliqq.models import ApiConfig, ChatHistory, PathManager

# load safety rules once
with open(Path(__file__).parent / "safety_rules.json", encoding="utf-8") as f:
    RULES = json.load(f)

DENY_ALWAYS = [t.lower() for t in RULES["DENY_ALWAYS"]]
CONFIRM_FIRST = [t.lower() for t in RULES["CONFIRM_FIRST"]]


def run(
    action: dict[str, str],
    api_config: ApiConfig,
    history: ChatHistory,
    paths: PathManager,
) -> bool:
    """Dispatches `action` to the appropriate hander"""

    action_type = action.get("type")
    if action_type == "command":
        return run_command(action["command"], api_config, history, paths)
    elif action_type == "file":
        return save_file(action)
    else:
        program_output(f"Invalid action: {action}", style_name="error")
        return False


def run_command(
    args: str,
    api_config: ApiConfig,
    history: ChatHistory,
    paths: PathManager,
    ask: bool = True,
) -> bool:
    """Coordinates the check and execution of a given command"""

    # for clarity
    command = args

    danger_level = classify_command(command)

    if danger_level == "deny":

        logger.error(f"Command denied: {command}")
        program_output(
            f"This command is considered too dangerous and will not be run:\n  {command}",
            style_name="error",
        )

        return False

    elif danger_level == "confirm":

        choices = [
            ("yes", "Yes"),
            ("no", "No"),
        ]
        user_choice = program_choice(
            f"This command may be unsafe or cause permanent changes to your system. Do you want to continue?\n  {command}",
            choices=choices,
        )
        if user_choice == "no":
            program_output("Command aborted.", style_name="error")
            return False

    code, stdout, stderr = execute_command(command)

    if stdout:
        program_output(
            f"Command `{command}` succeeded with exit code {code}:\n{stdout}\n"
        )

    if stderr:
        program_output(
            f"Command `{command}` failed with exit code {code}:\n{stderr}\n",
            style_name="error",
        )

    if ask:
        offer_analyze_output(stdout, paths.env_path, api_config, history)

    return code == 0


def execute_command(command: str) -> tuple[int, str, str]:
    """Runs a command"""

    try:
        cmd = shlex.split(command)

        # NOTE: This program executes commands with `shell=True` to support a broader range of functionality. While this improves compatibility, it also increases potential security risks. A strict denylist is enforced, and the AI is instructed not to generate dangerous commands. However, please exercise caution and use this software with an understanding of the associated risks.

        output = subprocess.run(
            cmd, capture_output=True, text=True, check=False, shell=True
        )

        return output.returncode, output.stdout.strip(), output.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"Command not found: {command}"


def classify_command(command: str) -> str:
    """Classifies and returns the danger level/status of a command"""
    lowered = command.lower()
    if any(token in lowered for token in DENY_ALWAYS):
        return "deny"
    if any(token in lowered for token in CONFIRM_FIRST):
        return "confirm"
    return "safe"


def offer_analyze_output(
    stdout: str, env_path: Path, api_config: ApiConfig, history: ChatHistory
) -> None:
    """Retrieves user input as to whether stdout from command execution
    should be sent and analyzed by the AI"""
    choices = [
        ("yes", "Yes"),
        ("no", "No"),
    ]
    user_choice = program_choice(
        "Would you like for me to analyze this output?",
        choices,
    )
    if user_choice == "yes":
        from cliqq.ai import ai_response

        ai_response(stdout.strip(), env_path, api_config, history)


def save_file(file: dict[str, str], overwrite: bool = False) -> bool:
    """Coordinates saving a given file

    Args:
        file:
            a dictionary containing "path" and "content" keys
        overwrite:
            If True user and a file with the given path already
            exists, the file is overwritten
    """

    path = Path(file["path"]).expanduser()
    content = file["content"]

    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        write_file(path, content, overwrite)
        return True

    except FileExistsError:
        return resolve_conflict(path, content)
    except IOError as e:
        logger.exception("IOError: Error while saving file\n%s", e)
        return False


def write_file(path: Path, content: str, overwrite: bool = False):
    if overwrite:
        mode = "w"
    else:
        mode = "x"

    with open(path, mode, encoding="utf-8") as f:
        f.write(content)


def resolve_conflict(path: Path, content: str) -> bool:
    """Resolves file saving conflicts with user prompting"""

    choices = [("yes", "Yes"), ("no", "No")]
    user_choice = program_choice(
        f"The file '{path}' already exists. Should I overwrite its content?",
        choices,
    )

    if user_choice == "yes":
        write_file(path, content, overwrite=True)
        return True
    else:
        # FIXME allow user to discard file here
        program_output(
            "Okay, please provide a different name for the file.",
            style_name="action",
        )
        new_name = user_input()
        new_path = path.parent / new_name
        # user gave a directory
        if new_path.is_dir():
            new_path = new_path / path.name
        # name with no extension
        elif not new_path.suffix and path.suffix:
            new_path = new_path.with_suffix(path.suffix)

        try:
            write_file(new_path, content, overwrite=False)
            return True
        except FileExistsError:
            program_output(
                f"The file '{new_path}' already exists too. This operation will be aborted.\nPlease request this file again!",
                style_name="error",
            )
            return False
