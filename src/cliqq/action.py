import json
from pathlib import Path
import subprocess
import shlex

from main import user_input, program_output, program_choice
from classes import ApiConfig, ChatHistory, PathManager
from ai import ai_response
from log import logger


def run(
    actionable: str, api_config: ApiConfig, history: ChatHistory, paths: PathManager
) -> bool:

    data = parse_actionable(actionable)

    if not data:
        program_output(
            "Something went wrong with my response and I can't parse it. Please ask me again!",
            style_name="error",
        )
        return False

    action_type = data.get("action")
    match action_type:
        case "command":
            return run_command(data["command"], api_config, history, paths.env_path)
        case "file":
            return save_file(data)
        case _:
            program_output(f"Invalid action: {data}", style_name="error")
            return False


def parse_actionable(actionable: str) -> dict[str, str] | None:
    """Parse actionable JSON safely. Return dict or None on failure."""
    try:
        return json.loads(actionable)
    except json.JSONDecodeError as e:
        logger.exception("Unable to parse actionable: %s", e)
        return None


def execute_command(command) -> tuple[int, str, str]:
    try:
        cmd = shlex.split(command)

        output = subprocess.run(cmd, capture_output=True, text=True, check=False)

        return output.returncode, output.stdout.strip(), output.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"Command not found: {command}"


def offer_analyze_output(output, api_config, history, env_path) -> None:
    choices = [
        ("yes", "Yes"),
        ("no", "No"),
    ]
    user_choice = program_choice(
        "Would you like for me to analyze this output?",
        choices,
    )
    if user_choice == "yes":
        ai_response(output.stdout.strip(), api_config, history, env_path)


# args = command as a str, just called args so commands.dispatch works
def run_command(
    args: str,
    api_config: ApiConfig,
    history: ChatHistory,
    env_path: Path,
    ask: bool = True,
) -> bool:

    # for clarity
    command = args

    code, stdout, stderr = execute_command(command)

    if code != 0:
        program_output(
            f"Command {command} failed with exit code {code}:\n{stderr}\nPlease try again!",
            style_name="error",
        )
        return False

    program_output(stdout.strip(), style_name="action")

    if ask:
        offer_analyze_output(stdout, api_config, history, env_path)

    return True


def save_file(file: dict[str, str], overwrite: bool = False) -> bool:
    # file is in json format
    path = Path(file["path"]).expanduser()
    content = file["content"]

    # ensure the directory exists
    path.parent.mkdir(exist_ok=True)

    try:
        write_file(path, content, overwrite)
        return True

    except FileExistsError:
        return resolve_conflict(path, content)
    except IOError as e:
        logger.exception(e)
        return False


def write_file(path: Path, content: str, overwrite: bool = False):
    if overwrite:
        mode = "w"
    else:
        mode = "x"

    with open(path, mode) as f:
        f.write(content)


def resolve_conflict(path: Path, content: str) -> bool:

    choices = [("yes", "Yes"), ("no", "No")]
    user_choice = program_choice(
        f"The file '{path}' already exists. Should I overwrite its content?",
        choices,
    )

    if user_choice == "yes":
        write_file(path, content, overwrite=True)
        return True
    else:
        # FIXME allow user to dscard file here
        program_output(
            "Okay, please provide a different name for the file.",
            style_name="action",
        )
        new_name = user_input()
        new_path = path.parent / new_name
        if new_path.is_dir():
            ext = path.suffix
            new_path = new_path / ext
        try:
            write_file(new_path, content, overwrite=False)
            return True
        except FileExistsError:
            program_output(
                f"The file '{new_path}' already exists too. This operation will be aborted.\nPlease request this file again!",
                style_name="error",
            )
            return False
