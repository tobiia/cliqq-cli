import logging
import os
import sys
from pathlib import Path


# can use MemoryHandler instead?
class BufferingFileHandler(logging.Handler):
    def __init__(self, filename: str, buffer_size: int = 10):
        super().__init__()
        self._buffer_size = buffer_size
        self._buffer: list[str] = []

        home = Path("~/.cliqq").expanduser()
        home.mkdir(parents=True, exist_ok=True)

        self._filename = home / filename

        self._filename.touch(exist_ok=True)

    # log info is passed around in LogRecord instances
    def emit(self, record: logging.LogRecord):
        msg = self.format(record)
        self._buffer.append(msg)
        if len(self._buffer) >= self._buffer_size:
            self.flush()

    def flush(self):
        if not self._buffer:
            return
        log_text = "".join(self._buffer)
        with open(self._filename, "a", encoding="utf-8") as f:
            f.write(log_text + "\n\n")
        self._buffer.clear()


# log any uncaught exceptions
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("Uncaught Exception", exc_info=(exc_type, exc_value, exc_traceback))


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("cliqq")
    logger.propagate = False  # don’t bubble up to root logger

    # clear any existing handlers (was causing issues while testing)
    if logger.handlers:
        logger.handlers.clear()

    debug_handler = BufferingFileHandler("debug.log", 1)
    debug_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    debug_handler.setLevel(logging.ERROR)

    io_handler = BufferingFileHandler("cliqq.log")
    io_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))

    # Attach handlers
    logger.addHandler(debug_handler)
    logger.addHandler(io_handler)

    return logger


logger = setup_logging()

sys.excepthook = handle_exception
