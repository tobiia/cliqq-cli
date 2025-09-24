from prompt_toolkit.styles import Style

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
        "error": "#e22d2d",
        "input-selection": "#71aabd",
        "selected-option": "underline bold",
    }
)
