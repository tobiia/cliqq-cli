from prompt_toolkit.styles import Style

"""Default prompt_toolkit style configuration.

Defines color and style rules for various text classes used
in the Cliqq CLI (e.g., user input, program output, errors).
"""

DEFAULT_STYLE = Style.from_dict(
    {
        # default
        "": "#91a9f9",
        # Prompt.
        "user": "#91a9f9 bold",  # user prompt
        "name": "#ad70f7 bold",  # (cliqq)
        "program": "#ad70f7",  # default program print
        "info": "#d5b9f8",
        "action": "#71aabd",
        "error": "#e3915e",
        "input-selection": "#71aabd",
        "selected-option": "underline bold",
    }
)
