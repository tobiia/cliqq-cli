from prompt_toolkit.styles import Style

DEFAULT_STYLE = Style.from_dict(
    # what is fg???
    {
        # User input (default text).
        "": "#00a2ff",
        # Prompt.
        "user": "#41D6BB",
        "name": "#00aa00",
        "program": "#00aa00",
        "action": "#e914a5",
        "input-selection": "fg:#ff0000",
        "number": "fg:#884444 bold",
        "selected-option": "underline",
    }
)
