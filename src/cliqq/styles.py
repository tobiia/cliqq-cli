from prompt_toolkit.styles import Style

"""Default prompt_toolkit style configuration.

Defines color and style rules for various text classes used
in the Cliqq CLI (e.g., user input, program output, errors).
"""

DEFAULT_STYLE = Style.from_dict(
    {
        "": "#f8f8f2",
        "user": "#8be9fd bold",
        "name": "#bd93f9 bold",
        "program": "#f8f8f2",
        "info": "#50fa7b",
        "action": "#ff79c6",
        "error": "#ff5555 bold",
        "input-selection": "#ffb86c",
        "selected-option": "underline bold",
    }
)
