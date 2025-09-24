import logging
import pytest

# python -m pytest
# pytest
# pytest test_action.py
# -v = verbose


@pytest.fixture(autouse=True)
def disable_program_output(monkeypatch):

    def dummy_program_output(*args, **kwargs):
        return None

    # raising=False means they won't raise error if file doesn't import this
    monkeypatch.setattr("cliqq.ai.program_output", dummy_program_output, raising=False)
    monkeypatch.setattr(
        "cliqq.action.program_output", dummy_program_output, raising=False
    )
    monkeypatch.setattr(
        "cliqq.commands.program_output", dummy_program_output, raising=False
    )
    monkeypatch.setattr(
        "cliqq.main.program_output", dummy_program_output, raising=False
    )

    return dummy_program_output


@pytest.fixture(autouse=True)
def disable_file_logging(monkeypatch):
    # Replace logger with a dummy that never writes files
    dummy_logger = logging.getLogger("test")
    dummy_logger.handlers.clear()
    dummy_logger.addHandler(logging.NullHandler())

    # Patch both setup_logging() and global logger
    monkeypatch.setattr("cliqq.log.setup_logging", lambda: dummy_logger)
    monkeypatch.setattr("cliqq.log.logger", dummy_logger)

    return dummy_logger
