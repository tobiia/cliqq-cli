import os
import re
from pathlib import Path
from dotenv import dotenv_values
from typing import Iterable
import openai

from cliqq.log import logger
from cliqq.io import program_output, user_input, program_choice
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cliqq.models import ApiConfig, ChatHistory

API_ERROR_MESSAGES = {
    openai.AuthenticationError: "API information validation failed: invalid API key",
    openai.BadRequestError: "API information validation failed: invalid model name",
    openai.NotFoundError: "API information validation failed: invalid base URL",
    ValueError: "Invalid API credentials (checked .env, system environment variables, and user input)",
}


def ai_response(
    user_prompt: str,
    env_path: Path,
    api_config: ApiConfig,
    history: ChatHistory,
) -> tuple[bool, dict[str, str]] | tuple[bool, None]:

    try:

        history.remember({"role": "user", "content": user_prompt})

        # ensure api info is valid every time an api call is made
        if not ensure_api(env_path, api_config):
            # false if program couldn't get valid api info
            program_output(
                f"I'm sorry, I cannot process your request! Please verify your API credentials and update your {env_path} and/or your system environment variables. If you need further guidance, please refer to the README.md.",
                style_name="error",
            )
            return False, None

        actionable = False
        response_content = {"text": "", "action": ""}

        # generator
        # tool_calls and function_call to separate some content like action?
        deltas = stream_chunks(
            api_config.model_name,
            api_config.base_url,
            api_config.api_key,
            history.chat_history,
        )

        raw_accum = []

        # also generator
        for delta in buffer_deltas(deltas):
            raw_accum.append(delta)
            program_output(delta, end="")

        raw_full_text = "".join(raw_accum)  # full raw text with markers

        action = extract_action(raw_full_text)

        if action:
            program_output(action, end="", style_name="action")
            actionable = True
            response_content["action"] = action

        clean_full_text = re.sub(r"[\x1e\x1f]+", "", raw_full_text)

        response_content["text"] = clean_full_text

        # AI will remember raw text so it remembers the format needed
        history.remember({"role": "assistant", "content": raw_full_text})

        return actionable, response_content

    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        program_output(f"Unexpected error: {e}", style_name="error")
        return False, None


def stream_chunks(
    model_name: str, base_url: str, api_key: str, chat_history: list[dict[str, str]]
):
    client = openai.OpenAI(api_key=api_key, base_url=base_url)

    with client.chat.completions.create(
        model=model_name,
        messages=chat_history,  # type: ignore
        stream=True,
    ) as stream:
        for chunk in stream:
            # ChatCompletionChunk(id='...', choices=[Choice(delta=ChoiceDelta(content='Two', function_call=None, role=None, tool_calls=None), finish_reason=None, ..., usage=None)
            if chunk.choices[0].delta and chunk.choices[0].delta.content:
                # accumulate the content, print until end of content or recieve actionable
                delta = str(chunk.choices[0].delta.content)
                yield delta
            if chunk.choices[0].finish_reason == "stop":
                break  # stop if the finish reason is 'stop


def buffer_deltas(deltas: Iterable[str]):
    buffer = []
    for delta in deltas:
        buffer.append(delta)
        if len(buffer) >= 5:  # magic number?
            yield "".join(buffer)
            buffer.clear()

    if buffer:
        yield "".join(buffer)


def extract_action(text: str) -> str | None:
    start_tag, end_tag = "\x1e", "\x1f"
    start = text.find(start_tag)
    end = text.find(end_tag, start)

    if start != -1 and end != -1:
        action = text[start + len(start_tag) : end]
        return action.strip()
    return None


def prompt_api_info() -> dict[str, str]:
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
    model_name = user_input(log=False)
    program_output(
        "Please enter the BASE URL for this language model:",
        style_name="action",
    )
    base_url = user_input(log=False)
    program_output(
        "Please enter your API KEY for this language model:",
        style_name="action",
    )
    api_key = user_input(log=False)

    config = {
        "model_name": model_name,
        "base_url": base_url,
        "api_key": api_key,
    }

    return config


def validate_api(config: dict[str, str], env_path: Path) -> bool:
    try:
        if ping_api(config):
            offer_save_env(config, env_path)
            return True
    except openai.AuthenticationError as e:
        logger.exception("AuthenticationError, likely invalid API key: %s", e)
    except openai.BadRequestError as e:
        logger.exception("BadRequestError, likely invalid model name: %s", e)
    except openai.NotFoundError as e:
        logger.exception("NotFoundError, likely invalid base URL: %s", e)
    return False


def ping_api(config: dict[str, str]) -> bool:
    client = openai.OpenAI(api_key=config["api_key"], base_url=config["base_url"])
    resp = client.chat.completions.create(
        model=config["model_name"],
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=1,
    )
    return True
    # raise error if fail


def offer_save_env(config: dict[str, str], env_path: Path) -> None:
    choices = [
        ("yes", "Yes"),
        ("no", "No"),
    ]
    user_choice = program_choice(
        "Would you like for me to create a .env file with your API information so you do not need to provide it the next time you load Cliqq?",
        choices,
    )
    if user_choice.lower() == "yes":
        if save_env_file(config, env_path):
            program_output(f"Your .env file has been created at {env_path}!")
        else:
            program_output(
                f"Sorry, I failed to create a .env file for you! If you would like to create one yourself, please do so at {env_path}."
            )


def save_env_file(config: dict[str, str], env_path: Path) -> bool:
    content = f"MODEL_NAME={config['model_name']}\nBASE_URL={config['base_url']}\nAPI_KEY={config['api_key']}\n"
    file = {"action": "file", "path": env_path, "content": content}
    from cliqq.action import save_file

    return save_file(file, overwrite=True)


def find_api_info(env_path: Path) -> dict[str, str]:
    config = {}

    for loader in (lambda: load_env_file(env_path), load_sys_env, prompt_api_info):
        config = loader()
        if config and validate_api(config, env_path):
            return config

    raise ValueError()


def load_env_file(env_path: Path):
    if env_path.exists():
        env_dict = dotenv_values(env_path)
        model_name = env_dict.get("MODEL_NAME")
        base_url = env_dict.get("BASE_URL")
        api_key = env_dict.get("API_KEY")

        if model_name and base_url and api_key:
            return {
                "model_name": model_name,
                "base_url": base_url,
                "api_key": api_key,
            }
    return None


def load_sys_env():
    model_name = os.getenv("MODEL_NAME")
    base_url = os.getenv("BASE_URL")
    api_key = os.getenv("API_KEY")

    if model_name and base_url and api_key:
        return {
            "model_name": model_name,
            "base_url": base_url,
            "api_key": api_key,
        }
    return None


def ensure_api(env_path: Path, api_config: ApiConfig) -> bool:
    # ensures api info is set
    if api_config.model_name and api_config.base_url and api_config.api_key:
        # don't validate again b/c if these have been set, the user must've made a valid call before
        return True

    program_output(
        "Your API credentials are not configured. Let's set those up now!",
        style_name="error",
    )

    try:
        config = find_api_info(env_path)
        api_config.set_config(config)
        return True
    except ValueError as e:
        logger.exception("ValueError, unable to find valid API credentials: %s", e)
        return False
