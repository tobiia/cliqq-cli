from prompt_toolkit.styles import Style

DEFAULT_STYLE = Style.from_dict(
    {
        # default
        "": "#91a9f9",
        # Prompt.
        "user": "#91a9f9 bold",  # user prompt
        "name": "#ad70f7 bold",  # (cliqq)
        "program": "#cba6f7",  # default program print
        "action": "#4bccbb",
        "error": "#e22d2d bold",
        "input-selection": "#91a9f9",
        "selected-option": "underline",
    }
)
