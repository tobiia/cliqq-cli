import json
import os
import subprocess
import shlex

from main import user_input, program_output, program_choice, CliqqSession
from ai import ai_response


def run(actionable: str, session: CliqqSession):
    try:
        data = json.loads(actionable)
    except json.JSONDecodeError:
        program_output(
            "Something went wrong with my response and I can't parse it. I'm sorry! Please ask me again!",
            session,
            style_name="error",
        )
        return
    except Exception as e:
        program_output(f"Unexpected error: {e}", session, style_name="error")
        return

    action = data.get("action")
    if action == "command":
        run_command(data["command"], session)
    elif action == "file":
        save_file(data, session)
    else:
        program_output(
            f"Failed to find action '{action}'. Please try again!",
            session,
            style_name="error",
        )


def run_command(command: str, session: CliqqSession, ask=True):
    """
    TODO: comments :(
    """
    try:
        cmd = shlex.split(command)

        output = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if output.returncode != 0:
            program_output(
                f"Command {command} failed with exit code {output.returncode}:\n{output.stderr.strip()}\nPlease try again!",
                session,
                style_name="error",
            )
        else:
            program_output(output.stdout.strip(), session, style_name="action")
        # send output to ai
        if ask:
            choices = [
                ("yes", "Yes"),
                ("no", "No"),
            ]
            user_choice = program_choice(
                "Would you like for me to analyze this output?", choices, session
            )
            if user_choice == "yes":
                ai_response(output.stdout.strip(), session)

    except FileNotFoundError:
        program_output(
            f"Failed to find command {command}\nPlease try again!",
            session,
            style_name="error",
        )

    except Exception as e:
        program_output(f"Unexpected error: {e}", session, style_name="error")


def save_file(file: dict[str, str], session):
    path = os.path.expanduser(file["path"])
    content = file["content"]
    name = os.path.basename(path)

    # ensure the directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)

    try:
        with open(path, "x") as f:
            f.write(content)

    except FileExistsError:
        choices = [("yes", "Yes"), ("no", "No")]
        user_choice = program_choice(
            f"The file '{name}' already exists. Should I overwrite its content?",
            choices,
            session,
        )

        if user_choice == "yes":
            with open(path, "w") as f:
                f.write(content)
        else:
            program_output(
                "Okay, please provide a different name for the file.",
                session,
                style_name="action",
            )
            new_name = user_input(session)
            new_path = os.path.join(os.path.dirname(path), new_name)

            try:
                with open(new_path, "x") as f:
                    f.write(content)
            except FileExistsError:
                program_output(
                    f"The file '{new_name}' already exists too. This operation will be aborted.\nPlease request this file again!",
                    session,
                    style_name="error",
                )

    except Exception as e:
        program_output(f"Unexpected error: {e}", session, style_name="error")
