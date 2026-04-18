from pathlib import Path
from loguru import logger


def logger_init():
    base_dir = Path(__file__).resolve().parents[2]
    log_dir = base_dir / "logs"
    log_dir.mkdir(exist_ok=True)

    logger.remove(0)
    logger.add(
        log_dir / "app.log",
        format="{time} {level} {message}",
        level="DEBUG",
        rotation="1 MB",
        retention="7 days"
    )
