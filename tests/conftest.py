import logging
import pytest


@pytest.fixture(autouse=True)
def disable_program_output(monkeypatch):

    def dummy_program_output(*args, **kwargs):
        return None

    monkeypatch.setattr("ai.program_output", dummy_program_output)
    monkeypatch.setattr("action.program_output", dummy_program_output)
    monkeypatch.setattr("commands.program_output", dummy_program_output)
    monkeypatch.setattr("main.program_output", dummy_program_output)
    monkeypatch.setattr("prep.program_output", dummy_program_output)

    return dummy_program_output


@pytest.fixture(autouse=True)
def disable_file_logging(monkeypatch):
    # Replace logger with a dummy that never writes files
    dummy_logger = logging.getLogger("test")
    dummy_logger.handlers.clear()
    dummy_logger.addHandler(logging.NullHandler())

    # Patch both setup_logging() and global logger
    monkeypatch.setattr("log.setup_logging", lambda: dummy_logger)
    monkeypatch.setattr("log.logger", dummy_logger)

    return dummy_logger
