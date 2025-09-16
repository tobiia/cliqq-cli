import json
import os
import subprocess
import shlex

from main import user_input, program_output, program_choice
from ai import ai_response


def run(actionable, session):
    data = json.loads(actionable)
    # TODO: need error handling in case not proper json
    if data["action"] == "command":
        run_command(data["command"], session)
    if data["action"] == "file":
        save_file(data)


def run_command(command, session):
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
        choices = [
            ("yes", "Yes"),
            ("no", "No"),
        ]
        user_choice = program_choice(
            "Would you like for me to analyze this output?",
            choices,
        )
        if user_choice == "yes":
            ai_response(output.stdout.strip(), session)

    except FileNotFoundError:
        program_output(
            f"Failed to find command {command}\nPlease try again!", style_name="error"
        )

    except Exception as e:
        program_output(f"Unexpected error running '{command}': {e}", style_name="error")


def save_file(file):
    path = file["path"]
    content = file["content"]
    name = os.path.basename(path)

    try:
        with open(path, "x") as f:
            f.write(content)
        return True
    except FileExistsError:
        choices = [
            ("yes", "Yes"),
            ("no", "No"),
        ]
        user_choice = program_choice(
            f"The file '{name}' already exists. Should I overwrite its contents?",
            choices,
        )

        if user_choice == "yes":
            with open(path, "w") as f:
                f.write(content)
            return True
        else:
            program_output(
                "Okay, please provide a different name for the file",
                style_name="action",
            )
            new_name = user_input()
            new_path = os.path.join(os.path.dirname(path), new_name)

            try:
                with open(new_path, "x") as f:
                    f.write(content)
                return True
            except FileExistsError:
                program_output(
                    "That file name already exists too. This operation will be aborted. Please request this file again!",
                    style_name="error",
                )
                return False
    except Exception as e:
        program_output(f"Unexpected error: {e}", style_name="error")
        return False
