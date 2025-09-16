import os
import sys
from dotenv import load_dotenv
import openai
from main import program_output, user_input, program_choice
from action import save_file


def ai_response(prompt, session):
    ai_response = ""
    data_buffer = []
    action_buffer = ""
    actionable = False

    client = openai.OpenAI(
        api_key=session.config["api_key"], base_url=session.config["base_url"]
    )

    session.chat_history = session.chat_history.append(
        {"role": "user", "content": prompt}
    )

    try:

        # don't really need generator?
        with client.chat.completions.create(
            # "openai/gpt-4o"
            model=session.config["model_name"],
            messages=session.chat_history,
            stream=True,
        ) as stream:
            for chunk in stream:
                # ChatCompletionChunk(id='...', choices=[Choice(delta=ChoiceDelta(content='Two', function_call=None, role=None, tool_calls=None), finish_reason=None, ..., usage=None)
                if chunk.choices[0].delta and chunk.choices[0].delta.content:
                    # accumulate the content, print until end of content or recieve actionable
                    delta = chunk.choices[0].delta.content
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
                            program_output(data_buffer[0], end="", style_name="action")
                        else:
                            program_output(data_buffer[0], end="")
                        data_buffer.pop(0)

                if chunk.choices[0].finish_reason == "stop":
                    break  # stop if the finish reason is 'stop
    except openai.AuthenticationError:
        program_output(
            "API information validation failed: invalid API key", style_name="error"
        )
    except openai.BadRequestError:
        program_output(
            "API information validation failed: invalid model name", style_name="error"
        )
    except openai.NotFoundError:
        program_output(
            "API information validation failed: invalid base URL", style_name="error"
        )
    except Exception as e:
        program_output(f"Unexpected error: {e}", style_name="error")

    program_output("".join(data_buffer), end="")

    session.chat_history.append({"role": "assistant", "content": ai_response})

    return session, actionable


def prompt_api_info():
    instructions = """

    To use Cliqq, you need to configure it to work with your API of choice
    If you want to avoid having to provide your API information every time you use Cliqq, you can either:
        - Create a file ~/.cliqq/.env with variables MODEL_NAME, BASE_URL, and API_KEY
        - Set environment variables named MODEL_NAME, BASE_URL, and API_KEY
        - Pass them as arguments and start Cliqq using this command: cliqq api [model_name] [base_url], and [api_key]
    
    Further information can be found in the README.md or using the command: cliqq help
    """

    program_output("Your API information could not be found automatically.")
    program_output(instructions)
    program_output(
        "I will now prompt you to provide the name of the model you want to use, the API key, and the base url."
    )
    api_key = user_input()
    base_url = user_input()
    model_name = user_input()

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
    )
    if user_choice.lower() == "yes":
        save_env_file(config)

    return config


def save_env_file(config):
    path = "~/.cliqq/.env"
    content = f"MODEL_NAME={config['model_name']}\nBASE_URL={config['base_url']}\nAPI_KEY={config['api_key']}\n"
    file = {"action": "file", "path": path, "content": content}
    save_file(file)


# TODO is this auth or validation?
def validate_api(config):
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
            "API information validation failed: invalid API key", style_name="error"
        )
        return False
    except openai.BadRequestError:
        program_output(
            "API information validation failed: invalid model name", style_name="error"
        )
        return False
    except openai.NotFoundError:
        program_output(
            "API information validation failed: invalid base URL", style_name="error"
        )
        return False
    except Exception as e:
        program_output(f"Unexpected error: {e}", style_name="error")
        return False


def find_api_info():
    config = {"": ""}
    env_file = os.path.expanduser("~") + "/.cliqq/.env"
    load_dotenv(env_file, override=True)
    model_name = os.getenv("MODEL_NAME")
    base_url = os.getenv("BASE_URL")
    api_key = os.getenv("API_KEY")
    if model_name is None or base_url is None or api_key is None:
        config = prompt_api_info()
    else:
        if not validate_api(config):
            config = prompt_api_info()
    return config
