import os
import sys
from openai import (
    OpenAI,
    APIError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)
from main import program_output


def find_api_info():
    # need to prompt user for this info
    # give suggestions for openai, claude, openrouter
    return


def prompt_ai(key, base_url, model, prompt, context):
    ai_response = ""
    data_buffer = []
    action_buffer = ""
    actionable = False

    client = OpenAI(api_key=key, base_url=base_url)

    chat_history = context.append({"role": "user", "content": prompt})

    # don't really need generator?
    with client.chat.completions.create(
        # "openai/gpt-4o"
        model=model,
        messages=context,
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
                        data_buffer.extend([pre_str, "incoming action", actionable, post_str])
                else:
                    data_buffer.append(delta)

                if len(data_buffer) > 5:
                    if data_buffer[0] is "incoming action":
                         # pop the flag
                         data_buffer.pop(0)
                         program_output(data_buffer[0], end="", True)
                    else:
                         program_output(data_buffer[0], end="")
                    data_buffer.pop(0)

            if chunk.choices[0].finish_reason == "stop":
                break  # stop if the finish reason is 'stop'

    program_output("".join(data_buffer), end="")

    chat_history.append({"role": "assistant", "content": ai_response})

    return chat_history, actionable
