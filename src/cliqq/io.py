from prompt_toolkit import prompt
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText, to_plain_text
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import choice

from cliqq.styles import DEFAULT_STYLE
from cliqq.log import logger


def user_input(log: bool = True) -> str:
    message = FormattedText(
        [
            ("class:user", ">> "),
        ]
    )
    input_text = prompt(
        message=message, style=DEFAULT_STYLE, auto_suggest=AutoSuggestFromHistory()
    )
    if log:
        logger.info(f"{to_plain_text(message)}{input_text}\n")
    return input_text


def program_choice(question: str, choices: list, log: bool = True) -> str:
    message = FormattedText([("class:name", "(cliqq) "), ("class:action", question)])
    # options is expected to be a list of (value, label) tuples
    # prompt_toolkit.shortcuts.choice returns the selected value
    from prompt_toolkit.shortcuts import choice

    result = choice(message=message, options=choices, style=DEFAULT_STYLE)
    if log:
        logger.info(f"{to_plain_text(message[0][1])}{question}\n")
        logger.info(f">> {result}\n")
    return result


def program_output(
    text: str,
    end: str = "\n",
    style_name: str = "program",
    continuous: bool = False,
    log: bool = True,
):

    if continuous:
        message = FormattedText(
            [
                ("class:" + style_name, text),
            ]
        )
        plain_text = to_plain_text(message[0][1])

    else:
        message = FormattedText(
            [
                ("class:name", "(cliqq) "),
                ("class:" + style_name, text),
            ]
        )
        plain_text = to_plain_text(message[1][1])

    if log:
        if end:
            logger.info(f"{plain_text}{text}{end}")
        else:
            logger.info(plain_text + text)

    print_formatted_text(message, style=DEFAULT_STYLE, end=end, flush=True)
