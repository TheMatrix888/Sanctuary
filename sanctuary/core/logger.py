from loguru import logger
from .config import LOG_FILE


def logger_init() -> None:
    logger.remove()

    logger.add(
        sink=LOG_FILE,
        level="DEBUG",
        format="{time:HH:mm:ss.SS} {level} {message}",
        backtrace=True,
        diagnose=True,
        encoding="utf-8",
    )
