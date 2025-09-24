a simple, lightweight command line chat assistant to answer questions and carry out tasks on your computer

# Cliqq - Command Line AI Assistant

Cliqq is a simple, lightweight command-line interface tool that integrates AI capabilities to assist with various tasks, including command execution, file creation, and code generation. It runs seamlessly on Windows, Linux, and macOS.

## Installation

Windows (Powershell):
```powershell
# Clone the repository
git clone https://github.com/tobiia/cliqq-cli.git
cd cliqq

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Upgrade pip and install in editable mode
python -m pip install --upgrade pip
pip install -e .

```

Linux/macOS:
```
# Clone the repository
git clone https://github.com/tobiia/cliqq-cli.git
cd cliqq

# Install in editable (development) mode
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

## Usage

```bash
# Launch interactive mode
cliqq

# Display available commands and options
cliqq --help

# Ask a one-off question (non-interactive)
cliqq q "your question or request"
```

## Configuration

> If no configuration is found, Cliqq will prompt for credentials and can generate this file automatically.

Cliqq requires valid API credentials. It supports multiple providers including OpenAI, Anthropic, DeepSeek, and OpenRouter. Credentials can be supplied via a `.env` file or system environment variables.

### Option 1: `.env` file

1. Create the directory `~/.cliqq`
2. Inside it, create a file named `.env`
3. Add the following entries, filling in your credentials:

```
MODEL_NAME="your_model_name"
BASE_URL="your_base_url"
API_KEY="your_api_key"
```

### Option 2: Environment variables

On Windows (PowerShell):

```powershell
setx MODEL_NAME "your_model_name"
setx BASE_URL "your_base_url"
setx API_KEY "your_api_key"
```

On Linux/macOS:
```bash
export MODEL_NAME=your_model_name
export BASE_URL=your_base_url
export API_KEY=your_api_key
```
## Security Notice

This program runs commands with shell=True so it can handle a wider variety of commands. While this increases compatibility and flexibility, it also increases potential risks (ex. deleting important files). To reduce this, I've written a denylist of dangerous commands, guided the AI not to generate harmful ones, and made sure that it thoroughly explains what commands it suggests.

These precautions make the program safer to use, but it’s still important to be mindful of what’s being executed. Please only use the program only with trusted AI providers (well-known, professional platforms) or your own local AI models, not with unverified or experimental services.

And, I would suggest just deleting files by yourself. Just in case.


## Dependencies

- Python 3.8+
- pip
- pytest
- openai
- prompt_toolkit
- psutil
- python-dotenv
- Additional AI SDKs depending on the configured provider

## Project Structure

```
src/cliqq/
├── __init__.py             # Package initialization
├── action.py               # Action handling and execution
├── ai.py                   # AI integration and response processing
├── classes.py              # Core data classes and models
├── commands.py             # Command definitions and parsing logic
├── log.py                  # Logging setup and utilities
├── main.py                 # Application entry point
├── prep.py                 # Configuration and environment setup
├── styles.py               # Output styling and formatting
└── templates/
    ├── reminder_template.txt
    └── starter_template.txt

tests/
├── conftest.py             # Test configuration and fixtures
├── test_action.py          # Unit tests for action handling
├── test_ai.py              # Unit tests for AI integration
├── test_commands.py        # Unit tests for command parsing
├── test_main.py            # Tests for main application flow
└── test_prep.py            # Tests for configuration and setup
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run a specific test module
pytest tests/test_ai.py

# Run with coverage reporting
pytest --cov=src/cliqq
```

## License

This project is licensed under the terms of the MIT LICENSE. See [LICENSE](LICENSE) for more details.