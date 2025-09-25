import logging
import os
import sys
from pathlib import Path


# can use MemoryHandler instead?
class BufferingFileHandler(logging.Handler):
    """Custom logging handler that buffers log records before writing to a file.

    Attributes:
        _buffer_size (int): Number of records to buffer before flushing.
        _buffer (list[str]): In-memory buffer of formatted log records.
        _filename (Path): Path to the log file.
    """

    def __init__(self, filename: str, buffer_size: int = 10):
        super().__init__()
        self._buffer_size = buffer_size
        self._buffer: list[str] = []

        home = Path("~/.cliqq").expanduser()
        home.mkdir(parents=True, exist_ok=True)

        self._filename = home / filename

        self._filename.touch(exist_ok=True)

    def emit(self, record: logging.LogRecord):
        """Handle a new log record, which is the type by which
        logging info is passed around.

        Args:
            record (logging.LogRecord): The log record to handle.
        """

        msg = self.format(record)
        self._buffer.append(msg)
        if len(self._buffer) >= self._buffer_size:
            self.flush()

    def flush(self):
        """Write buffered log records to file and clear the buffer."""

        if not self._buffer:
            return
        log_text = "".join(self._buffer)
        with open(self._filename, "a", encoding="utf-8") as f:
            f.write(log_text + "\n\n")
        self._buffer.clear()


def handle_exception(exc_type, exc_value, exc_traceback):
    """Log uncaught exceptions.

    Forwards KeyboardInterrupts to the default handler. For all other
    exceptions, logs a CRITICAL message with traceback details.

    Args:
        exc_type: The exception type.
        exc_value: The exception instance.
        exc_traceback: The traceback object.
    """

    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("UNCAUGHT EXCEPTION", exc_info=(exc_type, exc_value, exc_traceback))


def setup_logging() -> logging.Logger:
    """Configure and return the application logger.

    Sets up two handlers:
      - debug.log: For detailed error messages (level=ERROR).
      - cliqq.log: For general program logs.

    Returns:
        logging.Logger: The configured logger instance.
    """

    logger = logging.getLogger("cliqq")
    # don’t bubble up to root logger aka console
    logger.propagate = False

    # clear any existing handlers (was causing issues while testing)
    if logger.handlers:
        logger.handlers.clear()

    debug_handler = BufferingFileHandler("debug.log", 1)
    debug_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    debug_handler.setLevel(logging.DEBUG)

    io_handler = BufferingFileHandler("cliqq.log")
    io_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    io_handler.setLevel(logging.INFO)
    io_handler.addFilter(lambda record: record.levelno == logging.INFO)  # only INFO

    # Attach handlers
    logger.addHandler(debug_handler)
    logger.addHandler(io_handler)

    return logger


logger = setup_logging()

sys.excepthook = handle_exception
