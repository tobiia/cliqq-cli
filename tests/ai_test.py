"""
# commands.py
def help(session: CliqqSession)
def exit_cliqq(session: CliqqSession)
def clear(session: CliqqSession)
def show_log(session: CliqqSession)
def clear_log(session: CliqqSession)
def clear_context(session: CliqqSession)
def quick_response(user_prompt: str, session: CliqqSession)
def dispatch(args, session: CliqqSession)

    class CliqqSession:
        def __init__(self)
        @property commands(self) -> dict[str, CommandSpec]
        @property model_name(self) -> str
        @model_name.setter model_name(self, value: str)
        @property base_url(self) -> str
        @base_url.setter base_url(self, value: str)
        @property api_key(self) -> str
        @api_key.setter api_key(self, value: str)
        def set_config(self, config: dict[str, str])
        @property home_path(self)
        @property log_path(self)
        @property env_path(self)
        @property script_path(self)
        def set_path(self, path_name: str, path: str)
        def get_path(self, path_name: str)
        @property chat_history(self) -> list[dict[str, str]]
        def remember(self, msg: dict[str, str])
        def forget(self)
        def log(self, text: str)
        def flush_log(self)

# main.py
def create_paths(session: CliqqSession)
def load_template_local(name: str, session: CliqqSession) -> str
def user_input(session: CliqqSession, sensitive=False) -> str
def program_choice(question: str, choices: list, session: CliqqSession, sensitive=False) -> str
def program_output(text: str, session: CliqqSession, end="\n", style_name="program", sensitive=False)
def main()

# prep.py
def parse_commands(session: CliqqSession) -> argparse.ArgumentParser
def prep_prompt(prompt: str, template: str) -> str

# ai.py
def ai_response(prompt: str, session: CliqqSession) -> tuple[CliqqSession, str | None]
def prompt_api_info(session: CliqqSession) -> dict[str, str]
def validate_api(config: dict[str, str], session: CliqqSession) -> bool
def save_env_file(config: dict[str, str], session: CliqqSession)
def find_api_info(session: CliqqSession) -> dict[str, str]
def ensure_api(session: CliqqSession) -> None

# action.py
def run(actionable: str, session: CliqqSession)
def run_command(command: str, session: CliqqSession, ask=True)
def save_file(file: dict[str, str], session: CliqqSession, overwrite=False)

"""
