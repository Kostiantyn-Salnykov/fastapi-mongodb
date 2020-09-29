import copy
import functools
import logging

import click
from uvicorn.logging import TRACE_LOG_LEVEL

from settings import settings

__all__ = ["logger"]


class MainFormatter(logging.Formatter):
    COLORS = {
        TRACE_LOG_LEVEL: lambda data: click.style(str(data), fg="blue"),
        logging.DEBUG: lambda data: click.style(str(data), fg="white"),
        logging.INFO: lambda data: click.style(str(data), fg="bright_blue"),
        logging.WARNING: lambda data: click.style(str(data), fg="bright_yellow"),
        logging.ERROR: lambda data: click.style(str(data), fg="bright_red"),
        logging.CRITICAL: lambda data: click.style(str(data), fg="red", bold=True, underline=True),
    }

    def formatMessage(self, record: logging.LogRecord) -> str:
        recordcopy = copy.copy(record)
        recordcopy.__dict__["message"] = self.COLORS[recordcopy.levelno](recordcopy.__dict__["message"])
        recordcopy.__dict__["filename"] = click.style(text=str(recordcopy.__dict__["filename"]), fg="cyan")
        recordcopy.__dict__["lineno"] = click.style(
            text=str(recordcopy.__dict__["lineno"]), fg="bright_blue", underline=True
        )
        recordcopy.__dict__["created"] = click.style(text=str(recordcopy.__dict__["created"]), fg="cyan")
        separator = " " * (8 - len(recordcopy.__dict__["levelname"]))
        recordcopy.__dict__["levelname"] = (
            self.COLORS[recordcopy.__dict__["levelno"]](recordcopy.__dict__["levelname"])
            + click.style(text=":", fg="cyan")
            + separator
        )
        return super().formatMessage(record=recordcopy)


@functools.lru_cache()
def setup_logging():
    """Setup logging formatter"""
    default_format = (
        "%(levelname)s %(message)s (%(created)s) \n╰───{file_format}%(pathname)s{line_format}%(lineno)s".format(
            file_format=click.style(text='File "', fg="bright_blue", bold=True),
            line_format=click.style(text='", line ', fg="bright_blue", bold=True),
        )
    )
    formatter = MainFormatter(fmt=default_format)
    handler = logging.StreamHandler()
    handler.setFormatter(fmt=formatter)

    main_logger = logging.getLogger(name=settings.LOGGER_NAME)
    main_logger.setLevel(level=logging.NOTSET)
    main_logger.addHandler(hdlr=handler)
    return main_logger


logger = setup_logging()
