import os
from dotenv import dotenv_values
from typing import Literal, TypedDict
import openai

from main import program_output, user_input, program_choice
from classes import ApiConfig, ChatHistory, PathManager
from action import save_file
from log import logger


def ai_response(
    prompt: str, api_config: ApiConfig, history: ChatHistory, paths: PathManager
) -> dict[str, str | bool] | None:
    delta_list = []
    data_buffer = []
    action_buffer = []
    actionable = None
    response_content = {"actionable": False, "content": ""}

    # ensure api info is valid every time an api call is made
    if not ensure_api(api_config, paths):
        # only called if program couldn't get valid api info
        program_output(
            f"I'm sorry, I cannot process your request! Please verify your API credentials and update your {paths.env_path} and/or your system environment variables. If you need further guidance, please refer to the README.md.",
            style_name="error",
        )
        return None

    client = openai.OpenAI(api_key=api_config.api_key, base_url=api_config.base_url)

    history.remember({"role": "user", "content": prompt})

    try:

        # don't really need generator?
        with client.chat.completions.create(
            model=api_config.model_name,
            messages=history.chat_history,  # type: ignore
            stream=True,
        ) as stream:  # type: ignore
            for chunk in stream:
                # ChatCompletionChunk(id='...', choices=[Choice(delta=ChoiceDelta(content='Two', function_call=None, role=None, tool_calls=None), finish_reason=None, ..., usage=None)
                if chunk.choices[0].delta and chunk.choices[0].delta.content:
                    # accumulate the content, print until end of content or recieve actionable
                    delta = str(chunk.choices[0].delta.content)
                    delta_list.append(delta)
                    if "[JSON_START]" in delta:
                        printing_action = True
                        response_content["actionable"] = True
                    if printing_action:
                        action_buffer.append(delta)
                        if "[JSON_END]" in delta:
                            printing_action = False
                            action_str = "".join(action_buffer)
                            pre_str, rest = action_str.split("[JSON_START]")
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
                            program_output(data_buffer[0], end="", style_name="action")
                        else:
                            program_output(data_buffer[0], end="")
                        data_buffer.pop(0)

                if chunk.choices[0].finish_reason == "stop":
                    break  # stop if the finish reason is 'stop
    except openai.AuthenticationError as e:
        logger.exception("AuthenticationError: %s", e)
        program_output(
            "API information validation failed: invalid API key",
            style_name="error",
        )
        return None
    except openai.BadRequestError as e:
        logger.exception("BadRequestError: %s", e)
        program_output(
            "API information validation failed: invalid model name",
            style_name="error",
        )
        return None
    except openai.NotFoundError as e:
        logger.exception("NotFoundError: %s", e)
        program_output(
            "API information validation failed: invalid base URL",
            style_name="error",
        )
        return None
    except Exception as e:
        logger.exception("Exception: %s", e)
        program_output(f"Unexpected error: {e}", style_name="error")
        return None

    program_output("".join(data_buffer))

    ai_response = "".join(delta_list)

    history.remember({"role": "assistant", "content": ai_response})

    if actionable:
        response_content["content"] = actionable
    else:
        response_content["content"] = ai_response

    return response_content


def prompt_api_info() -> dict[str, str]:
    # TODO create default w openai
    # TODO only change 1 field
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
        style_name="error",
    )
    program_output(instructions)
    program_output(
        "I will now prompt you to provide the name of the model you want to use, the API key, and the base url.",
        style_name="action",
    )
    program_output(
        "Please enter the MODEL NAME for this language model:",
        style_name="action",
    )
    model_name = user_input(sensitive=True)
    program_output(
        "Please enter the BASE URL for this language model:",
        style_name="action",
    )
    base_url = user_input(sensitive=True)
    program_output(
        "Please enter your API KEY for this language model:",
        style_name="action",
    )
    api_key = user_input(sensitive=True)

    config = {
        "model_name": model_name,
        "base_url": base_url,
        "api_key": api_key,
    }

    return config


def validate_api(config: dict[str, str], paths: PathManager) -> bool:
    try:
        client = openai.OpenAI(api_key=config["api_key"], base_url=config["base_url"])

        # quick call
        resp = client.chat.completions.create(
            model=config["model_name"],
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )

        # if we get here, info was validated/correct

        choices = [
            ("yes", "Yes"),
            ("no", "No"),
        ]
        user_choice = program_choice(
            "Would you like for me to create a .env file with your API information so you do not need to provide it the next time you load Cliqq?",
            choices,
        )
        if user_choice.lower() == "yes":
            if save_env_file(config, paths):
                program_output(f"Your .env file has been created at {paths.env_path}!")
            else:
                program_output(
                    f"Sorry, I failed to create a .env file for you! If you would like to create one yourself, please do so at {paths.env_path}."
                )
        return True

    except openai.AuthenticationError as e:
        logger.exception("AuthenticationError: %s", e)
        program_output(
            "API information validation failed: invalid API key",
            style_name="error",
        )
        return False
    except openai.BadRequestError as e:
        logger.exception("BadRequestError: %s", e)
        program_output(
            "API information validation failed: invalid model name",
            style_name="error",
        )
        return False
    except openai.NotFoundError as e:
        logger.exception("NotFoundError: %s", e)
        program_output(
            "API information validation failed: invalid base URL",
            style_name="error",
        )
        return False
    except Exception as e:
        logger.exception("Exception: %s", e)
        program_output(f"Unexpected error: {e}", style_name="error")
        return False


def save_env_file(config: dict[str, str], paths: PathManager) -> bool:
    path = paths.env_path
    content = f"MODEL_NAME={config['model_name']}\nBASE_URL={config['base_url']}\nAPI_KEY={config['api_key']}\n"
    file = {"action": "file", "path": path, "content": content}
    return save_file(file, overwrite=True)


def find_api_info(paths: PathManager) -> dict[str, str]:
    config = {}

    env_file = paths.env_path

    # check values in .env if it exists
    if os.path.exists(env_file):
        env_dict = dotenv_values(env_file)
        model_name = env_dict.get("MODEL_NAME")
        base_url = env_dict.get("BASE_URL")
        api_key = env_dict.get("API_KEY")

        if model_name and base_url and api_key:
            config = {
                "model_name": model_name,
                "base_url": base_url,
                "api_key": api_key,
            }
            if validate_api(config, paths):
                return config

    # if .env check fails, check sys env vars
    model_name = os.getenv("MODEL_NAME")
    base_url = os.getenv("BASE_URL")
    api_key = os.getenv("API_KEY")

    if model_name and base_url and api_key:
        config = {"model_name": model_name, "base_url": base_url, "api_key": api_key}
        if validate_api(config, paths):
            return config

    # if neither, prompt the user for api info
    config = prompt_api_info()
    if validate_api(config, paths):
        return config
    else:
        raise ValueError(
            "Invalid API credentials (checked .env, system environment variables, and user input)"
        )


def ensure_api(api_config: ApiConfig, paths: PathManager) -> bool:
    # ensures api info is set
    if api_config.model_name and api_config.base_url and api_config.api_key:
        # don't validate again b/c if these have been set, the user must've made a valid call before
        return True

    program_output(
        "Your API credentials are not configured. Let's set those up now!",
        style_name="error",
    )

    # was unsure how to change so it doesn't return None since find_api raises an error
    # --> obviously catch it w a try-except
    try:
        config = find_api_info(paths)
        api_config.set_config(config)
        return True
    except ValueError as e:
        logger.exception("ValueError: %s", e)
        program_output(
            f"Failed to configure API credentials: {e}",
            style_name="error",
        )
        return False
    except Exception as e:
        logger.exception("Exception: %s", e)
        program_output(
            f"Failed to configure API credentials: {e}",
            style_name="error",
        )
        return False
