import logging
import logging.handlers

from rich.logging import RichHandler

RICH_FORMAT = "[%(filename)s:%(lineno)s] >> %(message)s"
FILE_HANDLER_FORMAT = "[%(asctime)s]\\t%(levelname)s\\t[%(filename)s:%(funcName)s:%(lineno)s]\\t>> %(message)s"


def get_logger(name="log", log_path="./log.log") -> logging.Logger:
    logging.basicConfig(
        level="NOTSET", format=RICH_FORMAT, handlers=[RichHandler(rich_tracebacks=True)]
    )

    logger = logging.getLogger(name)
    file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(FILE_HANDLER_FORMAT))
    logger.addHandler(file_handler)

    return logger


def handle_exception(exc_type, exc_value, exc_traceback):
    logger = logging.getLogger("rich")
    logger.error("Unexpected exception", exc_info=(exc_type, exc_value, exc_traceback))
