import logging
import os
import sys


# can use MemoryHandler instead?
class BufferingFileHandler(logging.Handler):
    def __init__(self, filename: str, buffer_size: int = 10):
        super().__init__()
        self._filename = filename
        self._buffer_size = buffer_size
        self._buffer: list[str] = []

    # log info is passed around in LogRecord instances
    def emit(self, record: logging.LogRecord):
        msg = self.format(record)
        self._buffer.append(msg)
        if len(self._buffer) >= self._buffer_size:
            self.flush()

    def flush(self):
        if not self._buffer:
            return
        os.makedirs(os.path.dirname(self._filename), exist_ok=True)
        log_text = "".join(self._buffer)
        with open(self._filename, "a") as f:
            f.write(log_text)
        self._buffer.clear()


# log any uncaught exceptions
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("Uncaught Exception", exc_info=(exc_type, exc_value, exc_traceback))


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("cliqq")
    # root logger setup
    logging.basicConfig(encoding="utf-8", level=logging.DEBUG)  # catch all

    debug_handler = BufferingFileHandler("debug.log", 3)
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


# FIXME check that this object is even set up?

logger = setup_logging()

sys.excepthook = handle_exception
