from prompt_toolkit import prompt
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText, to_plain_text
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.shortcuts import choice

from cliqq.styles import DEFAULT_STYLE
from cliqq.log import logger


def user_input(log: bool = True) -> str:
    """Prompt the user for input with styled formatting and returns
    the entered text. Optionally logs the input.
    """

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
    """Present a multiple-choice question to the user and returns the
    selected option. Optionally logs both the question and the user’s selection.

    Args:
        question (str): The question text to display.
        choices (list[str]): A list of choices for the user to select from.
        log (bool, optional): Whether to log the question and selection. Defaults to True.

    Returns:
        str: The selected choice.
    """

    message = FormattedText([("class:name", "(cliqq) "), ("class:action", question)])

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
    """Print styled program output to the console.

    Args:
        text (str): The text to print.
        end (str, optional): Line ending to append. Defaults to "\\n".
        style_name (str, optional): Style class name to apply. Defaults to "program".
        continuous (bool, optional): If True, prints streaming output without prefix. Defaults to False.
        log (bool, optional): Whether to log the output. Defaults to True.
    """

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

    # don't log every streaming chunk
    if log and not continuous:
        if end:
            logger.info(f"{plain_text}{text}{end}")
        else:
            logger.info(plain_text + text)

    print_formatted_text(message, style=DEFAULT_STYLE, end=end, flush=True)
