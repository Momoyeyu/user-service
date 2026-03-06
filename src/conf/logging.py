"""Loguru 日志配置模块。"""

import logging
import sys
from pathlib import Path

from loguru import logger

from src.conf.config import settings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "logs"


class _InterceptHandler(logging.Handler):
    """将标准库 logging 重定向到 loguru。"""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    _LOG_DIR.mkdir(exist_ok=True)

    logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message:.300}</level>"
    )

    log_level = "DEBUG" if settings.APP_DEBUG else "INFO"

    logger.add(
        sys.stderr,
        format=log_format,
        level=log_level,
        colorize=True,
    )

    logger.add(
        _LOG_DIR / "user-service_{time:YYYY-MM-DD}.log",
        format=log_format,
        level=log_level,
        rotation="00:00",
        retention="7 days",
        compression="zip",
        encoding="utf-8",
    )

    # 拦截标准库 logging → loguru
    intercept = _InterceptHandler()
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine"):
        stdlib_logger = logging.getLogger(name)
        stdlib_logger.handlers = [intercept]
        stdlib_logger.propagate = False
