import os
import sys
from dotenv import dotenv_values
import openai
from main import program_output, user_input, program_choice, CliqqSession
from action import save_file


def ai_response(prompt: str, session: CliqqSession) -> tuple[CliqqSession, str | None]:
    ai_response = ""
    data_buffer = []
    action_buffer = ""
    actionable = None

    client = openai.OpenAI(
        api_key=session.get_config("api_key"), base_url=session.get_config("base_url")
    )

    session.remember({"role": "user", "content": prompt})

    try:

        # don't really need generator?
        with client.chat.completions.create(
            model=session.get_config("model_name"),
            messages=session._chat_history,  # type: ignore
            stream=True,
        ) as stream:  # type: ignore
            for chunk in stream:
                # ChatCompletionChunk(id='...', choices=[Choice(delta=ChoiceDelta(content='Two', function_call=None, role=None, tool_calls=None), finish_reason=None, ..., usage=None)
                if chunk.choices[0].delta and chunk.choices[0].delta.content:
                    # accumulate the content, print until end of content or recieve actionable
                    delta = str(chunk.choices[0].delta.content)
                    ai_response += delta
                    if "[JSON_START]" in delta:
                        printing_action = True
                    if printing_action:
                        action_buffer += delta
                        if "[JSON_END]" in delta:
                            printing_action = False
                            pre_str, rest = action_buffer.split("[JSON_START]")
                            actionable, post_str = rest.split("[JSON_END]")
                            data_buffer.extend(
                                [pre_str, "incoming action", actionable, post_str]
                            )
                    else:
                        data_buffer.append(delta)

                    if len(data_buffer) > 5:
                        if data_buffer[0] == "incoming action":
                            # pop the flag
                            data_buffer.pop(0)
                            program_output(
                                data_buffer[0], session, end="", style_name="action"
                            )
                        else:
                            program_output(data_buffer[0], session, end="")
                        data_buffer.pop(0)

                if chunk.choices[0].finish_reason == "stop":
                    break  # stop if the finish reason is 'stop
    except openai.AuthenticationError:
        program_output(
            "API information validation failed: invalid API key",
            session,
            style_name="error",
        )
    except openai.BadRequestError:
        program_output(
            "API information validation failed: invalid model name",
            session,
            style_name="error",
        )
    except openai.NotFoundError:
        program_output(
            "API information validation failed: invalid base URL",
            session,
            style_name="error",
        )
    except Exception as e:
        program_output(f"Unexpected error: {e}", session, style_name="error")

    program_output("".join(data_buffer), session)

    session.remember({"role": "assistant", "content": ai_response})

    return session, actionable


def prompt_api_info(session: CliqqSession) -> dict[str, str]:
    # TODO create default w openai
    instructions = """
    To use Cliqq, you need to configure it to work with your API of choice
    If you want to avoid having to provide your API information every time you use Cliqq, you can either:
        - Create a file ~/.cliqq/.env with variables MODEL_NAME, BASE_URL, and API_KEY
        - Set environment variables named MODEL_NAME, BASE_URL, and API_KEY
    Further information can be found in the README.md

    If you believe that this is a mistake, please check the values of your environment variables in your ~/.cliqq/.env (if it exists) and/or your system environment variables. Cliqq will always prioritize the values in the .env file if it exists.
    """

    program_output(
        "Your API information could not be found automatically.",
        session,
        style_name="action",
    )
    program_output(instructions, session)
    program_output(
        "I will now prompt you to provide the name of the model you want to use, the API key, and the base url.",
        session,
        style_name="action",
    )
    program_output(
        "Please enter the MODEL NAME for this language model:",
        session,
        style_name="action",
    )
    # FIXME add arg to prevent logging sensitive info!
    model_name = user_input(session)
    program_output(
        "Please enter the BASE URL for this language model:",
        session,
        style_name="action",
    )
    base_url = user_input(session)
    program_output(
        "Please enter your API KEY for this language model:",
        session,
        style_name="action",
    )
    api_key = user_input(session)

    config = {
        "model_name": model_name,
        "base_url": base_url,
        "api_key": api_key,
    }

    choices = [
        ("yes", "Yes"),
        ("no", "No"),
    ]
    user_choice = program_choice(
        "Would you like for me to create a .env file with your API information so you do not need to provide it the next time you load Cliqq?",
        choices,
        session,
    )
    if user_choice.lower() == "yes":
        save_env_file(config, session)
    else:
        program_output(
            "",
            session,
        )

    return config


def save_env_file(config: dict[str, str], session: CliqqSession):
    path = session.env_path
    content = f"MODEL_NAME={config['model_name']}\nBASE_URL={config['base_url']}\nAPI_KEY={config['api_key']}\n"
    file = {"action": "file", "path": path, "content": content}
    save_file(file, session, overwrite=True)


def validate_api(config: dict[str, str], session: CliqqSession) -> bool:
    try:
        client = openai.OpenAI(api_key=config["api_key"], base_url=config["base_url"])

        # quick call
        resp = client.chat.completions.create(
            model=config["model_name"],
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )

        # if we get here, all are valid
        return True

    except openai.AuthenticationError:
        program_output(
            "API information validation failed: invalid API key",
            session,
            style_name="error",
        )
        return False
    except openai.BadRequestError:
        program_output(
            "API information validation failed: invalid model name",
            session,
            style_name="error",
        )
        return False
    except openai.NotFoundError:
        program_output(
            "API information validation failed: invalid base URL",
            session,
            style_name="error",
        )
        return False
    except Exception as e:
        program_output(f"Unexpected error: {e}", session, style_name="error")
        return False


def find_api_info(session: CliqqSession) -> dict[str, str]:
    config = {}

    env_file = os.path.expanduser(session.env_path)

    # check values in .env if it exists
    if os.path.exists(env_file):
        env_dict = dotenv_values(env_file)
        model_name = env_dict.get("MODEL_NAME")
        base_url = env_dict.get("BASE_URL")
        api_key = env_dict.get("API_KEY")

        if model_name and base_url and api_key:
            config = {
                "MODEL_NAME": model_name,
                "BASE_URL": base_url,
                "API_KEY": api_key,
            }
            if validate_api(config, session):
                return config

    # if .env check fails, check sys env vars
    model_name = os.getenv("MODEL_NAME")
    base_url = os.getenv("BASE_URL")
    api_key = os.getenv("API_KEY")

    if model_name and base_url and api_key:
        config = {"MODEL_NAME": model_name, "BASE_URL": base_url, "API_KEY": api_key}
        if validate_api(config, session):
            return config

    # if neither, prompt the user for api info
    return prompt_api_info(session)
